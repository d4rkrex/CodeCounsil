from pathlib import Path

from core.config.loader import hash_config, load_config


def test_default_config_loads_with_secure_defaults(tmp_path: Path) -> None:
    config, rejected = load_config(tmp_path)
    assert rejected == {}
    assert config.review.modify_code is False
    assert config.review.output_directory == ".review"
    assert config.specialists.security.enabled is True
    assert config.tools.timeout_seconds == 60


def test_modify_code_and_security_disable_are_rejected_and_logged(malicious_repo: Path) -> None:
    config, rejected = load_config(malicious_repo)
    assert config.review.modify_code is False
    assert config.specialists.security.enabled is True
    assert rejected["review.modify_code"] is True
    assert rejected["specialists.security.enabled"] is False


def test_tool_timeout_above_three_hundred_is_capped(tmp_path: Path) -> None:
    (tmp_path / "codecounsil.yaml").write_text("tools:\n  timeout_seconds: 999\n", encoding="utf-8")
    config, _ = load_config(tmp_path)
    assert config.tools.timeout_seconds == 300


def test_config_hash_is_deterministic(tmp_path: Path) -> None:
    (tmp_path / "codecounsil.yaml").write_text("project:\n  name: demo\n", encoding="utf-8")
    config_one, _ = load_config(tmp_path)
    config_two, _ = load_config(tmp_path)
    assert hash_config(config_one) == hash_config(config_two)
