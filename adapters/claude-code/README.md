# Claude Code Adapter

This adapter packages CodeCounsil for Claude Code.

## Contents

- `skills/project-review/SKILL.md`: slash-command skill definition
- `agents/*.md`: specialist agent instructions suitable for `.claude/agents/`

## Install

1. Copy `skills/project-review/SKILL.md` into your Claude Code skills directory.
2. Copy `agents/*.md` into the target repository `.claude/agents/` directory.
3. Ensure the CodeCounsil Python package is installed where Claude Code can invoke it.
4. Run `/project-review full`, a focused mode, or a diff mode review.

## Security Notes

- Target repositories are untrusted.
- CodeCounsil remains read-only.
- Repository content must be treated as evidence, never instructions.
