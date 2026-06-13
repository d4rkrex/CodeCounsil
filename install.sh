#!/usr/bin/env bash
# ============================================================
#  CodeCounsil — Installer & Updater
#  Usage:
#    ./install.sh              # fresh install
#    ./install.sh --update     # update to latest version
#    ./install.sh --force      # overwrite everything
# ============================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN="\033[0;32m"; YELLOW="\033[1;33m"; CYAN="\033[0;36m"; RED="\033[0;31m"
BOLD="\033[1m"; RESET="\033[0m"

# ── Parse flags ────────────────────────────────────────────
MODE="install"   # install | update | force
for arg in "$@"; do
  case "$arg" in
    --update|-u) MODE="update" ;;
    --force|-f)  MODE="force"  ;;
    --help|-h)
      echo "Usage: ./install.sh [--update | --force]"
      echo "  (no flag)  Fresh install — skips existing files"
      echo "  --update   Pull latest code + update all adapter files"
      echo "  --force    Overwrite all files without asking"
      exit 0 ;;
  esac
done

echo ""
if [[ "$MODE" == "update" ]]; then
  echo -e "${BOLD}╔══════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}║       CodeCounsil — Update               ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}"
elif [[ "$MODE" == "force" ]]; then
  echo -e "${BOLD}╔══════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}║       CodeCounsil — Force Install        ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}"
else
  echo -e "${BOLD}╔══════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}║        CodeCounsil Installer             ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}"
fi
echo ""

# ── 0. Git pull if updating ────────────────────────────────
if [[ "$MODE" == "update" ]]; then
  echo -e "${CYAN}▶ Pulling latest version from git...${RESET}"
  if git -C "$REPO_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    CURRENT_COMMIT=$(git -C "$REPO_DIR" rev-parse --short HEAD)
    git -C "$REPO_DIR" pull origin main --quiet
    NEW_COMMIT=$(git -C "$REPO_DIR" rev-parse --short HEAD)
    if [[ "$CURRENT_COMMIT" == "$NEW_COMMIT" ]]; then
      echo -e "${GREEN}  ✓ Already up to date ($CURRENT_COMMIT)${RESET}"
    else
      echo -e "${GREEN}  ✓ Updated $CURRENT_COMMIT → $NEW_COMMIT${RESET}"
    fi
  else
    echo -e "  ${YELLOW}Not a git repo — skipping git pull${RESET}"
  fi
  echo ""
fi

# ── 1. Install Python package ──────────────────────────────

echo -e "${CYAN}▶ Installing CodeCounsil Python package...${RESET}"

# Use pip3 if available, fallback to pip
PIP=$(command -v pip3 2>/dev/null || command -v pip 2>/dev/null || echo "")
if [[ -z "$PIP" ]]; then
  echo "Error: pip not found. Install Python 3.9+ first." >&2
  exit 1
fi

$PIP install -e "$REPO_DIR" --quiet
echo -e "${GREEN}  ✓ package installed (editable mode)${RESET}"
echo ""

# ── 2. Detect installed coding agents ──────────────────────

echo -e "${CYAN}▶ Detecting installed coding agents...${RESET}"

HAS_CLAUDE=0; HAS_COPILOT=0; HAS_OPENCODE=0; HAS_COPILOT_CLI=0

# In update/force mode: detect what's ALREADY INSTALLED (by checking existing files)
# In install mode: detect by binary/extension presence
if [[ "$MODE" == "update" || "$MODE" == "force" ]]; then
  # Check for existing CodeCounsil adapter files
  [[ -f "$HOME/.claude/commands/project-review.md" ]] && HAS_CLAUDE=1
  [[ -f "$HOME/.copilot/skills/codecounsil/SKILL.md" ]] && HAS_COPILOT_CLI=1
  # For Copilot VS / OpenCode, check if any project recently installed adapters
  # Fall back to binary detection
  command -v claude &>/dev/null && HAS_CLAUDE=1
  [[ -d "$HOME/.copilot/skills" ]] && HAS_COPILOT_CLI=1
  command -v opencode &>/dev/null && HAS_OPENCODE=1
  # Don't prompt for undetected agents in update mode
