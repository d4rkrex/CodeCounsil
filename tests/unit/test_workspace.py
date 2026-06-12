from pathlib import Path

import pytest

from core.output.workspace import SecurityError, create_safe_workspace, safe_write


def test_normal_review_dir_is_created_successfully(tmp_path: Path) -> None:
    workspace = create_safe_workspace(tmp_path)
    assert workspace.exists()
    assert (workspace / "raw").exists()
    assert (workspace / "tools").exists()


def test_symlink_at_review_path_raises_security_error(tmp_path: Path) -> None:
    # T-003: .review/ itself being a symlink is blocked
    target = tmp_path / "outside"
    target.mkdir()
    (tmp_path / ".review").symlink_to(target, target_is_directory=True)
    with pytest.raises(SecurityError):
        create_safe_workspace(tmp_path)


def test_symlink_inside_existing_review_dir_is_safely_replaced(tmp_path: Path) -> None:
    # T-003: A symlink INSIDE an existing .review is safely removed when
    # the workspace is recreated fresh. The actual write-time protection
    # is O_NOFOLLOW in safe_write (tested below).
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    target = tmp_path / "outside.txt"
    target.write_text("outside", encoding="utf-8")
    (review_dir / "poison.txt").symlink_to(target)
    # Should NOT raise — it deletes the old .review and creates a fresh one
    workspace = create_safe_workspace(tmp_path)
    assert workspace.exists()
    assert not (workspace / "poison.txt").exists()
    assert target.read_text() == "outside"  # outside file was NOT deleted


def test_safe_write_to_symlink_raises_security_error(tmp_path: Path) -> None:
    # T-003: safe_write refuses to follow a symlink via O_NOFOLLOW
    workspace = create_safe_workspace(tmp_path)
    target = tmp_path / "real_file.txt"
    target.write_text("real", encoding="utf-8")
    # Manually place a symlink inside the workspace (simulate attacker pre-planting)
    link = workspace / "malicious.md"
    link.symlink_to(target)
    with pytest.raises(SecurityError):
        safe_write(workspace, "malicious.md", "overwritten")
    assert target.read_text() == "real"  # real file was NOT modified


def test_path_traversal_in_output_directory_raises_security_error(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        create_safe_workspace(tmp_path, "../escape")


def test_fresh_workspace_is_empty_except_framework_directories(tmp_path: Path) -> None:
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    (review_dir / "poison.txt").write_text("poison", encoding="utf-8")
    workspace = create_safe_workspace(tmp_path)
    assert sorted(path.name for path in workspace.iterdir()) == ["raw", "tools"]
