from __future__ import annotations

import codecs
import json
import socket
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_ENDPOINT = "https://api.perplexity.ai/v1/sonar"
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RESPONSE_BYTES = 10 * 1024 * 1024


class PerplexityError(RuntimeError):
    """Base exception returned by this package."""


@dataclass(frozen=True)
class ChatResult:
    text: str
    citations: list[str] = field(default_factory=list)
    search_results: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] | None = None


class PerplexityClient:
    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        if not api_key:
            raise PerplexityError(
                "PERPLEXITY_API_KEY is missing. Export it before running pplx-python."
            )
        if not endpoint.startswith("https://"):
            raise ValueError("The Perplexity endpoint must use HTTPS.")
        if timeout <= 0 or max_response_bytes <= 0:
            raise ValueError("Timeout and response size limits must be positive.")

        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout = timeout
        self._max_response_bytes = max_response_bytes
        self._opener = opener

    def chat(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        stream: bool = True,
        on_text: Callable[[str], None] = lambda _text: None,
    ) -> ChatResult:
        request = Request(
            self._endpoint,
            data=json.dumps(
                {"model": model, "messages": messages, "stream": stream}
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream" if stream else "application/json",
                "User-Agent": "perplexity-cli-python/0.1.0",
            },
            method="POST",
        )

        try:
            with self._opener(request, timeout=self._timeout) as response:
                if stream:
                    return read_event_stream(
                        response,
                        on_text,
                        max_response_bytes=self._max_response_bytes,
                    )

                payload = _read_json_response(response, self._max_response_bytes)
        except HTTPError as error:
            raise PerplexityError(_format_http_error(error)) from error
        except (URLError, TimeoutError, socket.timeout) as error:
            reason = getattr(error, "reason", error)
            raise PerplexityError(f"Network error: {reason}") from error

        text = str(payload.get("choices", [{}])[0].get("message", {}).get("content", ""))
        on_text(text)
        return _result_from_payload(payload, text)


def parse_sse_event(event: str) -> dict[str, Any] | None:
    data = "\n".join(
        line[5:].lstrip()
        for line in event.splitlines()
        if line.startswith("data:")
    )
    if not data or data == "[DONE]":
        return None

    try:
        payload = json.loads(data)
    except json.JSONDecodeError as error:
        raise PerplexityError("The API returned an invalid streaming event.") from error
    if not isinstance(payload, dict):
        raise PerplexityError("The API returned an unexpected streaming payload.")
    return payload


def read_event_stream(
    response: Iterable[bytes],
    on_text: Callable[[str], None],
    *,
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
) -> ChatResult:
    decoder = codecs.getincrementaldecoder("utf-8")()
    buffer = ""
    output = ""
    metadata: dict[str, Any] = {}
    total_bytes = 0

    for chunk in response:
        total_bytes += len(chunk)
        if total_bytes > max_response_bytes:
            raise PerplexityError(
                f"The API response exceeded the {max_response_bytes}-byte safety limit."
            )
        buffer += decoder.decode(chunk)
        events, buffer = _extract_events(buffer)
        for event in events:
            output, metadata = _consume_event(event, output, metadata, on_text)

    buffer += decoder.decode(b"", final=True)
    if buffer.strip():
        output, metadata = _consume_event(buffer, output, metadata, on_text)

    return _result_from_payload(metadata, output)


def _extract_events(buffer: str) -> tuple[list[str], str]:
    normalized = buffer.replace("\r\n", "\n")
    parts = normalized.split("\n\n")
    return parts[:-1], parts[-1]


def _consume_event(
    event: str,
    output: str,
    metadata: dict[str, Any],
    on_text: Callable[[str], None],
) -> tuple[str, dict[str, Any]]:
    payload = parse_sse_event(event)
    if payload is None:
        return output, metadata

    choices = payload.get("choices") or [{}]
    delta = choices[0].get("delta", {}).get("content", "")
    if delta:
        delta = str(delta)
        output += delta
        on_text(delta)

    metadata = {**metadata, **payload}
    return output, metadata


def _read_json_response(response: Any, limit: int) -> dict[str, Any]:
    body = response.read(limit + 1)
    if len(body) > limit:
        raise PerplexityError(f"The API response exceeded the {limit}-byte safety limit.")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PerplexityError("The API returned invalid JSON.") from error
    if not isinstance(payload, dict):
        raise PerplexityError("The API returned an unexpected JSON payload.")
    return payload


def _format_http_error(error: HTTPError) -> str:
    body = error.read(64 * 1024).decode("utf-8", errors="replace")
    details = body
    try:
        payload = json.loads(body)
        if isinstance(payload, dict):
            details = str(
                payload.get("error", {}).get("message")
                or payload.get("detail")
                or payload
            )
    except json.JSONDecodeError:
        pass
    suffix = f": {details}" if details else ""
    return f"Perplexity API error ({error.code}){suffix}"


def _result_from_payload(payload: dict[str, Any], text: str) -> ChatResult:
    citations = payload.get("citations") or []
    search_results = payload.get("search_results") or []
    return ChatResult(
        text=text,
        citations=[str(item) for item in citations],
        search_results=[item for item in search_results if isinstance(item, dict)],
        usage=payload.get("usage") if isinstance(payload.get("usage"), dict) else None,
    )
