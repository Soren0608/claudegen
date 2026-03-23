# claudegen

Automatic `CLAUDE.md` generator. Analyses your repo and writes the file for you.

## Install

```bash
pip install claudegen
```

## Usage

```bash
# Analyse current directory and write CLAUDE.md
claudegen

# Preview without writing
claudegen --dry-run

# Overwrite existing CLAUDE.md
claudegen --force

# Analyse a specific repo
claudegen ~/projects/myapp
```

## What it detects

- **Languages** — Python, TypeScript, JavaScript, Rust, Go, Ruby, and more
- **Frameworks** — FastAPI, Django, Next.js, React, Express, and more
- **Package manager** — pip, uv, poetry, npm, pnpm, yarn, cargo, etc.
- **Test runner** — pytest, jest, vitest, go test, cargo test
- **Linter / formatter** — ruff, black, eslint, prettier, clippy
- **Commands** — install, build, test, lint, run
- **Project structure** — key directories with descriptions
- **Code conventions** — indentation, quotes, type annotations
- **Infrastructure** — Docker, CI/CD

## Why

CLAUDE.md is the most important file for getting good results from Claude Code, but it's tedious to write from scratch. `claudegen` does it in one command.

## Zero dependencies

Pure Python stdlib. No extra packages required.
