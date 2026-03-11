from __future__ import annotations

from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from git_story.models import StoryReport

ICON_REPO = "󰊢"
ICON_USER = "󰀄"
ICON_STATS = "󰔟"
ICON_CLOCK = "󰅐"
ICON_CAL = "󰃰"
ICON_STORY = "󰈭"
ICON_PERSONA = "󰊠"


def _pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def _activity_graph(commits_per_weekday: dict[str, int], width: int = 16) -> str:
    max_value = max(commits_per_weekday.values()) if commits_per_weekday else 0
    lines: list[str] = []

    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        count = commits_per_weekday.get(day, 0)
        bar_len = int((count / max_value) * width) if max_value > 0 else 0
        bar = "█" * bar_len
        lines.append(f"{day:<3} {bar:<{width}} {count:>3}")

    return "\n".join(lines)


def _header_panel(report: StoryReport) -> Panel:
    repo_line = f"{ICON_REPO} [bold cyan]{report.repo.name}[/bold cyan]"
    author_line = f"{ICON_USER} [bold white]{report.stats.primary_author}[/bold white]"

    if report.author_filter:
        author_line += f"  [dim](filter: {report.author_filter})[/dim]"

    return Panel.fit(
        Text.from_markup(f"{repo_line}\n{author_line}"),
        title="git-story",
        border_style="bright_blue",
    )


def _stats_panel(report: StoryReport) -> Panel:
    stats = report.stats
    table = Table.grid(expand=True)
    table.add_column(style="bright_white")
    table.add_column(style="cyan", justify="right")

    table.add_row("commits", str(stats.total_commits))
    table.add_row("active days", str(stats.active_days))
    table.add_row("longest streak", f"{stats.longest_streak} days")
    table.add_row("avg/day", f"{stats.avg_commits_per_active_day:.2f}")
    table.add_row("most active hour", f"{stats.most_active_hour:02d}:00")
    table.add_row("night commits", _pct(stats.night_commit_ratio))
    table.add_row("weekend commits", _pct(stats.weekend_commit_ratio))

    return Panel(table, title=f"{ICON_STATS} Stats", border_style="green")


def _words_panel(report: StoryReport) -> Panel:
    if report.stats.most_common_commit_words:
        words = ", ".join(
            f"{item.word} [{item.count}]" for item in report.stats.most_common_commit_words
        )
    else:
        words = "No commit message words available"

    return Panel(words, title="󰇥 Top Commit Words", border_style="magenta")


def _personality_panel(report: StoryReport) -> Panel:
    p = report.personality
    traits = ", ".join(p.traits) if p.traits else "n/a"

    body = Group(
        Text(p.personality_name, style="bold yellow"),
        Text(p.subtitle, style="bright_black"),
        Text(""),
        Text(p.summary),
        Text(""),
        Text(f"Traits: {traits}"),
        Text(f"Vibe: {p.vibe}"),
    )

    return Panel(body, title=f"{ICON_PERSONA} Developer Personality", border_style="yellow")


def _weekly_panel(report: StoryReport) -> Panel:
    graph = _activity_graph(report.stats.commits_per_weekday)
    return Panel(graph, title=f"{ICON_CAL} Weekly Activity", border_style="blue")


def _story_panel(report: StoryReport) -> Panel:
    story = "\n".join(report.personality.story_lines)
    return Panel(story, title=f"{ICON_STORY} Git Story", border_style="bright_magenta")


def _roast_panel(report: StoryReport) -> Panel:
    return Panel(report.personality.roast, title="󱐋 Roast", border_style="red")


def render_report(console: Console, report: StoryReport) -> None:
    header = _header_panel(report)
    stats_row = Columns([_stats_panel(report), _words_panel(report)], equal=True, expand=True)
    persona_row = Columns([_personality_panel(report), _weekly_panel(report)], equal=True, expand=True)
    story = _story_panel(report)
    roast = _roast_panel(report)

    console.print()
    console.print(header)
    console.print(stats_row)
    console.print(persona_row)
    console.print(story)
    console.print(roast)

    if report.used_offline_mode:
        reason = report.fallback_reason or "offline mode requested"
        console.print(f"\n[dim]fallback mode: {reason}[/dim]")