else
  # Fresh install: detect by binary/extension presence
  command -v claude &>/dev/null && HAS_CLAUDE=1
  [[ -d "$HOME/.copilot/skills" ]] && HAS_COPILOT_CLI=1
  if command -v gh &>/dev/null && gh extension list 2>/dev/null | grep -q "copilot"; then
    HAS_COPILOT=1
  fi
  if [[ -d "$HOME/.vscode/extensions" ]] && ls "$HOME/.vscode/extensions/" 2>/dev/null | grep -qi "github.copilot"; then
    HAS_COPILOT=1
  fi
  command -v cursor &>/dev/null && HAS_COPILOT=1
  command -v opencode &>/dev/null && HAS_OPENCODE=1
fi

[[ $HAS_CLAUDE       -eq 1 ]] && echo -e "  ${GREEN}✓ Claude Code${RESET}"           || echo -e "  ○ Claude Code — not detected"
[[ $HAS_COPILOT_CLI  -eq 1 ]] && echo -e "  ${GREEN}✓ GitHub Copilot CLI${RESET}"    || echo -e "  ○ GitHub Copilot CLI — not detected"
[[ $HAS_COPILOT      -eq 1 ]] && echo -e "  ${GREEN}✓ GitHub Copilot (VS Code)${RESET}" || true
[[ $HAS_OPENCODE     -eq 1 ]] && echo -e "  ${GREEN}✓ OpenCode${RESET}"               || echo -e "  ○ OpenCode — not detected"
echo ""

# Only prompt in fresh install mode
if [[ "$MODE" == "install" ]]; then
  if [[ $HAS_CLAUDE -eq 0 || $HAS_COPILOT_CLI -eq 0 || $HAS_COPILOT -eq 0 || $HAS_OPENCODE -eq 0 ]]; then
    echo -e "${YELLOW}Some agents were not auto-detected. Install adapters for them anyway?${RESET}"
    [[ $HAS_CLAUDE      -eq 0 ]] && read -rp "  Install Claude Code adapter?            [y/N] " r && [[ "$r" =~ ^[Yy] ]] && HAS_CLAUDE=1
    [[ $HAS_COPILOT_CLI -eq 0 ]] && read -rp "  Install GitHub Copilot CLI skill?       [y/N] " r && [[ "$r" =~ ^[Yy] ]] && HAS_COPILOT_CLI=1
    [[ $HAS_COPILOT     -eq 0 ]] && read -rp "  Install GitHub Copilot VS Code adapter? [y/N] " r && [[ "$r" =~ ^[Yy] ]] && HAS_COPILOT=1
    [[ $HAS_OPENCODE    -eq 0 ]] && read -rp "  Install OpenCode adapter?               [y/N] " r && [[ "$r" =~ ^[Yy] ]] && HAS_OPENCODE=1
    echo ""
  fi
fi

if [[ $HAS_CLAUDE -eq 0 && $HAS_COPILOT_CLI -eq 0 && $HAS_COPILOT -eq 0 && $HAS_OPENCODE -eq 0 ]]; then
  echo "No agents detected or selected. Nothing to install."
  exit 0
fi

# ── 3. Global or per-project? ──────────────────────────────

# In update mode: default global (where most things are installed)
if [[ "$MODE" == "update" || "$MODE" == "force" ]]; then
  INSTALL_MODE="global"
  TARGET="$HOME"
  echo -e "${CYAN}▶ Updating global adapter files...${RESET}"
  echo ""
else
  echo -e "${CYAN}▶ Where do you want to install the adapters?${RESET}"
  echo ""
  echo -e "  ${BOLD}[1] Global${RESET} — installs to your home config directories"
  echo -e "      ${YELLOW}Claude Code${RESET}       → ~/.claude/commands/ and ~/.claude/agents/"
  echo -e "      ${YELLOW}Copilot CLI${RESET}       → ~/.copilot/skills/codecounsil/"
  echo -e "      ${YELLOW}GitHub Copilot VS${RESET} → (per-project only)"
  echo -e "      ${YELLOW}OpenCode${RESET}           → (per-project only)"
  echo ""
  echo -e "  ${BOLD}[2] Per-project${RESET} — installs into a specific repo"
  echo -e "      Adds adapter files directly to that repository's config dirs"
  echo ""

  while true; do
    read -rp "Choice [1/2]: " INSTALL_MODE
    case "$INSTALL_MODE" in
      1) INSTALL_MODE="global"; break ;;
      2) INSTALL_MODE="project"; break ;;
      *) echo "Please enter 1 or 2." ;;
    esac
  done
  echo ""
fi

# ── 4. Get target path ─────────────────────────────────────

