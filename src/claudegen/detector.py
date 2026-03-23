"""
claudegen.detector
~~~~~~~~~~~~~~~~~~
Analyses a repository and returns a ProjectInfo with everything
the generator needs. Zero external dependencies — pure stdlib.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─── Data model ───────────────────────────────────────────────────────────────

@dataclass
class Commands:
    install: str = ""
    build:   str = ""
    test:    str = ""
    lint:    str = ""
    run:     str = ""
    format:  str = ""


@dataclass
class ProjectInfo:
    name:            str = ""
    description:     str = ""
    languages:       list[str] = field(default_factory=list)
    frameworks:      list[str] = field(default_factory=list)
    package_manager: str = ""
    test_runner:     str = ""
    linter:          str = ""
    formatter:       str = ""
    commands:        Commands = field(default_factory=Commands)
    structure:       dict[str, str] = field(default_factory=dict)
    conventions:     list[str] = field(default_factory=list)
    notes:           list[str] = field(default_factory=list)
    has_docker:      bool = False
    has_ci:          bool = False


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}


def _exists(*parts) -> bool:
    return Path(*parts).exists()


# ─── Language detection ───────────────────────────────────────────────────────

_EXT_LANG: dict[str, str] = {
    ".py":    "Python",
    ".ts":    "TypeScript",
    ".tsx":   "TypeScript",
    ".js":    "JavaScript",
    ".jsx":   "JavaScript",
    ".rs":    "Rust",
    ".go":    "Go",
    ".java":  "Java",
    ".kt":    "Kotlin",
    ".rb":    "Ruby",
    ".cs":    "C#",
    ".cpp":   "C++",
    ".c":     "C",
    ".swift": "Swift",
    ".php":   "PHP",
    ".ex":    "Elixir",
    ".exs":   "Elixir",
    ".hs":    "Haskell",
    ".lua":   "Lua",
    ".r":     "R",
    ".scala": "Scala",
    ".clj":   "Clojure",
}

_IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", "target", ".cargo", "vendor",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "coverage",
}


def _detect_languages(root: Path) -> list[str]:
    counts: dict[str, int] = {}
    for p in root.rglob("*"):
        if any(part in _IGNORE_DIRS for part in p.parts):
            continue
        lang = _EXT_LANG.get(p.suffix.lower())
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return sorted(counts, key=lambda k: counts[k], reverse=True)


# ─── Stack detection ──────────────────────────────────────────────────────────

def _detect_python(root: Path, info: ProjectInfo) -> None:
    # package manager
    if _exists(root, "uv.lock") or _exists(root, ".python-version"):
        info.package_manager = "uv"
        info.commands.install = "uv sync"
    elif _exists(root, "Pipfile"):
        info.package_manager = "pipenv"
        info.commands.install = "pipenv install"
    elif _exists(root, "poetry.lock"):
        info.package_manager = "poetry"
        info.commands.install = "poetry install"
    else:
        info.package_manager = "pip"
        req = "requirements-dev.txt" if _exists(root, "requirements-dev.txt") else "requirements.txt"
        if _exists(root, req):
            info.commands.install = f"pip install -r {req}"

    # pyproject.toml
    pyproject = _read_json(root / "pyproject.toml") if _exists(root, "pyproject.toml") else {}
    if not pyproject:
        # tomllib not available in 3.9 — parse manually for basics
        raw = _read(root / "pyproject.toml")
        m = re.search(r'name\s*=\s*"([^"]+)"', raw)
        if m and not info.name:
            info.name = m.group(1)
        m = re.search(r'description\s*=\s*"([^"]+)"', raw)
        if m and not info.description:
            info.description = m.group(1)
    else:
        proj = pyproject.get("project", {})
        if not info.name:
            info.name = proj.get("name", "")
        if not info.description:
            info.description = proj.get("description", "")

    # test runner
    if _exists(root, "pytest.ini") or _exists(root, "conftest.py"):
        info.test_runner = "pytest"
        info.commands.test = "pytest"
    elif any(root.rglob("test_*.py")):
        info.test_runner = "pytest"
        info.commands.test = "pytest"

    # linter / formatter
    if _exists(root, "ruff.toml") or _exists(root, ".ruff.toml"):
        info.linter = "ruff"
        info.commands.lint = "ruff check ."
        info.commands.format = "ruff format ."
    elif _exists(root, ".flake8") or _exists(root, "setup.cfg"):
        info.linter = "flake8"
        info.commands.lint = "flake8 ."

    if not info.commands.format:
        if _exists(root, ".black") or any(root.glob("pyproject.toml")):
            raw = _read(root / "pyproject.toml")
            if "[tool.black]" in raw:
                info.formatter = "black"
                info.commands.format = "black ."

    # frameworks
    deps_raw = _read(root / "pyproject.toml") + _read(root / "requirements.txt")
    fw_map = {
        "fastapi":  "FastAPI",
        "django":   "Django",
        "flask":    "Flask",
        "starlette":"Starlette",
        "tornado":  "Tornado",
        "streamlit":"Streamlit",
        "gradio":   "Gradio",
        "celery":   "Celery",
        "sqlalchemy":"SQLAlchemy",
        "pydantic": "Pydantic",
        "typer":    "Typer",
        "click":    "Click",
        "anthropic":"Anthropic SDK",
        "openai":   "OpenAI SDK",
        "langchain":"LangChain",
    }
    for key, name in fw_map.items():
        if re.search(rf'\b{key}\b', deps_raw, re.I):
            info.frameworks.append(name)

    # run command heuristics
    if not info.commands.run:
        if _exists(root, "main.py"):
            info.commands.run = "python main.py"
        elif _exists(root, "app.py"):
            info.commands.run = "python app.py"
        elif "FastAPI" in info.frameworks or "Starlette" in info.frameworks:
            info.commands.run = "uvicorn main:app --reload"
        elif "Django" in info.frameworks:
            info.commands.run = "python manage.py runserver"
        elif "Flask" in info.frameworks:
            info.commands.run = "flask run"
        elif "Streamlit" in info.frameworks:
            info.commands.run = "streamlit run app.py"


def _detect_node(root: Path, info: ProjectInfo) -> None:
    pkg = _read_json(root / "package.json")
    if not pkg:
        return

    if not info.name:
        info.name = pkg.get("name", "")
    if not info.description:
        info.description = pkg.get("description", "")

    # package manager
    if _exists(root, "pnpm-lock.yaml"):
        info.package_manager = "pnpm"
        info.commands.install = "pnpm install"
    elif _exists(root, "yarn.lock"):
        info.package_manager = "yarn"
        info.commands.install = "yarn"
    elif _exists(root, "bun.lockb"):
        info.package_manager = "bun"
        info.commands.install = "bun install"
    else:
        info.package_manager = "npm"
        info.commands.install = "npm install"

    pm = info.package_manager
    scripts = pkg.get("scripts", {})

    def _script(key: str) -> str:
        return f"{pm} run {key}" if key in scripts else ""

    info.commands.build  = _script("build")
    info.commands.test   = _script("test")
    info.commands.lint   = _script("lint")
    info.commands.format = _script("format") or _script("fmt")
    info.commands.run    = _script("dev") or _script("start")

    # frameworks
    all_deps: dict = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    fw_map = {
        "next":        "Next.js",
        "react":       "React",
        "vue":         "Vue",
        "nuxt":        "Nuxt",
        "svelte":      "Svelte",
        "@sveltejs/kit":"SvelteKit",
        "express":     "Express",
        "fastify":     "Fastify",
        "hono":        "Hono",
        "remix":       "@remix-run/react",
        "astro":       "Astro",
        "vite":        "Vite",
        "vitest":      "Vitest",
        "jest":        "Jest",
        "playwright":  "Playwright",
        "cypress":     "Cypress",
        "prisma":      "Prisma",
        "drizzle-orm": "Drizzle",
        "trpc":        "tRPC",
        "tailwindcss": "Tailwind CSS",
        "@anthropic-ai/sdk": "Anthropic SDK",
    }
    for key, name in fw_map.items():
        if key in all_deps:
            info.frameworks.append(name)

    # TypeScript
    if _exists(root, "tsconfig.json") or "typescript" in all_deps:
        if "TypeScript" not in info.languages:
            info.languages.insert(0, "TypeScript")

    # test runner
    if "vitest" in all_deps:
        info.test_runner = "vitest"
    elif "jest" in all_deps:
        info.test_runner = "jest"
    elif "playwright" in all_deps:
        info.test_runner = "playwright"


def _detect_rust(root: Path, info: ProjectInfo) -> None:
    cargo = _read(root / "Cargo.toml")
    if not cargo:
        return
    m = re.search(r'name\s*=\s*"([^"]+)"', cargo)
    if m and not info.name:
        info.name = m.group(1)
    info.package_manager  = "cargo"
    info.commands.install = ""
    info.commands.build   = "cargo build"
    info.commands.test    = "cargo test"
    info.commands.lint    = "cargo clippy"
    info.commands.format  = "cargo fmt"
    info.commands.run     = "cargo run"


def _detect_go(root: Path, info: ProjectInfo) -> None:
    gomod = _read(root / "go.mod")
    if not gomod:
        return
    m = re.search(r'^module\s+(\S+)', gomod, re.M)
    if m and not info.name:
        info.name = m.group(1).split("/")[-1]
    info.package_manager  = "go modules"
    info.commands.install = "go mod tidy"
    info.commands.build   = "go build ./..."
    info.commands.test    = "go test ./..."
    info.commands.lint    = "golangci-lint run"
    info.commands.run     = "go run ."


def _detect_ruby(root: Path, info: ProjectInfo) -> None:
    if not _exists(root, "Gemfile"):
        return
    gemfile = _read(root / "Gemfile")
    info.package_manager  = "bundler"
    info.commands.install = "bundle install"
    info.commands.test    = "bundle exec rspec" if "rspec" in gemfile else "bundle exec rake test"
    if "rails" in gemfile.lower():
        info.frameworks.append("Rails")
        info.commands.run = "rails server"


# ─── Structure detection ──────────────────────────────────────────────────────

_DIR_DESCRIPTIONS = {
    "src":        "Main source code",
    "lib":        "Library code",
    "app":        "Application code",
    "tests":      "Test files",
    "test":       "Test files",
    "spec":       "Test specifications",
    "docs":       "Documentation",
    "scripts":    "Utility scripts",
    "config":     "Configuration files",
    "migrations": "Database migrations",
    "public":     "Static assets",
    "static":     "Static assets",
    "assets":     "Assets",
    "components": "UI components",
    "pages":      "Page components",
    "api":        "API routes / handlers",
    "models":     "Data models",
    "services":   "Business logic / services",
    "utils":      "Utility functions",
    "hooks":      "React hooks",
    "store":      "State management",
    "types":      "TypeScript types",
    "db":         "Database layer",
    "cmd":        "CLI entry points",
    "internal":   "Internal packages",
    "pkg":        "Shared packages",
    "examples":   "Example code",
    "bin":        "Executables",
}


def _detect_structure(root: Path) -> dict[str, str]:
    result = {}
    for d in sorted(root.iterdir()):
        if d.is_dir() and d.name in _DIR_DESCRIPTIONS and d.name not in _IGNORE_DIRS:
            result[d.name] = _DIR_DESCRIPTIONS[d.name]
    return result


# ─── Convention detection ─────────────────────────────────────────────────────

def _detect_conventions(root: Path, languages: list[str]) -> list[str]:
    conventions = []
    lang = languages[0] if languages else ""

    if lang == "Python":
        # Sample a few Python files
        samples = list(root.rglob("*.py"))[:10]
        text = "\n".join(_read(f) for f in samples if "test" not in str(f))

        # indentation
        if re.search(r'^\t', text, re.M):
            conventions.append("Indentation: tabs")
        else:
            conventions.append("Indentation: 4 spaces")

        # type annotations
        if re.search(r'def \w+\([^)]*:\s*\w', text):
            conventions.append("Type annotations used")

        # docstrings
        if '"""' in text or "'''" in text:
            conventions.append('Docstrings with triple quotes')

    elif lang in ("TypeScript", "JavaScript"):
        samples = list(root.rglob("*.ts"))[:5] + list(root.rglob("*.tsx"))[:5]
        text = "\n".join(_read(f) for f in samples)

        # quotes
        single = len(re.findall(r"'[^']*'", text))
        double = len(re.findall(r'"[^"]*"', text))
        conventions.append(f"Prefer {'single' if single > double else 'double'} quotes")

        # semicolons
        semi = len(re.findall(r';$', text, re.M))
        conventions.append(f"{'Semicolons required' if semi > 20 else 'No semicolons'}")

        # indent
        two = len(re.findall(r'^  \w', text, re.M))
        four = len(re.findall(r'^    \w', text, re.M))
        conventions.append(f"Indentation: {'2' if two > four else '4'} spaces")

    return conventions


