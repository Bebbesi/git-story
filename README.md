# git-story

`git-story` turns your Git history into a **developer profile + project narrative**.
It computes repository statistics locally, then uses Gemini to generate a personality snapshot, a short story, and a playful roast.

Built for terminal-first developers who want insight without dashboards.

## Why git-story

- Fast CLI workflow for Linux/macOS
- Local-first analytics (no AI for numeric stats)
- Structured Gemini output validated with Pydantic
- Rich, hacker-style terminal UI with Nerd Font icons
- Works fully offline with smart fallback personas

## Features

- Repository analytics from `git log`
- Commit behavior metrics:
  - total commits
  - active days
  - longest streak
  - commits per weekday
  - most active hour
  - night commit ratio (22:00–06:00)
  - weekend commit ratio
  - top commit words
  - primary author
- AI-generated sections:
  - personality name + subtitle
  - traits
  - coding style summary
  - playful roast
  - 4-line repo story
- JSON output mode for scripting/automation

## Tech Stack

- Python 3.11+
- `rich`
- `google-genai`
- `pydantic`
- `python-dotenv`
- `subprocess` (for Git commands)

## Installation

```bash
git clone https://github.com/bebbesi/git-story.git
cd git-story
./install.sh
```

After install, run:

```bash
git-story --help
```

### One-command install (Linux/macOS)

From a local clone:

```bash
./install.sh
```

What `install.sh` does:

- Uses `pipx` if available (recommended)
- Falls back to an isolated virtual environment at `~/.local/share/git-story/venv`
- Creates a launcher at `~/.local/bin/git-story`

If `git-story` is still not found after install, add this once:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Then verify:

```bash
git-story --help
```

## Configuration

Create an environment file:

```bash
cp .env.example .env
```

Set variables:

- `GEMINI_API_KEY` required for AI mode
- `GIT_STORY_MODEL` optional, defaults to `gemini-2.5-flash`

Example `.env`:

```env
GEMINI_API_KEY=your_api_key_here
GIT_STORY_MODEL=gemini-2.5-flash
```

## Quick Start

Analyze the current repository:

```bash
git-story
```

Run without AI (offline fallback):

```bash
git-story --offline
```

Analyze a different repository:

```bash
git-story --repo /path/to/repo
```

Filter by author:

```bash
git-story --author "Bebbesi"
```

JSON output for scripts:

```bash
git-story --json
```

## CLI Reference

```text
git-story [--repo PATH] [--author NAME] [--offline] [--json] [--model MODEL_NAME] [--no-color]
```

- `--repo PATH` Analyze a specific git repository
- `--author NAME` Filter commits by author
- `--offline` Disable Gemini and use local fallback personality
- `--json` Print raw JSON report
- `--model MODEL_NAME` Override Gemini model
- `--no-color` Disable colored output

## Example Output

```text
git-story

󰊢 cool-cli-tool
󰀄 Bebbesi

󰔟 Stats
commits            142
active days         39
longest streak   6 days
avg/day           3.64
most active hour 23:00
night commits      41%
weekend commits    48%

󰇥 Top Commit Words
fix [28], add [24], refactor [11]

󰊠 Developer Personality
The Midnight Debugger
Thrives after dark

Traits: persistent, night-owl, iterative
Vibe: chaotic

󰃰 Weekly Activity
Mon ████            12
Tue ███              9
Wed ███████         20
Thu ██               5
Fri █████            16
Sat █████████       27
Sun ██               8

󰈭 Git Story
It started quietly, with a few careful commits.
Then the repo found its rhythm around Sat.
fix kept showing up like a recurring side character.
By the end, the project felt less like homework and more like a habit.

󱐋 Roast
Your sleep schedule lost a long time ago, and so did fix.
```

## How It Works

1. Detects and validates a git repository.
2. Reads commits with:
   ```bash
   git log --pretty=format:%H%x1f%an%x1f%ae%x1f%aI%x1f%s
   ```
3. Computes all statistics locally.
4. Sends only calculated stats to Gemini for text generation.
5. Validates Gemini JSON with Pydantic schema.
6. Renders a terminal dashboard with Rich.

## Project Structure

```text
git-story/
├── git_story/
│   ├── __init__.py
│   ├── __main__.py
│   ├── ai.py
│   ├── cli.py
│   ├── git_utils.py
│   ├── main.py
│   ├── models.py
│   └── render.py
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Development

Run directly without installed entrypoint:

```bash
python3 -m git_story.cli --offline
```

Useful checks:

```bash
python3 -m compileall git_story
```

## Troubleshooting

- `git-story: command not found`
  - Add `~/.local/bin` to `PATH`:
    ```bash
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
    ```
  - Or run directly:
    ```bash
    ~/.local/bin/git-story --help
    ```
- `ModuleNotFoundError`
  - Re-run:
    ```bash
    ./install.sh
    ```
- `error: externally-managed-environment` (PEP 668 on Arch)
  - Use `./install.sh` (already handles this safely without system pip).
- `No commits found`
  - Ensure the target path is a git repo and the `--author` filter matches existing commits.
- AI fallback activated
  - Check `GEMINI_API_KEY` in `.env`, network access, and model name.

## License

MIT
