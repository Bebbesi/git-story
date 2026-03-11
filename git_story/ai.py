from __future__ import annotations

import json
from typing import Any

from git_story.models import GitStats, PersonalityReport

try:
    from google import genai
except Exception:  # pragma: no cover - handled gracefully in runtime fallback
    genai = None  # type: ignore[assignment]


class AIError(RuntimeError):
    """Raised when Gemini output cannot be produced or parsed."""


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise AIError("Gemini response did not contain JSON")

    snippet = cleaned[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError as exc:
        raise AIError("Failed to decode JSON response from Gemini") from exc


def _prompt_for_stats(stats: GitStats) -> str:
    stats_payload = {
        "total_commits": stats.total_commits,
        "active_days": stats.active_days,
        "longest_streak": stats.longest_streak,
        "commits_per_weekday": stats.commits_per_weekday,
        "most_active_hour": stats.most_active_hour,
        "night_commit_ratio": round(stats.night_commit_ratio, 4),
        "weekend_commit_ratio": round(stats.weekend_commit_ratio, 4),
        "most_common_commit_words": [w.model_dump() for w in stats.most_common_commit_words],
        "primary_author": stats.primary_author,
        "avg_commits_per_active_day": round(stats.avg_commits_per_active_day, 3),
    }

    fields = {
        "personality_name": "string",
        "subtitle": "string",
        "traits": "array of short strings (3 to 6 items)",
        "summary": "string (2 to 4 sentences)",
        "roast": "string (playful, non-toxic)",
        "story_lines": "array of exactly 4 short lines",
        "vibe": "string (single-word or short phrase)",
    }

    return (
        "You are writing a playful developer persona report for a CLI tool. "
        "Use only the stats provided. Do not invent hidden context. "
        "Output strict JSON with no markdown fences and no extra keys.\n\n"
        f"Stats:\n{json.dumps(stats_payload, indent=2)}\n\n"
        f"Required JSON fields:\n{json.dumps(fields, indent=2)}"
    )


def generate_personality_with_gemini(stats: GitStats, model: str, api_key: str) -> PersonalityReport:
    if genai is None:
        raise AIError("google-genai is not available")

    prompt = _prompt_for_stats(stats)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.9,
            },
        )
    except Exception as exc:  # pragma: no cover - network/API errors are runtime concerns
        raise AIError(f"Gemini request failed: {exc}") from exc

    response_text = getattr(response, "text", None)
    if not response_text:
        raise AIError("Gemini returned an empty response")

    data = _extract_json(response_text)

    try:
        return PersonalityReport.model_validate(data)
    except Exception as exc:
        raise AIError(f"Gemini JSON did not match expected schema: {exc}") from exc


def fallback_personality(stats: GitStats) -> PersonalityReport:
    night = stats.night_commit_ratio
    weekend = stats.weekend_commit_ratio
    streak = stats.longest_streak

    if night >= 0.4:
        name = "The Midnight Debugger"
        subtitle = "Thrives when the terminal glows past midnight"
        vibe = "nocturnal"
        traits = ["persistent", "night-owl", "iterative"]
    elif weekend >= 0.35:
        name = "The Weekend Hacker"
        subtitle = "Turns downtime into shipping time"
        vibe = "restless"
        traits = ["self-driven", "curious", "hands-on"]
    elif streak >= 10:
        name = "The Streak Builder"
        subtitle = "Builds momentum one day at a time"
        vibe = "disciplined"
        traits = ["consistent", "focused", "gritty"]
    else:
        name = "The Steady Committer"
        subtitle = "Small, reliable steps toward better code"
        vibe = "balanced"
        traits = ["pragmatic", "methodical", "reliable"]

    primary_word = stats.most_common_commit_words[0].word if stats.most_common_commit_words else "fix"

    summary = (
        f"{stats.primary_author} has {stats.total_commits} commits across {stats.active_days} active days. "
        f"Peak coding hour is {stats.most_active_hour:02d}:00 with a longest streak of {stats.longest_streak} days. "
        "The commit pattern suggests a builder who improves things incrementally and keeps momentum."
    )

    roast = (
        f"Your commit history and '{primary_word}' are clearly in a long-term relationship. "
        "At this point, even your shell prompt expects another push."
    )

    story_lines = [
        "It started with careful commits and a quiet plan.",
        "Then the repo found a rhythm and the diffs got bolder.",
        f"Around {stats.most_active_hour:02d}:00, the best ideas kept landing.",
        "Now the project reads like a logbook of stubborn progress.",
    ]

    return PersonalityReport(
        personality_name=name,
        subtitle=subtitle,
        traits=traits,
        summary=summary,
        roast=roast,
        story_lines=story_lines,
        vibe=vibe,
    )
