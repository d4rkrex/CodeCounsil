"""
CodeCounsil Adapter Installer

Installs CodeCounsil integration files into the target repository
for Claude Code, GitHub Copilot, and/or OpenCode.

Usage:
    codecounsil-install                    # auto-detect + install all
    codecounsil-install --platform claude  # Claude Code only
    codecounsil-install --platform copilot # GitHub Copilot only
    codecounsil-install --platform opencode # OpenCode only
    codecounsil-install --platform all     # all platforms
    codecounsil-install --repo /path/to/repo
    codecounsil-install --force            # overwrite existing files
    codecounsil-install --dry-run          # preview without writing
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Package root — adapters live alongside this file's package
_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_ADAPTERS_DIR = _PACKAGE_ROOT / "adapters"


# ── Platform definitions ──────────────────────────────────────────────────────

PLATFORMS: dict[str, dict] = {
    "claude": {
        "name": "Claude Code",
        "detect": lambda repo: (repo / ".claude").exists(),
        "files": [
            {
                "src": _ADAPTERS_DIR / "claude-code" / "skills" / "project-review" / "SKILL.md",
                "dst": Path(".claude") / "commands" / "project-review.md",
                "mkdir": True,
                "description": "Slash command /project-review",
            },
        ],
        "agent_glob": {
            "src_dir": _ADAPTERS_DIR / "claude-code" / "agents",
            "dst_dir": Path(".claude") / "agents",
            "pattern": "*.md",
            "description": "Specialist sub-agents",
        },
    },
    "copilot": {
        "name": "GitHub Copilot",
        "detect": lambda repo: (repo / ".github").exists(),
        "files": [
            {
                "src": _ADAPTERS_DIR / "github-copilot" / "copilot-instructions.md",
                "dst": Path(".github") / "copilot-instructions.md",
                "mkdir": True,
                "description": "Copilot workspace instructions",
                "merge": True,  # append if already exists
            },
        ],
        "agent_glob": None,
    },
    "opencode": {
        "name": "OpenCode",
        "detect": lambda repo: (repo / "AGENTS.md").exists() or (repo / ".opencode").exists(),
        "files": [
            {
                "src": _ADAPTERS_DIR / "opencode" / "AGENTS.md",
                "dst": Path("AGENTS.md"),
                "mkdir": False,
                "description": "AGENTS.md (OpenCode + Copilot agents)",
                "merge": True,  # append if already exists
            },
        ],
        "agent_glob": None,
    },
}


# ── Installer ─────────────────────────────────────────────────────────────────

def install(
    repo_path: Path,
    platforms: list[str],
    force: bool = False,
    dry_run: bool = False,
) -> int:
    """
    Install adapter files for the requested platforms.
    Returns number of files written.
    """
    repo = repo_path.resolve()
    if not repo.is_dir():
        print(f"Error: {repo} is not a directory.", file=sys.stderr)
        return 0

    written = 0
    for platform_key in platforms:
        spec = PLATFORMS[platform_key]
        print(f"\n{'─'*50}")
        print(f"  {spec['name']}")
        print(f"{'─'*50}")

        # Install individual files
        for file_spec in spec["files"]:
            count = _install_file(repo, file_spec, force=force, dry_run=dry_run)
            written += count

        # Install agent glob (e.g. claude agents/*.md)
        if spec.get("agent_glob"):
            ag = spec["agent_glob"]
            count = _install_glob(repo, ag, force=force, dry_run=dry_run)
            written += count

    if written == 0:
        print("\nNothing to install (all files already up to date). Use --force to overwrite.")
    else:
        action = "Would write" if dry_run else "Wrote"
        print(f"\n✅ {action} {written} file(s).")
        if not dry_run:
            print(f"\nNext steps:")
            if "claude" in platforms:
                print("  Claude Code  → open repo in Claude Code, run: /project-review full")
            if "copilot" in platforms:
                print("  GitHub Copilot → ask Copilot: 'run a full CodeCounsil review'")
            if "opencode" in platforms:
                print("  OpenCode → open repo in OpenCode, ask: 'run project-review full'")
            print("\n  After specialist agents write findings:")
            print("  → project-review --consolidate-only")
    return written


def _install_file(repo: Path, spec: dict, force: bool, dry_run: bool) -> int:
    src: Path = spec["src"]
    dst: Path = repo / spec["dst"]
    desc: str = spec.get("description", "")
    merge: bool = spec.get("merge", False)
    mkdir: bool = spec.get("mkdir", False)

    if not src.exists():
        print(f"  ⚠️  Source not found: {src.relative_to(_PACKAGE_ROOT)}")
        return 0

    if dst.exists() and not force and not merge:
        print(f"  ↩️  Skip  {spec['dst']}  ({desc}) — already exists, use --force to overwrite")
        return 0

    if dst.exists() and merge:
        existing = dst.read_text(encoding="utf-8")
        new_content = src.read_text(encoding="utf-8")
        marker = "<!-- codecounsil-adapter -->"
        if marker in existing:
            print(f"  ↩️  Skip  {spec['dst']}  ({desc}) — CodeCounsil section already present")
            return 0
        # Append with separator
        merged = existing.rstrip() + f"\n\n{marker}\n\n" + new_content
        if dry_run:
            print(f"  ✏️  Merge {spec['dst']}  ({desc})")
        else:
            if mkdir:
                dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(merged, encoding="utf-8")
            print(f"  ✅  Merge {spec['dst']}  ({desc})")
        return 1

    if dry_run:
        print(f"  ✏️  Write {spec['dst']}  ({desc})")
    else:
        if mkdir:
            dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  ✅  Write {spec['dst']}  ({desc})")
    return 1


def _install_glob(repo: Path, spec: dict, force: bool, dry_run: bool) -> int:
    src_dir: Path = spec["src_dir"]
    dst_dir: Path = repo / spec["dst_dir"]
    pattern: str = spec["pattern"]
    desc: str = spec.get("description", "")

    if not src_dir.is_dir():
        print(f"  ⚠️  Agent directory not found: {src_dir}")
        return 0

    written = 0
    for src_file in sorted(src_dir.glob(pattern)):
        dst_file = dst_dir / src_file.name
        if dst_file.exists() and not force:
            print(f"  ↩️  Skip  {spec['dst_dir']}/{src_file.name} — already exists")
            continue
        if dry_run:
            print(f"  ✏️  Write {spec['dst_dir']}/{src_file.name}")
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            print(f"  ✅  Write {spec['dst_dir']}/{src_file.name}")
        written += 1

    if written > 0:
        print(f"  ({desc})")
    return written


def _auto_detect(repo: Path) -> list[str]:
    """Detect which platforms are already set up in the repo."""
    detected = []
    for key, spec in PLATFORMS.items():
        if spec["detect"](repo):
            detected.append(key)
    # Always include all if nothing detected
    return detected if detected else list(PLATFORMS.keys())


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="codecounsil-install",
        description="Install CodeCounsil adapter files into a target repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Platforms:
  claude    Claude Code (.claude/commands/ and .claude/agents/)
  copilot   GitHub Copilot (.github/copilot-instructions.md)
  opencode  OpenCode (AGENTS.md in project root)
  all       All platforms (default)

Examples:
  codecounsil-install                        # auto-detect, install all
  codecounsil-install --platform all         # install all platforms
  codecounsil-install --platform claude      # Claude Code only
  codecounsil-install --platform copilot opencode  # two platforms
  codecounsil-install --repo /path/to/repo   # different repo
  codecounsil-install --force                # overwrite existing files
  codecounsil-install --dry-run              # preview without writing
""",
    )
    parser.add_argument(
        "--platform",
        nargs="+",
        choices=[*PLATFORMS.keys(), "all"],
        default=["all"],
        metavar="PLATFORM",
        help="Target platform(s): claude, copilot, opencode, all (default: all)",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Target repository path (default: current directory)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing adapter files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be installed without writing files",
    )

    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    # Resolve platform list
    requested = args.platform
    if "all" in requested:
        platforms = list(PLATFORMS.keys())
    else:
        platforms = requested

    print(f"\nCodeCounsil Installer")
    print(f"  Repository : {repo}")
    print(f"  Platforms  : {', '.join(PLATFORMS[p]['name'] for p in platforms)}")
    if args.dry_run:
        print(f"  Mode       : DRY RUN (no files written)")
    if args.force:
        print(f"  Mode       : FORCE (overwriting existing files)")

    install(repo, platforms, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
