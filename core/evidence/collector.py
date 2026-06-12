# VT-Spec T-008: subprocess execution with allowlist, no shell=True
# VT-Spec T-007: timeout and output size limits
# VT-Spec T-005: strip control sequences from tool output

import json
import re
import shutil
import subprocess
from pathlib import Path

from ..output.workspace import safe_write

MAX_OUTPUT_BYTES = 51_200
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# VT-Spec T-008: allowlisted passive tools only. Run inside a Docker sandbox in production.
TOOL_ALLOWLIST = {
    "ruff": ["ruff", "check", ".", "--output-format", "json"],
    "flake8": ["flake8", ".", "--max-line-length=120"],
    "bandit": ["bandit", "-r", ".", "-f", "json"],
    "semgrep": ["semgrep", "scan", "--json", "--quiet", "."],
    "pip-audit": ["pip-audit", "--format", "json"],
    "trivy": ["trivy", "fs", "--format", "json", "--quiet", "."],
    "checkov": ["checkov", "-d", ".", "--output", "json", "--quiet"],
}


def collect_evidence(repo_path: Path, tools_config, manifest_stage: dict, manifest, workspace: Path) -> dict:
    results: dict[str, dict] = {}
    safe_write(workspace, "tools/results.json", "{}")

    for tool_name, base_cmd in TOOL_ALLOWLIST.items():
        binary = shutil.which(base_cmd[0])
        result = {
            "tool": tool_name,
            "detected": binary is not None,
            "executed": False,
            "command": None,
            "exit_code": None,
            "summary": None,
            "result_path": None,
            "errors": None,
            "version": None,
        }

        if not binary:
            manifest.log_tool_result(manifest_stage, result)
            results[tool_name] = result
            continue

        result["version"] = _detect_version(binary)
        if not tools_config.allow_execution:
            result["errors"] = "Tool execution disabled by config"
            manifest.log_tool_result(manifest_stage, result)
            results[tool_name] = result
            continue

        cmd = [binary] + base_cmd[1:]
        result["command"] = cmd
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(repo_path),
                capture_output=True,
                timeout=tools_config.timeout_seconds,
                shell=False,
                check=False,
            )
            output = _sanitize_output(proc.stdout + (b"\n" + proc.stderr if proc.stderr else b""))
            output = _truncate_output(output)
            result["executed"] = True
            result["exit_code"] = proc.returncode
            result["summary"] = output[:2000] if output else "(no output)"
            result["result_path"] = f"tools/{tool_name}.txt"
            safe_write(workspace, result["result_path"], output)
            manifest.log_command(manifest_stage, cmd, proc.returncode, f"{tool_name}: exit {proc.returncode}")
        except subprocess.TimeoutExpired:
            result["errors"] = f"T-007: Tool timed out after {tools_config.timeout_seconds}s"
        except Exception as exc:
            result["errors"] = f"Execution error: {exc}"

        manifest.log_tool_result(manifest_stage, result)
        results[tool_name] = result

    safe_write(workspace, "tools/results.json", json.dumps(results, indent=2))
    return results


def _sanitize_output(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = ANSI_ESCAPE.sub("", text)
    text = CONTROL_CHARS.sub("", text)
    return text.strip()


def _truncate_output(text: str) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= MAX_OUTPUT_BYTES:
        return text
    truncated = encoded[:MAX_OUTPUT_BYTES].decode("utf-8", errors="ignore")
    return truncated.rstrip() + "\n[TRUNCATED: T-007 output limit]"


def _detect_version(binary: str) -> str | None:
    for args in ([binary, "--version"], [binary, "-V"]):
        try:
            proc = subprocess.run(args, capture_output=True, timeout=5, shell=False, check=False)
        except Exception:
            continue
        output = _sanitize_output(proc.stdout + (b"\n" + proc.stderr if proc.stderr else b""))
        if output:
            return output.splitlines()[0][:200]
    return None
