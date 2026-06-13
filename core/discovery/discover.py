from __future__ import annotations

# VT-Spec T-007: file size, count, and symlink depth limits
# VT-Spec T-001: discovery output is framework-generated, not repo content

import os
import re
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
AI_LIBRARY_INDICATORS = {
    "openai": ("openai",),
    "anthropic": ("anthropic",),
    "langchain": ("langchain",),
    "langgraph": ("langgraph",),
    "llama_index": ("llama_index", "llama-index"),
    "transformers": ("transformers",),
    "torch": ("import torch", "torch.", '"torch"', "'torch'"),
    "tensorflow": ("tensorflow", "tf.keras"),
    "sklearn": ("sklearn", "scikit-learn"),
}
AI_SIGNAL_SUFFIXES = {".py", ".ipynb", ".js", ".jsx", ".ts", ".tsx", ".toml", ".txt", ".json", ".yaml", ".yml"}

ENTRYPOINT_NAMES = {"app.py", "main.py", "server.py", "manage.py", "index.js", "main.ts"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".toml", ".ini", ".json", ".env"}
COMPOSE_FILE_NAMES = {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}
VERSIONED_SQL_RE = re.compile(r"^V[^/]+\.sql$", re.IGNORECASE)


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
        "has_ai_libraries": False,
        "ai_libraries": [],
        "auth_mechanisms": [],
        "database_signals": {
            "migration_tool": "unknown",
            "connection_pooling": "unknown",
            "dev_prod_mismatch": False,
            "migration_tool_files": [],
            "has_manual_migrations": False,
            "has_no_pooling": False,
        },
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
    ai_libraries: set[str] = set()
    database_signal_observations = _init_database_signal_observations()

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
            _classify_content(
                rel_file,
                content,
                frameworks,
                entrypoints,
                apis,
                databases,
                services,
                auth,
                test_frameworks,
                frontend_frameworks,
                ai_libraries,
                context,
            )
            _collect_database_signals(rel_file, content, database_signal_observations)

        if context["truncated"]:
            break

    if "fastapi" in frameworks or apis:
        context["app_type"] = "api"
    elif frontend_frameworks:
        context["app_type"] = "frontend"
    elif any(name.endswith(".tf") or name.startswith("terraform:") for name in iac):
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
    context["has_ai_libraries"] = bool(ai_libraries)
    context["ai_libraries"] = sorted(ai_libraries)
    context["auth_mechanisms"] = sorted(auth)
    context["config_files"] = sorted(configs)[:100]
    context["dependency_managers"] = sorted(dependency_managers)
    context["file_count"] = file_count
    context["total_size_bytes"] = total_size
    context["tests"]["frameworks"] = sorted(test_frameworks)
    context["tests"]["locations"] = sorted(test_locations)
    context["frontend"]["present"] = bool(frontend_frameworks)
    context["frontend"]["frameworks"] = sorted(frontend_frameworks)
    context["database_signals"] = _finalize_database_signals(databases, database_signal_observations)
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

    if name in {"readme.md", "architecture.md", "adr.md", "contributing.md", "proyect.md"} or rel_file.parts[:1] == ("docs",):
        docs.add(rel_text)
    if name in {"requirements.txt", "pyproject.toml", "setup.py", "package.json", "go.mod", "cargo.toml", "gemfile", "pom.xml"}:
        dependency_managers.add(rel_text)
    if name in {"dockerfile", "docker-compose.yml", "docker-compose.yaml", "nginx.conf", ".env.example", "codecounsil.yaml"} or rel_file.suffix.lower() in CONFIG_SUFFIXES:
        configs.add(rel_text)
    if rel_file.suffix.lower() == ".tf":
        iac.add(f"terraform:{rel_text}")
    elif name in {"template.yaml", "cloudformation.yaml", "template.yml", "cloudformation.yml"} or "cloudformation" in rel_text.lower():
        iac.add(f"cloudformation:{rel_text}")
    elif "terraform" in rel_text.lower():
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
    ai_libraries: set[str],
    context: dict,
) -> None:
    lower = content.lower()
    rel_text = str(rel_file)

    # CC-ARCH-001 / CC-SEC-001: Restrict all content-based detection to source
    # code files. Documentation (.md, .txt, .rst, .adoc) and config files that
    # mention framework names (e.g. checklists, agent prompts) must not trigger
    # framework, database, auth, or any other detection.
    is_source = rel_file.suffix.lower() not in {".md", ".txt", ".rst", ".adoc"}

    if is_source:
        for framework, indicators in FRAMEWORK_INDICATORS.items():
            if any(indicator.lower() in lower for indicator in indicators):
                frameworks.add(framework)
        if rel_file.name in ENTRYPOINT_NAMES or 'if __name__ == "__main__"' in content or "FastAPI(" in content:
            entrypoints.add(rel_text)
        if "@app.get" in lower or "@router.get" in lower or "route(" in lower or "fastapi(" in lower:
            apis.add(rel_text)
        for engine in _detect_database_engines(lower):
            databases.add(engine)
        if "sqlalchemy" in lower:
            databases.add("sqlalchemy")
        if "requests." in lower or "httpx." in lower or "boto3" in lower or "stripe" in lower:
            services.add(rel_text)
        if any(token in lower for token in ("auth", "oauth", "jwt", "bearer", "session")):
            auth.update({token for token in ("jwt", "oauth", "session") if token in lower})
        if "react" in lower or rel_file.suffix.lower() in {".tsx", ".jsx"}:
            frontend_frameworks.add("react")
        if "vue" in lower:
            frontend_frameworks.add("vue")
        if "angular" in lower:
            frontend_frameworks.add("angular")

    if "pytest" in lower:
        context["tests"]["present"] = True
        test_frameworks.add("pytest")
    if "unittest" in lower:
        context["tests"]["present"] = True
        test_frameworks.add("unittest")

    # CC-DEV-001: Restrict AI detection to true source code suffixes only.
    # .yaml/.yml/.txt/.json include tool outputs, checklists, and config files
    # that mention AI library names without the project actually using them.
    _AI_SOURCE_SUFFIXES = {".py", ".ipynb", ".js", ".jsx", ".ts", ".tsx"}
    if rel_file.suffix.lower() in _AI_SOURCE_SUFFIXES or rel_file.name.lower() in {"requirements.txt", "pyproject.toml", "package.json"}:
        for library, indicators in AI_LIBRARY_INDICATORS.items():
            if any(indicator in lower for indicator in indicators):
                ai_libraries.add(library)


