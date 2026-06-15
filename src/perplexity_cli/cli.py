from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from perplexity_cli import __version__
from perplexity_cli.client import PerplexityClient, PerplexityError
from perplexity_cli.security import sanitize_terminal_text


DEFAULT_SYSTEM_MESSAGE = (
    "You are a precise and helpful assistant. Answer in the user's language."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pplx-python",
        description=(
            "Ask Perplexity from the terminal. Without a question, an interactive "
            "session starts."
        ),
    )
    parser.add_argument("question", nargs="*", help="one-shot question")
    parser.add_argument(
        "-m",
        "--model",
        default=os.getenv("PERPLEXITY_MODEL", "sonar"),
        choices=("sonar", "sonar-pro", "sonar-reasoning-pro", "sonar-deep-research"),
        help="Sonar model (default: sonar)",
    )
    parser.add_argument(
        "-s", "--system", default=DEFAULT_SYSTEM_MESSAGE, help="system instruction"
    )
    parser.add_argument("--no-stream", action="store_true", help="disable streaming")
    parser.add_argument(
        "--no-citations", action="store_true", help="do not print source URLs"
    )
    parser.add_argument(
        "--timeout", type=positive_float, default=60.0, help="network timeout in seconds"
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = PerplexityClient(
            os.getenv("PERPLEXITY_API_KEY", ""), timeout=args.timeout
        )
    except (PerplexityError, ValueError) as error:
        print(sanitize_terminal_text(error), file=sys.stderr)
        return 1

    question = " ".join(args.question).strip()
    messages = [{"role": "system", "content": args.system}]
    if question:
        try:
            ask(client, args, messages, question)
            return 0
        except PerplexityError as error:
            print(f"Error: {sanitize_terminal_text(error)}", file=sys.stderr)
            return 1

    return interactive_session(client, args, messages)


def interactive_session(
    client: PerplexityClient,
    args: argparse.Namespace,
    messages: list[dict[str, str]],
) -> int:
    print(f"Perplexity CLI Python {__version__} ({args.model})")
    print("Type /help to list commands. Ctrl+D or /exit quits.\n")

    while True:
        try:
            prompt = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not prompt:
            continue
        if prompt in {"/exit", "/quit"}:
            return 0
        if prompt == "/help":
            print_interactive_help()
            continue
        if prompt == "/clear":
            messages[:] = [{"role": "system", "content": args.system}]
            print("Conversation cleared.\n")
            continue
        if prompt.startswith("/model "):
            model = prompt[7:].strip()
            allowed = {
                "sonar",
                "sonar-pro",
                "sonar-reasoning-pro",
                "sonar-deep-research",
            }
            if model not in allowed:
                print(f"Unknown model: {sanitize_terminal_text(model)}\n")
                continue
            args.model = model
            print(f"Model: {model}\n")
            continue

        try:
            updated = ask(client, args, messages, prompt)
            messages[:] = updated
        except PerplexityError as error:
            print(f"\nError: {sanitize_terminal_text(error)}\n", file=sys.stderr)


def ask(
    client: PerplexityClient,
    args: argparse.Namespace,
    messages: list[dict[str, str]],
    prompt: str,
) -> list[dict[str, str]]:
    next_messages = [*messages, {"role": "user", "content": prompt}]
    print("pplx> ", end="", flush=True)
    result = client.chat(
        messages=next_messages,
        model=args.model,
        stream=not args.no_stream,
        on_text=lambda text: print(
            sanitize_terminal_text(text), end="", flush=True
        ),
    )
    print()
    if not args.no_citations and result.citations:
        print("\nSources:")
        for index, url in enumerate(result.citations, start=1):
            print(f"  [{index}] {sanitize_terminal_text(url)}")
    print()
    return [*next_messages, {"role": "assistant", "content": result.text}]


def print_interactive_help() -> None:
    print(
        """
Commands:
  /help           Show this list
  /clear          Clear conversation history
  /model <name>   Change the Sonar model
  /exit           Quit
"""
    )


def main() -> None:
    raise SystemExit(run())
