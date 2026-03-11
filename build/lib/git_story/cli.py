from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console

from git_story.git_utils import GitStoryError
from git_story.main import DEFAULT_MODEL, build_story_report
from git_story.render import render_report


def build_parser() -> argparse.ArgumentParser:
    load_dotenv()

    default_model = os.getenv("GIT_STORY_MODEL", DEFAULT_MODEL)

    parser = argparse.ArgumentParser(
        prog="git-story",
        description="Analyze git history and generate a developer story/personality report.",
    )
    parser.add_argument("--repo", type=str, default=None, help="Path to a git repository")
    parser.add_argument("--author", type=str, default=None, help="Filter commits by author")
    parser.add_argument("--offline", action="store_true", help="Disable Gemini and use local fallback")
    parser.add_argument("--json", action="store_true", help="Output raw JSON report")
    parser.add_argument("--model", type=str, default=default_model, help="Gemini model name")
    parser.add_argument("--no-color", action="store_true", help="Disable color output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    console = Console(no_color=args.no_color, stderr=True)
    api_key = os.getenv("GEMINI_API_KEY")

    try:
        report = build_story_report(
            repo_path=args.repo,
            author=args.author,
            model=args.model,
            offline=args.offline,
            api_key=api_key,
        )
    except GitStoryError as exc:
        console.print(f"[bold red]󰅙 git-story error:[/bold red] {exc}")
        return 2
    except Exception as exc:
        console.print(f"[bold red]󰅙 unexpected error:[/bold red] {exc}")
        return 1

    if args.json:
        print(report.model_dump_json(indent=2, by_alias=False))
        return 0

    output_console = Console(no_color=args.no_color)
    render_report(output_console, report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