if [[ "$INSTALL_MODE" == "project" ]]; then
  echo -e "${CYAN}▶ Target repository path${RESET}"
  read -rp "  Path to the project to review [.]: " TARGET
  TARGET="${TARGET:-.}"
  TARGET="$(cd "$TARGET" 2>/dev/null && pwd)" || { echo "Error: path not found: $TARGET" >&2; exit 1; }
  echo -e "  Target: ${BOLD}$TARGET${RESET}"
  echo ""
fi

# ── 5. Install adapter files ───────────────────────────────

if [[ "$MODE" == "update" || "$MODE" == "force" ]]; then
  echo -e "${CYAN}▶ Updating adapters...${RESET}"
else
  echo -e "${CYAN}▶ Installing adapters...${RESET}"
fi
echo ""

PLATFORMS=""
[[ $HAS_CLAUDE      -eq 1 ]] && PLATFORMS="$PLATFORMS claude"
[[ $HAS_COPILOT_CLI -eq 1 ]] && PLATFORMS="$PLATFORMS copilot_cli"
[[ $HAS_COPILOT     -eq 1 ]] && PLATFORMS="$PLATFORMS copilot"
[[ $HAS_OPENCODE    -eq 1 ]] && PLATFORMS="$PLATFORMS opencode"

install_adapters() {
  local target="$1"
  local platforms="$2"
  local force_mode="${3:-$MODE}"  # inherit global MODE

  for platform in $platforms; do
    case "$platform" in
      claude)
        echo -e "  ${BOLD}Claude Code${RESET}"
        mkdir -p "$target/.claude/commands" "$target/.claude/agents"
        cp "$REPO_DIR/adapters/claude-code/skills/project-review/SKILL.md" \
           "$target/.claude/commands/project-review.md"
        echo -e "    ${GREEN}✓${RESET} .claude/commands/project-review.md  (/project-review slash command)"
        count=0
        for f in "$REPO_DIR/adapters/claude-code/agents/"*.md; do
          dest="$target/.claude/agents/$(basename "$f")"
          cp "$f" "$dest"
          count=$((count+1))
        done
        echo -e "    ${GREEN}✓${RESET} .claude/agents/  ($count specialist agents)"
        ;;
      copilot_cli)
        # Copilot CLI skills — always global regardless of mode
        echo -e "  ${BOLD}GitHub Copilot CLI${RESET}"
        SKILL_DIR="$HOME/.copilot/skills/codecounsil"
        mkdir -p "$SKILL_DIR"
        cp "$REPO_DIR/adapters/copilot-cli/SKILL.md" "$SKILL_DIR/SKILL.md"
        echo -e "    ${GREEN}✓${RESET} ~/.copilot/skills/codecounsil/SKILL.md  (trigger: 'run a CodeCounsil review')"
        # Also install combined skill if appsec-plugins is installed
        if [[ -d "$HOME/.copilot/installed-plugins/appsec-plugins" ]] || \
           ls "$HOME/.copilot/skills/" 2>/dev/null | grep -q "appsec"; then
          COMBINED_DIR="$HOME/.copilot/skills/appsec-codecounsil"
          mkdir -p "$COMBINED_DIR"
          cp "$REPO_DIR/adapters/appsec-plugins/SKILL.md" "$COMBINED_DIR/SKILL.md"
          echo -e "    ${GREEN}✓${RESET} ~/.copilot/skills/appsec-codecounsil/SKILL.md  (combined CodeCounsil + appsec-plugins)"
        fi
        ;;
      copilot)
        echo -e "  ${BOLD}GitHub Copilot${RESET}"
        if [[ "$target" == "$HOME" ]]; then
          echo -e "    ${YELLOW}↩${RESET} Global Copilot instructions not applicable — use per-project mode"
        else
          mkdir -p "$target/.github"
          local marker="<!-- codecounsil-adapter -->"
          local dst="$target/.github/copilot-instructions.md"
          if [[ -f "$dst" ]] && grep -q "$marker" "$dst"; then
            if [[ "$force_mode" == "update" || "$force_mode" == "force" ]]; then
              # Remove old CodeCounsil section and re-add updated version
              # Everything between marker and end of file is replaced
              head_content=$(sed "/$marker/,\$d" "$dst")
              printf "%s\n\n%s\n\n" "$head_content" "$marker" > "$dst"
              cat "$REPO_DIR/adapters/github-copilot/copilot-instructions.md" >> "$dst"
              echo -e "    ${GREEN}✓${RESET} .github/copilot-instructions.md  (updated)"
            else
              echo -e "    ${YELLOW}↩${RESET} .github/copilot-instructions.md — already present (use --update to refresh)"
            fi
          elif [[ -f "$dst" ]]; then
            { echo ""; echo "$marker"; echo ""; cat "$REPO_DIR/adapters/github-copilot/copilot-instructions.md"; } >> "$dst"
            echo -e "    ${GREEN}✓${RESET} .github/copilot-instructions.md  (merged)"
          else
            cp "$REPO_DIR/adapters/github-copilot/copilot-instructions.md" "$dst"
            echo -e "    ${GREEN}✓${RESET} .github/copilot-instructions.md"
          fi
        fi
        ;;
      opencode)
        echo -e "  ${BOLD}OpenCode${RESET}"
        if [[ "$target" == "$HOME" ]]; then
          echo -e "    ${YELLOW}↩${RESET} Global AGENTS.md not applicable — use per-project mode"
        else
          local marker="<!-- codecounsil-adapter -->"
          local dst="$target/AGENTS.md"
          if [[ -f "$dst" ]] && grep -q "$marker" "$dst"; then
            if [[ "$force_mode" == "update" || "$force_mode" == "force" ]]; then
              head_content=$(sed "/$marker/,\$d" "$dst")
              printf "%s\n\n%s\n\n" "$head_content" "$marker" > "$dst"
              cat "$REPO_DIR/adapters/opencode/AGENTS.md" >> "$dst"
              echo -e "    ${GREEN}✓${RESET} AGENTS.md  (updated)"
            else
              echo -e "    ${YELLOW}↩${RESET} AGENTS.md — already present (use --update to refresh)"
            fi
          elif [[ -f "$dst" ]]; then
            { echo ""; echo "$marker"; echo ""; cat "$REPO_DIR/adapters/opencode/AGENTS.md"; } >> "$dst"
            echo -e "    ${GREEN}✓${RESET} AGENTS.md  (merged into existing file)"
          else
            cp "$REPO_DIR/adapters/opencode/AGENTS.md" "$dst"
            echo -e "    ${GREEN}✓${RESET} AGENTS.md"
          fi
        fi
        ;;
    esac
  done
}

