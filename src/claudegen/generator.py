"""
claudegen.generator
~~~~~~~~~~~~~~~~~~~
Turns a ProjectInfo into a CLAUDE.md string.
"""

from __future__ import annotations

from .detector import ProjectInfo


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body.strip()}\n"


def generate(info: ProjectInfo) -> str:
    parts: list[str] = []

    # ── Header ────────────────────────────────────────────────────────────────
    parts.append("# CLAUDE.md\n")
    parts.append(
        "This file provides guidance to Claude Code (claude.ai/code) "
        "when working with this repository.\n"
    )

    # ── Project overview ──────────────────────────────────────────────────────
    overview_lines = []
    if info.description:
        overview_lines.append(info.description)
    if info.languages:
        overview_lines.append(f"**Primary language:** {info.languages[0]}")
    if info.frameworks:
        overview_lines.append(f"**Frameworks / libraries:** {', '.join(info.frameworks[:6])}")
    if info.package_manager:
        overview_lines.append(f"**Package manager:** {info.package_manager}")
    if overview_lines:
        parts.append(_section("Project Overview", "\n\n".join(overview_lines)))

    # ── Commands ──────────────────────────────────────────────────────────────
    cmd = info.commands
    cmd_lines = []
    if cmd.install:
        cmd_lines.append(f"# Install dependencies\n{cmd.install}")
    if cmd.run:
        cmd_lines.append(f"# Run / development server\n{cmd.run}")
    if cmd.build:
        cmd_lines.append(f"# Build\n{cmd.build}")
    if cmd.test:
        cmd_lines.append(f"# Run tests\n{cmd.test}")
    if cmd.lint:
        cmd_lines.append(f"# Lint\n{cmd.lint}")
    if cmd.format:
        cmd_lines.append(f"# Format\n{cmd.format}")
    if cmd_lines:
        block = "```bash\n" + "\n\n".join(cmd_lines) + "\n```"
        parts.append(_section("Common Commands", block))

    # ── Project structure ─────────────────────────────────────────────────────
    if info.structure:
        rows = "\n".join(f"  {d}/{'':10s}  # {desc}" for d, desc in info.structure.items())
        block = f"```\n{rows}\n```"
        parts.append(_section("Project Structure", block))

    # ── Code conventions ──────────────────────────────────────────────────────
    if info.conventions:
        bullet_list = "\n".join(f"- {c}" for c in info.conventions)
        parts.append(_section("Code Conventions", bullet_list))

    # ── Architecture notes ────────────────────────────────────────────────────
    arch_lines = []
    if info.has_docker:
        arch_lines.append("- Containerised with Docker")
    if info.has_ci:
        arch_lines.append("- CI/CD pipeline configured")
    if info.test_runner:
        arch_lines.append(f"- Test runner: **{info.test_runner}**")
    if info.linter:
        arch_lines.append(f"- Linter: **{info.linter}**")
    if info.formatter:
        arch_lines.append(f"- Formatter: **{info.formatter}**")
    if arch_lines:
        parts.append(_section("Architecture Notes", "\n".join(arch_lines)))

    # ── Important notes ───────────────────────────────────────────────────────
    if info.notes:
        bullet_list = "\n".join(f"- {n}" for n in info.notes)
        parts.append(_section("Important Notes", bullet_list))

    return "\n".join(parts)
