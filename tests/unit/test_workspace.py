from pathlib import Path

import pytest

from core.output.workspace import SecurityError, create_safe_workspace


def test_normal_review_dir_is_created_successfully(tmp_path: Path) -> None:
    workspace = create_safe_workspace(tmp_path)
    assert workspace.exists()
    assert (workspace / "raw").exists()
    assert (workspace / "tools").exists()


def test_symlink_at_review_path_raises_security_error(tmp_path: Path) -> None:
    target = tmp_path / "outside"
    target.mkdir()
    (tmp_path / ".review").symlink_to(target, target_is_directory=True)
    with pytest.raises(SecurityError):
        create_safe_workspace(tmp_path)


def test_symlink_inside_existing_review_dir_raises_security_error(tmp_path: Path) -> None:
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    target = tmp_path / "outside.txt"
    target.write_text("outside", encoding="utf-8")
    (review_dir / "poison.txt").symlink_to(target)
    with pytest.raises(SecurityError):
        create_safe_workspace(tmp_path)


def test_path_traversal_in_output_directory_raises_security_error(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        create_safe_workspace(tmp_path, "../escape")


def test_fresh_workspace_is_empty_except_framework_directories(tmp_path: Path) -> None:
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    (review_dir / "poison.txt").write_text("poison", encoding="utf-8")
    workspace = create_safe_workspace(tmp_path)
    assert sorted(path.name for path in workspace.iterdir()) == ["raw", "tools"]