if [[ "$INSTALL_MODE" == "global" ]]; then
  install_adapters "$HOME" "$PLATFORMS"
else
  install_adapters "$TARGET" "$PLATFORMS"
fi

# ── 6. Summary ─────────────────────────────────────────────

echo ""
if [[ "$MODE" == "update" ]]; then
  echo -e "${GREEN}${BOLD}══════════════════════════════════════════${RESET}"
  echo -e "${GREEN}${BOLD}  ✓ CodeCounsil updated successfully!     ${RESET}"
  echo -e "${GREEN}${BOLD}══════════════════════════════════════════${RESET}"
else
  echo -e "${GREEN}${BOLD}══════════════════════════════════════════${RESET}"
  echo -e "${GREEN}${BOLD}  ✓ CodeCounsil installed successfully!   ${RESET}"
  echo -e "${GREEN}${BOLD}══════════════════════════════════════════${RESET}"
fi
echo ""

if [[ $HAS_CLAUDE      -eq 1 ]]; then
  echo -e "  ${BOLD}Claude Code${RESET}"
  echo -e "  Open the repo in Claude Code and run:"
  echo -e "    ${CYAN}/project-review full${RESET}"
  echo ""
fi
if [[ $HAS_COPILOT_CLI -eq 1 ]]; then
  echo -e "  ${BOLD}GitHub Copilot CLI${RESET}"
  echo -e "  In any repo, just say:"
  echo -e "    ${CYAN}run a full CodeCounsil review${RESET}"
  echo ""
fi
if [[ $HAS_COPILOT  -eq 1 ]]; then
  echo -e "  ${BOLD}GitHub Copilot (VS Code)${RESET}"
  echo -e "  Ask Copilot Chat:"
  echo -e "    ${CYAN}run a full CodeCounsil review${RESET}"
  echo ""
fi
if [[ $HAS_OPENCODE -eq 1 ]]; then
  echo -e "  ${BOLD}OpenCode${RESET}"
  echo -e "  Inside OpenCode ask:"
  echo -e "    ${CYAN}run project-review full${RESET}"
  echo ""
fi

echo -e "  After specialists write findings to ${BOLD}.review/raw/*.json${RESET}:"
echo -e "    ${CYAN}project-review --consolidate-only${RESET}"
echo ""
