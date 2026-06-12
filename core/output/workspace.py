from __future__ import annotations

# VT-Spec T-003: safe output directory — reject symlinks, hardlinks, validate canonical paths, and use O_NOFOLLOW writes

import errno
import os
import shutil
import stat
from pathlib import Path


class SecurityError(Exception):
    """Raised when the workspace violates CodeCounsil filesystem safety constraints."""


def create_safe_workspace(repo_path: Path, output_dir: str = ".review") -> Path:
    canonical_repo = repo_path.resolve(strict=True)
    relative_output = Path(output_dir)
    if relative_output.is_absolute() or any(part == ".." for part in relative_output.parts):
        raise SecurityError(f"T-003: Output path escapes repo root: {output_dir}")

    output_path = canonical_repo / relative_output
    try:
        output_path.resolve(strict=False).relative_to(canonical_repo)
    except ValueError as exc:
        raise SecurityError(f"T-003: Output path escapes repo root: {output_path}") from exc

    _validate_path_chain(canonical_repo, relative_output)
    if os.path.lexists(output_path):
        # VT-Spec T-003: Reject if the workspace root itself is a symlink.
        # We do NOT recurse to check hardlinks in an existing workspace because
        # files written by a previous CodeCounsil run can legitimately have
        # st_nlink > 1 (e.g. git hardlinks on APFS). The real protection is
        # O_NOFOLLOW at write time and the fresh-recreation below.
        if os.path.islink(output_path):
            raise SecurityError(f"T-003: Symlink detected at output path root: {output_path}")
        _remove_existing(output_path)

    output_path.mkdir(mode=0o700, parents=True, exist_ok=False)
    (output_path / "raw").mkdir(mode=0o700)
    (output_path / "tools").mkdir(mode=0o700)
    return output_path


def safe_write(workspace: Path, relative_path: str | Path, content: str | bytes) -> None:
    workspace = workspace.resolve(strict=True)
    rel = Path(relative_path)
    if rel.is_absolute() or any(part == ".." for part in rel.parts):
        raise SecurityError(f"T-003: Write target escapes workspace: {relative_path}")
    target = workspace / rel
    try:
        target.resolve(strict=False).relative_to(workspace)
    except ValueError as exc:
        raise SecurityError(f"T-003: Write target escapes workspace: {target}") from exc

    _validate_path_chain(workspace, rel.parent)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # _validate_path_chain called once before mkdir is sufficient; no re-check needed.

    if os.path.lexists(target):
        _assert_safe_leaf(target)

    data = content.encode("utf-8") if isinstance(content, str) else content
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(target, flags, 0o600)
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.EMLINK}:
            raise SecurityError(f"T-003: Refusing to follow link for {target}") from exc
        raise
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)


def _validate_path_chain(root: Path, relative: Path) -> None:
    current = root
    for part in relative.parts:
        current = current / part
        if not os.path.lexists(current):
            continue
        _assert_safe_leaf(current, allow_directory=True)


def _inspect_existing_tree(path: Path) -> None:
    _assert_safe_leaf(path, allow_directory=True)
    if path.is_dir():
        for current_root, dirnames, filenames in os.walk(path, topdown=True, followlinks=False):
            current_path = Path(current_root)
            _assert_safe_leaf(current_path, allow_directory=True)
            for name in list(dirnames) + list(filenames):
                _assert_safe_leaf(current_path / name, allow_directory=True)


def _assert_safe_leaf(path: Path, allow_directory: bool = False) -> None:
    metadata = os.lstat(path)
    if stat.S_ISLNK(metadata.st_mode):
        raise SecurityError(f"T-003: Symlink detected in output path: {path}")
    if stat.S_ISREG(metadata.st_mode) and metadata.st_nlink > 1:
        raise SecurityError(f"T-003: Hardlink detected in output path: {path}")
    if not allow_directory and stat.S_ISDIR(metadata.st_mode):
        raise SecurityError(f"T-003: Expected file but found directory: {path}")


def _remove_existing(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