# ─── README extraction ────────────────────────────────────────────────────────

def _extract_readme(root: Path, info: ProjectInfo) -> None:
    for name in ("README.md", "README.rst", "README.txt", "README"):
        p = root / name
        if p.exists():
            text = _read(p)
            if not info.name:
                m = re.search(r'^#\s+(.+)', text, re.M)
                if m:
                    info.name = m.group(1).strip()
            if not info.description:
                # grab first non-heading, non-empty paragraph
                for line in text.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("!"):
                        info.description = line[:200]
                        break
            break


# ─── Main entry point ─────────────────────────────────────────────────────────

def detect(root: Path) -> ProjectInfo:
    info = ProjectInfo()

    info.languages = _detect_languages(root)

    # Stack-specific detection
    if _exists(root, "pyproject.toml") or _exists(root, "setup.py") or _exists(root, "requirements.txt"):
        _detect_python(root, info)
    if _exists(root, "package.json"):
        _detect_node(root, info)
    if _exists(root, "Cargo.toml"):
        _detect_rust(root, info)
    if _exists(root, "go.mod"):
        _detect_go(root, info)
    if _exists(root, "Gemfile"):
        _detect_ruby(root, info)

    # Fallbacks
    _extract_readme(root, info)

    if not info.name:
        info.name = root.name

    info.structure   = _detect_structure(root)
    info.conventions = _detect_conventions(root, info.languages)

    # Infrastructure
    info.has_docker = _exists(root, "Dockerfile") or _exists(root, "docker-compose.yml")
    info.has_ci     = _exists(root, ".github", "workflows") or _exists(root, ".gitlab-ci.yml") or _exists(root, ".circleci")

    # Extra notes
    if info.has_docker:
        info.notes.append("Docker available — use `docker compose up` for local infra")
    if _exists(root, ".env.example"):
        info.notes.append("Copy `.env.example` to `.env` before running locally")
    if _exists(root, "CLAUDE.md"):
        info.notes.append("A CLAUDE.md already existed — this file replaces it")

    return info
