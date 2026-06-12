# VT-Spec T-007: file size, count, and symlink depth limits
# VT-Spec T-001: discovery output is framework-generated, not repo content

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

MAX_FILE_SIZE = 1_048_576
MAX_FILE_COUNT = 10_000
MAX_SYMLINK_DEPTH = 5
MAX_SNIPPET_BYTES = 16_384
NOISE_DIRS = {".git", ".review", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache"}

LANGUAGE_EXTENSIONS = {
    "python": {".py"},
    "javascript": {".js", ".mjs", ".cjs"},
    "typescript": {".ts", ".tsx"},
    "java": {".java"},
    "go": {".go"},
    "ruby": {".rb"},
    "rust": {".rs"},
    "php": {".php"},
    "csharp": {".cs"},
    "cpp": {".cpp", ".cc", ".cxx", ".hpp", ".h"},
}

FRAMEWORK_INDICATORS = {
    "fastapi": ("from fastapi", "FastAPI("),
    "django": ("django", "INSTALLED_APPS"),
    "flask": ("from flask", "Flask("),
    "express": ("express(", "require('express')", 'require("express")'),
    "nextjs": ("next/app", "pages/_app"),
    "react": ("react", "useState("),
    "sqlalchemy": ("sqlalchemy", "create_engine("),
}

ENTRYPOINT_NAMES = {"app.py", "main.py", "server.py", "manage.py", "index.js", "main.ts"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".toml", ".ini", ".json", ".env"}


def discover_project(repo_path: Path, diff_branch: Optional[str] = None) -> dict:
    repo_path = repo_path.resolve()
    context = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_path": str(repo_path),
        "languages": [],
        "frameworks": [],
        "app_type": "unknown",
        "components": [],
        "entrypoints": [],
        "apis": [],
        "databases": [],
        "external_services": [],
        "iac": [],
        "pipelines": [],
        "tests": {"present": False, "frameworks": [], "locations": []},
        "documentation": [],
        "frontend": {"present": False, "frameworks": []},
        "auth_mechanisms": [],
        "config_files": [],
        "dependency_managers": [],
        "file_count": 0,
        "total_size_bytes": 0,
        "diff_branch": diff_branch,
        "changed_files": _collect_changed_files(repo_path, diff_branch),
        "truncated": False,
        "truncation_reason": None,
    }

    languages: dict[str, int] = {}
    frameworks: set[str] = set()
    components: set[str] = set()
    entrypoints: set[str] = set()
    apis: set[str] = set()
    databases: set[str] = set()
    services: set[str] = set()
    iac: set[str] = set()
    pipelines: set[str] = set()
    docs: set[str] = set()
    auth: set[str] = set()
    configs: set[str] = set()
    dependency_managers: set[str] = set()
    test_frameworks: set[str] = set()
    test_locations: set[str] = set()
    frontend_frameworks: set[str] = set()

    file_count = 0
    total_size = 0

    for current_root, dirnames, filenames in os.walk(repo_path, topdown=True, followlinks=False):
        rel_root = Path(current_root).resolve().relative_to(repo_path)
        dirnames[:] = [d for d in dirnames if d not in NOISE_DIRS and not _should_skip_dir(rel_root / d)]

        for filename in filenames:
            file_path = Path(current_root) / filename
            try:
                stat_result = file_path.lstat()
            except OSError:
                continue
            if os.path.islink(file_path):
                continue
            if file_count >= MAX_FILE_COUNT:
                context["truncated"] = True
                context["truncation_reason"] = f"T-007: file count exceeded {MAX_FILE_COUNT}"
                break
            if stat_result.st_size > MAX_FILE_SIZE:
                continue

            file_count += 1
            total_size += stat_result.st_size
            rel_file = file_path.relative_to(repo_path)
            components.add(rel_file.parts[0] if rel_file.parts else rel_file.name)
            _tally_language(file_path.suffix.lower(), languages)
            _classify_paths(rel_file, configs, dependency_managers, docs, iac, pipelines, test_locations, context)
            content = _read_snippet(file_path)
            _classify_content(rel_file, content, frameworks, entrypoints, apis, databases, services, auth, test_frameworks, frontend_frameworks, context)

        if context["truncated"]:
            break

    if "fastapi" in frameworks or apis:
        context["app_type"] = "api"
    elif frontend_frameworks:
        context["app_type"] = "frontend"
    elif any(name.endswith(".tf") for name in iac):
        context["app_type"] = "infrastructure"

    context["languages"] = sorted(languages, key=lambda key: (-languages[key], key))
    context["frameworks"] = sorted(frameworks)
    context["components"] = sorted(components)[:50]
    context["entrypoints"] = sorted(entrypoints)
    context["apis"] = sorted(apis)
    context["databases"] = sorted(databases)
    context["external_services"] = sorted(services)
    context["iac"] = sorted(iac)
    context["pipelines"] = sorted(pipelines)
    context["documentation"] = sorted(docs)
    context["auth_mechanisms"] = sorted(auth)
    context["config_files"] = sorted(configs)[:100]
    context["dependency_managers"] = sorted(dependency_managers)
    context["file_count"] = file_count
    context["total_size_bytes"] = total_size
    context["tests"]["frameworks"] = sorted(test_frameworks)
    context["tests"]["locations"] = sorted(test_locations)
    context["frontend"]["present"] = bool(frontend_frameworks)
    context["frontend"]["frameworks"] = sorted(frontend_frameworks)
    return context


