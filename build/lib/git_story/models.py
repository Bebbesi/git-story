from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class CommitRecord(BaseModel):
    commit_hash: str
    author_name: str
    author_email: str
    authored_at: datetime
    subject: str


class WordCount(BaseModel):
    word: str
    count: int = Field(ge=0)


class RepoInfo(BaseModel):
    path: Path
    root: Path
    name: str


class GitStats(BaseModel):
    total_commits: int = Field(ge=0)
    active_days: int = Field(ge=0)
    longest_streak: int = Field(ge=0)
    commits_per_weekday: dict[str, int]
    most_active_hour: int = Field(ge=0, le=23)
    night_commit_ratio: float = Field(ge=0.0, le=1.0)
    weekend_commit_ratio: float = Field(ge=0.0, le=1.0)
    most_common_commit_words: list[WordCount]
    primary_author: str
    avg_commits_per_active_day: float = Field(ge=0.0)


class PersonalityReport(BaseModel):
    personality_name: str
    subtitle: str
    traits: list[str] = Field(default_factory=list, min_length=3, max_length=6)
    summary: str
    roast: str
    story_lines: list[str] = Field(default_factory=list, min_length=4, max_length=4)
    vibe: str


class StoryReport(BaseModel):
    repo: RepoInfo
    author_filter: str | None = None
    model: str
    used_offline_mode: bool = False
    fallback_reason: str | None = None
    stats: GitStats
    personality: PersonalityReport
