from __future__ import annotations

import re
import subprocess
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from git_story.models import CommitRecord, GitStats, RepoInfo, WordCount


class GitStoryError(RuntimeError):
    """Raised when repository analysis cannot proceed."""


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "this",
    "that",
    "update",
    "merge",
    "revert",
    "bump",
}
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-]{1,}")


def _run_git(repo_path: Path, args: list[str]) -> str:
    cmd = ["git", *args]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise GitStoryError("git executable not found in PATH") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        message = stderr or f"git command failed: {' '.join(cmd)}"
        raise GitStoryError(message) from exc
    return completed.stdout.strip()


def detect_repo(repo_path: str | Path | None = None) -> RepoInfo:
    base = Path(repo_path).expanduser().resolve() if repo_path else Path.cwd().resolve()

    inside = _run_git(base, ["rev-parse", "--is-inside-work-tree"])
    if inside.lower() != "true":
        raise GitStoryError(f"{base} is not inside a git repository")

    root = Path(_run_git(base, ["rev-parse", "--show-toplevel"]))
    name = root.name
    return RepoInfo(path=base, root=root, name=name)


def get_repo_commits(repo: RepoInfo, author_filter: str | None = None) -> list[CommitRecord]:
    args = ["log", "--pretty=format:%H%x1f%an%x1f%ae%x1f%aI%x1f%s"]
    if author_filter:
        args.append(f"--author={author_filter}")

    output = _run_git(repo.root, args)
    commits: list[CommitRecord] = []

    if not output:
        return commits

    for line in output.splitlines():
        parts = line.split("\x1f", 4)
        if len(parts) != 5:
            continue
        commit_hash, author_name, author_email, authored_at, subject = parts
        commits.append(
            CommitRecord(
                commit_hash=commit_hash,
                author_name=author_name,
                author_email=author_email,
                authored_at=authored_at,
                subject=subject,
            )
        )

    return commits


def _longest_streak(days: set[date]) -> int:
    if not days:
        return 0

    sorted_days = sorted(days)
    longest = 1
    current = 1

    for idx in range(1, len(sorted_days)):
        if sorted_days[idx] == sorted_days[idx - 1] + timedelta(days=1):
            current += 1
        else:
            current = 1
        longest = max(longest, current)

    return longest


def _top_commit_words(commits: list[CommitRecord], limit: int = 8) -> list[WordCount]:
    counter: Counter[str] = Counter()

    for commit in commits:
        words = [match.group(0).lower() for match in WORD_RE.finditer(commit.subject)]
        for word in words:
            if word in STOP_WORDS:
                continue
            if len(word) <= 2:
                continue
            counter[word] += 1

    top = counter.most_common(limit)
    return [WordCount(word=word, count=count) for word, count in top]


def analyze_commits(commits: list[CommitRecord]) -> GitStats:
    if not commits:
        return GitStats(
            total_commits=0,
            active_days=0,
            longest_streak=0,
            commits_per_weekday={day: 0 for day in WEEKDAYS},
            most_active_hour=0,
            night_commit_ratio=0.0,
            weekend_commit_ratio=0.0,
            most_common_commit_words=[],
            primary_author="unknown",
            avg_commits_per_active_day=0.0,
        )

    days: set[date] = set()
    weekday_counts = Counter({day: 0 for day in WEEKDAYS})
    hour_counts: Counter[int] = Counter()
    author_counts: Counter[str] = Counter()

    night_commits = 0
    weekend_commits = 0

    for commit in commits:
        dt = commit.authored_at
        days.add(dt.date())

        weekday_key = WEEKDAYS[dt.weekday()]
        weekday_counts[weekday_key] += 1

        hour_counts[dt.hour] += 1
        author_counts[commit.author_name] += 1

        if dt.hour >= 22 or dt.hour < 6:
            night_commits += 1
        if dt.weekday() >= 5:
            weekend_commits += 1

    total_commits = len(commits)
    active_days = len(days)

    most_active_hour = min(
        (hour for hour, count in hour_counts.items() if count == max(hour_counts.values())),
        default=0,
    )
    primary_author = author_counts.most_common(1)[0][0] if author_counts else "unknown"

    return GitStats(
        total_commits=total_commits,
        active_days=active_days,
        longest_streak=_longest_streak(days),
        commits_per_weekday={day: weekday_counts[day] for day in WEEKDAYS},
        most_active_hour=most_active_hour,
        night_commit_ratio=night_commits / total_commits,
        weekend_commit_ratio=weekend_commits / total_commits,
        most_common_commit_words=_top_commit_words(commits),
        primary_author=primary_author,
        avg_commits_per_active_day=(total_commits / active_days if active_days else 0.0),
    )
