from pathlib import Path

from core.config.models import CodeCounsilConfig
from core.manifest.manifest import ExecutionManifest
from core.selection.selector import select_specialists


def make_manifest(tmp_path: Path) -> ExecutionManifest:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return ExecutionManifest(workspace=workspace, mode="full", target_repo=tmp_path, config_hash="sha256:test", effective_config={})


def test_full_mode_selects_all_available_domain_specialists_when_tests_present(tmp_path: Path) -> None:
    # CC-QA-001: use set membership checks instead of exact equality
    # so the test doesn't break when new conditional specialists are added
    manifest = make_manifest(tmp_path)
    config = CodeCounsilConfig()
    context = {"tests": {"present": True}}
    selected = select_specialists("full", context, config, manifest)
    # Mandatory specialists always present
    assert "discovery" in selected
    assert "challenger" in selected
    assert "consolidator" in selected
    # Core MVP specialists always present in full mode with tests
    assert "architecture" in selected
    assert "developer" in selected
    assert "qa" in selected
    assert "security" in selected
    assert "data_privacy" in selected
    # v1.1 conditional specialists NOT present without their context signals
    assert "ux" not in selected       # requires frontend.present=True
    assert "sre" not in selected      # requires iac or pipelines
    assert "finops" not in selected   # requires terraform/cloudformation
    assert "product" not in selected  # requires documentation
    assert "ai" not in selected       # requires has_ai_libraries=True


def test_security_mode_selects_only_security_plus_mandatory(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    selected = select_specialists("security", {"tests": {"present": True}}, CodeCounsilConfig(), manifest)
    assert selected == ["security", "discovery", "challenger", "consolidator"]


def test_mandatory_specialists_are_always_present(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    selected = select_specialists("developer", {"tests": {"present": False}}, CodeCounsilConfig(), manifest)
    assert all(name in selected for name in ["discovery", "challenger", "consolidator"])


def test_qa_is_excluded_when_no_tests_are_detected(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    selected = select_specialists("full", {"tests": {"present": False}}, CodeCounsilConfig(), manifest)
    assert "qa" not in selected
    assert any(item["name"] == "qa" for item in manifest.data["specialists_excluded"])


def test_custom_mode_selects_architecture_and_security(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    selected = select_specialists("architecture,security", {"tests": {"present": True}}, CodeCounsilConfig(), manifest)
    assert selected == ["architecture", "security", "discovery", "challenger", "consolidator"]


def test_ux_excluded_when_no_frontend(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    selected = select_specialists("full", {"frontend": {"present": False}}, CodeCounsilConfig(), manifest)
    assert "ux" not in selected


def test_ux_selected_when_frontend_present(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    context = {"frontend": {"present": True}}
    selected = select_specialists("full", context, CodeCounsilConfig(), manifest)
    assert "ux" in selected


def test_sre_excluded_when_no_iac_or_pipelines(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    selected = select_specialists("full", {"iac": [], "pipelines": []}, CodeCounsilConfig(), manifest)
    assert "sre" not in selected


def test_sre_selected_when_iac_present(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    context = {"iac": ["terraform:main.tf"], "pipelines": []}
    selected = select_specialists("full", context, CodeCounsilConfig(), manifest)
    assert "sre" in selected


def test_data_privacy_always_selected_in_full_mode(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    selected = select_specialists("full", {}, CodeCounsilConfig(), manifest)
    assert "data_privacy" in selected
