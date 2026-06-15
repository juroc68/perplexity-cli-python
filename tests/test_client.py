import io
import json
import unittest

from perplexity_cli.client import (
    PerplexityClient,
    PerplexityError,
    parse_sse_event,
    read_event_stream,
)


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()


class ClientTests(unittest.TestCase):
    def test_parses_sse_event(self) -> None:
        payload = parse_sse_event(
            'data: {"choices":[{"delta":{"content":"hello"}}]}'
        )
        self.assertEqual(payload["choices"][0]["delta"]["content"], "hello")

    def test_ignores_done_marker(self) -> None:
        self.assertIsNone(parse_sse_event("data: [DONE]"))

    def test_assembles_stream_and_citations(self) -> None:
        response = io.BytesIO(
            b'data: {"choices":[{"delta":{"content":"Bon"}}]}\n\n'
            b'data: {"choices":[{"delta":{"content":"jour"}}],'
            b'"citations":["https://example.com"]}\n\ndata: [DONE]\n\n'
        )
        output = []
        result = read_event_stream(response, output.append)
        self.assertEqual("".join(output), "Bonjour")
        self.assertEqual(result.text, "Bonjour")
        self.assertEqual(result.citations, ["https://example.com"])

    def test_rejects_oversized_stream(self) -> None:
        with self.assertRaisesRegex(PerplexityError, "safety limit"):
            read_event_stream(io.BytesIO(b"x" * 11), lambda _text: None, max_response_bytes=10)

    def test_sends_key_only_in_authorization_header(self) -> None:
        captured = {}

        def opener(request, *, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse(
                json.dumps(
                    {"choices": [{"message": {"content": "response"}}]}
                ).encode("utf-8")
            )

        client = PerplexityClient("secret", timeout=12, opener=opener)
        result = client.chat(
            messages=[{"role": "user", "content": "question"}],
            model="sonar",
            stream=False,
        )

        request = captured["request"]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://api.perplexity.ai/v1/sonar")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertNotIn("secret", request.full_url)
        self.assertNotIn("secret", request.data.decode("utf-8"))
        self.assertEqual(body["model"], "sonar")
        self.assertEqual(captured["timeout"], 12)
        self.assertEqual(result.text, "response")

    def test_rejects_non_https_endpoint(self) -> None:
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            PerplexityClient("secret", endpoint="http://example.com")


if __name__ == "__main__":
    unittest.main()
