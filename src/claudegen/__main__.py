"""
claudegen.__main__
~~~~~~~~~~~~~~~~~~
CLI entry point.

Usage
-----
  claudegen                   # analyse current dir, write CLAUDE.md
  claudegen /path/to/repo     # analyse a specific repo
  claudegen --dry-run         # print to stdout, don't write
  claudegen --force           # overwrite existing CLAUDE.md
  claudegen --output PATH     # write to a custom path
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .detector import detect
from .generator import generate

_GREEN = "\033[92m"
_YEL   = "\033[93m"
_RED   = "\033[91m"
_BOLD  = "\033[1m"
_DIM   = "\033[2m"
_RST   = "\033[0m"


def _info(msg: str)  -> None: print(f"  {_GREEN}✓{_RST}  {msg}")
def _warn(msg: str)  -> None: print(f"  {_YEL}⚠{_RST}  {msg}")
def _error(msg: str) -> None: print(f"  {_RED}✗{_RST}  {msg}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="claudegen",
        description="Automatic CLAUDE.md generator. Zero dependencies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  claudegen                   analyse current directory
  claudegen ~/projects/myapp  analyse a specific repo
  claudegen --dry-run         preview without writing
  claudegen --force           overwrite existing CLAUDE.md
        """,
    )
    parser.add_argument("repo", nargs="?", default=".", help="path to repo (default: .)")
    parser.add_argument("--version",  action="version", version=f"claudegen {__version__}")
    parser.add_argument("--dry-run",  action="store_true", help="print to stdout, don't write file")
    parser.add_argument("--force",    action="store_true", help="overwrite existing CLAUDE.md")
    parser.add_argument("--output",   metavar="PATH",      help="custom output path (default: <repo>/CLAUDE.md)")
    args = parser.parse_args()

    root = Path(args.repo).expanduser().resolve()
    if not root.is_dir():
        _error(f"Not a directory: {root}")
        sys.exit(1)

    out_path = Path(args.output).expanduser().resolve() if args.output else root / "CLAUDE.md"

    # Guard against overwriting
    if not args.dry_run and out_path.exists() and not args.force:
        _warn(f"CLAUDE.md already exists at {out_path}")
        _warn("Use --force to overwrite.")
        sys.exit(1)

    # Analyse
    print(f"\n  {_BOLD}claudegen{_RST} {_DIM}v{__version__}{_RST}\n")
    print(f"  Analysing {_BOLD}{root}{_RST} …\n")

    info = detect(root)

    _info(f"Project:    {info.name or '(unnamed)'}")
    if info.languages:
        _info(f"Languages:  {', '.join(info.languages[:4])}")
    if info.frameworks:
        _info(f"Frameworks: {', '.join(info.frameworks[:5])}")
    if info.package_manager:
        _info(f"Package mgr:{info.package_manager}")
    if info.test_runner:
        _info(f"Tests:      {info.test_runner}")

    content = generate(info)

    if args.dry_run:
        print(f"\n{'─' * 60}\n")
        print(content)
        print(f"{'─' * 60}\n")
        print(f"  {_DIM}(dry-run — nothing written){_RST}\n")
        return

    out_path.write_text(content, encoding="utf-8")
    _info(f"Written to  {out_path}")
    print()


if __name__ == "__main__":
    main()
