import shutil
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def simple_api_repo(tmp_path: Path, fixtures_dir: Path) -> Path:
    destination = tmp_path / "simple-python-api"
    shutil.copytree(fixtures_dir / "simple-python-api", destination)
    return destination


@pytest.fixture
def malicious_repo(tmp_path: Path, fixtures_dir: Path) -> Path:
    destination = tmp_path / "malicious-repo"
    shutil.copytree(fixtures_dir / "malicious-repo", destination, dirs_exist_ok=True)
    return destination
