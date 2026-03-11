from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from git_story.ai import AIError, fallback_personality, generate_personality_with_gemini
from git_story.git_utils import GitStoryError, analyze_commits, detect_repo, get_repo_commits
from git_story.models import StoryReport

DEFAULT_MODEL = "gemini-2.5-flash"


def build_story_report(
    repo_path: str | Path | None = None,
    author: str | None = None,
    model: str = DEFAULT_MODEL,
    offline: bool = False,
    api_key: str | None = None,
) -> StoryReport:
    load_dotenv()

    repo = detect_repo(repo_path)
    commits = get_repo_commits(repo, author_filter=author)

    if not commits:
        who = f" for author '{author}'" if author else ""
        raise GitStoryError(f"No commits found{who} in repository {repo.name}")

    stats = analyze_commits(commits)

    used_offline_mode = offline
    fallback_reason: str | None = None

    if offline:
        personality = fallback_personality(stats)
    else:
        if not api_key:
            used_offline_mode = True
            fallback_reason = "GEMINI_API_KEY not set"
            personality = fallback_personality(stats)
        else:
            try:
                personality = generate_personality_with_gemini(stats=stats, model=model, api_key=api_key)
            except AIError as exc:
                used_offline_mode = True
                fallback_reason = str(exc)
                personality = fallback_personality(stats)

    return StoryReport(
        repo=repo,
        author_filter=author,
        model=model,
        used_offline_mode=used_offline_mode,
        fallback_reason=fallback_reason,
        stats=stats,
        personality=personality,
    )