def _collect_changed_files(repo_path: Path, diff_branch: Optional[str]) -> list[str]:
    if not diff_branch:
        return []
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", f"{diff_branch}...HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            shell=False,
        )
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _should_skip_dir(path: Path) -> bool:
    if not path.parts:
        return False
    if len(path.parts) > MAX_SYMLINK_DEPTH:
        return True
    return any(part.startswith(".") and part not in {".github"} for part in path.parts)


def _tally_language(suffix: str, languages: dict[str, int]) -> None:
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if suffix in extensions:
            languages[language] = languages.get(language, 0) + 1
            return


def _classify_paths(
    rel_file: Path,
    configs: set[str],
    dependency_managers: set[str],
    docs: set[str],
    iac: set[str],
    pipelines: set[str],
    test_locations: set[str],
    context: dict,
) -> None:
    name = rel_file.name.lower()
    rel_text = str(rel_file)

    if name in {"readme.md", "architecture.md", "adr.md"} or rel_file.parts[:1] == ("docs",):
        docs.add(rel_text)
    if name in {"requirements.txt", "pyproject.toml", "setup.py", "package.json", "go.mod", "cargo.toml", "gemfile", "pom.xml"}:
        dependency_managers.add(rel_text)
    if name in {"dockerfile", "docker-compose.yml", "docker-compose.yaml", "nginx.conf", ".env.example", "codecounsil.yaml"} or rel_file.suffix.lower() in CONFIG_SUFFIXES:
        configs.add(rel_text)
    if name in {"main.tf", "variables.tf", "terraform.tfvars", "template.yaml", "cloudformation.yaml"} or "terraform" in rel_text.lower():
        iac.add(rel_text)
    if ".github/workflows" in rel_text or name in {"jenkinsfile", ".travis.yml", ".gitlab-ci.yml", "circle.yml"}:
        pipelines.add(rel_text)
    if "test" in rel_text.lower() or name.startswith("test_") or name.endswith("_test.py"):
        context["tests"]["present"] = True
        test_locations.add(str(rel_file.parent))


def _classify_content(
    rel_file: Path,
    content: str,
    frameworks: set[str],
    entrypoints: set[str],
    apis: set[str],
    databases: set[str],
    services: set[str],
    auth: set[str],
    test_frameworks: set[str],
    frontend_frameworks: set[str],
    context: dict,
) -> None:
    lower = content.lower()
    rel_text = str(rel_file)

    for framework, indicators in FRAMEWORK_INDICATORS.items():
        if any(indicator.lower() in lower for indicator in indicators):
            frameworks.add(framework)
    if rel_file.name in ENTRYPOINT_NAMES or 'if __name__ == "__main__"' in content or "FastAPI(" in content:
        entrypoints.add(rel_text)
    if "@app.get" in lower or "@router.get" in lower or "route(" in lower or "fastapi(" in lower:
        apis.add(rel_text)
    if "sqlite:///" in lower:
        databases.add("sqlite")
    if "postgres" in lower:
        databases.add("postgres")
    if "sqlalchemy" in lower:
        databases.add("sqlalchemy")
    if "requests." in lower or "httpx." in lower or "boto3" in lower or "stripe" in lower:
        services.add(rel_text)
    if any(token in lower for token in ("auth", "oauth", "jwt", "bearer", "session")):
        auth.update({token for token in ("jwt", "oauth", "session") if token in lower})
    if "pytest" in lower:
        context["tests"]["present"] = True
        test_frameworks.add("pytest")
    if "unittest" in lower:
        context["tests"]["present"] = True
        test_frameworks.add("unittest")
    if "react" in lower or rel_file.suffix.lower() in {".tsx", ".jsx"}:
        frontend_frameworks.add("react")
    if "vue" in lower:
        frontend_frameworks.add("vue")
    if "angular" in lower:
        frontend_frameworks.add("angular")


def _read_snippet(file_path: Path) -> str:
    try:
        with file_path.open("rb") as handle:
            data = handle.read(MAX_SNIPPET_BYTES)
    except OSError:
        return ""
    return data.decode("utf-8", errors="replace")