def _init_database_signal_observations() -> dict:
    return {
        "migration_tools": {
            "alembic": set(),
            "flyway": set(),
            "liquibase": set(),
            "flyway-style": set(),
        },
        "connection_pooling": {
            "pgbouncer": set(),
            "pgpool": set(),
            "sqlalchemy_pool": set(),
        },
        "all_databases": set(),
        "compose_databases": set(),
        "non_compose_databases": set(),
    }


def _collect_database_signals(rel_file: Path, content: str, observations: dict) -> None:
    lower = content.lower()
    rel_text = str(rel_file)

    if rel_file.name == "alembic.ini" or rel_text.endswith("migrations/env.py"):
        observations["migration_tools"]["alembic"].add(rel_text)
    if rel_file.name == "flyway.conf" or (rel_file.parts[:2] == ("db", "migration") and rel_file.suffix.lower() == ".sql"):
        observations["migration_tools"]["flyway"].add(rel_text)
    if rel_file.name == "liquibase.properties":
        observations["migration_tools"]["liquibase"].add(rel_text)
    if rel_file.suffix.lower() == ".sql" and VERSIONED_SQL_RE.match(rel_file.name) and rel_file.parts[:1] and rel_file.parts[0] in {"db", "migrations"}:
        observations["migration_tools"]["flyway-style"].add(rel_text)

    if rel_file.name == "pgbouncer.ini" or (
        "pgbouncer" in lower and (rel_file.name in COMPOSE_FILE_NAMES or rel_file.suffix.lower() in CONFIG_SUFFIXES)
    ):
        observations["connection_pooling"]["pgbouncer"].add(rel_text)
    if rel_file.name == "pgpool.conf" or "PGPOOL" in content or "pgpool" in lower:
        observations["connection_pooling"]["pgpool"].add(rel_text)
    if ("pool_size" in lower or "max_overflow" in lower) and ("sqlalchemy" in lower or "create_engine(" in lower):
        observations["connection_pooling"]["sqlalchemy_pool"].add(rel_text)

    detected_engines = _detect_database_engines(lower)
    if not detected_engines:
        return

    observations["all_databases"].update(detected_engines)
    if rel_file.name.lower() in COMPOSE_FILE_NAMES:
        observations["compose_databases"].update(detected_engines)
    else:
        observations["non_compose_databases"].update(detected_engines)


def _detect_database_engines(lower: str) -> set[str]:
    engines: set[str] = set()
    if "sqlite:///" in lower or "sqlite+" in lower or "import sqlite3" in lower:
        engines.add("sqlite")
    if any(token in lower for token in ("postgres://", "postgresql://", "postgres:", "postgres ", "postgres\n", "asyncpg", "psycopg")):
        engines.add("postgres")
    if any(token in lower for token in ("mysql://", "mysql+", "mysql:", "pymysql", "mysqldb", "mysql.connector")):
        engines.add("mysql")
    if "mariadb://" in lower or "mariadb:" in lower:
        engines.add("mariadb")
    return engines


def _finalize_database_signals(databases: set[str], observations: dict) -> dict:
    database_names = {name for name in databases if name != "sqlalchemy"}
    detected_databases = database_names | observations["all_databases"]

    migration_tool = "unknown"
    migration_tool_files: list[str] = []
    for tool_name in ("alembic", "flyway", "liquibase", "flyway-style"):
        files = observations["migration_tools"][tool_name]
        if files:
            migration_tool = "flyway" if tool_name == "flyway-style" else tool_name
            migration_tool_files = sorted(files)
            break

    has_manual_migrations = False
    if detected_databases and migration_tool == "unknown":
        migration_tool = "manual"
        has_manual_migrations = True

    connection_pooling = "unknown"
    has_no_pooling = False
    for tool_name in ("pgbouncer", "pgpool", "sqlalchemy_pool"):
        files = observations["connection_pooling"][tool_name]
        if files:
            connection_pooling = tool_name
            break
    if detected_databases and connection_pooling == "unknown":
        connection_pooling = "none"
        has_no_pooling = True

    dev_prod_mismatch = (
        "sqlite" in detected_databases and bool({"postgres", "mysql", "mariadb"} & detected_databases)
    ) or (
        bool(observations["compose_databases"])
        and bool(observations["non_compose_databases"])
        and observations["compose_databases"] != observations["non_compose_databases"]
    )

    return {
        "migration_tool": migration_tool,
        "connection_pooling": connection_pooling,
        "dev_prod_mismatch": dev_prod_mismatch,
        "migration_tool_files": migration_tool_files,
        "has_manual_migrations": has_manual_migrations,
        "has_no_pooling": has_no_pooling,
    }


def _read_snippet(file_path: Path) -> str:
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.read(MAX_SNIPPET_BYTES)
    except OSError:
        return ""
