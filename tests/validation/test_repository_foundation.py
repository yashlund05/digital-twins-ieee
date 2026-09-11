"""
test_repository_foundation.py — Phase 0 Repository Validation Tests

Verifies that the repository foundation conforms to Phase 0 requirements:
1. All YAML configuration files parse cleanly without errors.
2. All src submodules import cleanly.
3. Key documentation and governance files exist and are non-empty.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.validation
def test_yaml_configs_parse() -> None:
    """Verify every YAML config in configs/ parses valid syntax."""
    configs_dir = REPO_ROOT / "configs"
    assert configs_dir.is_dir(), "configs/ directory must exist"

    yaml_files = list(configs_dir.rglob("*.yaml")) + list(configs_dir.rglob("*.yml"))
    assert len(yaml_files) >= 6, f"Expected at least 6 config files, found {len(yaml_files)}"

    for yaml_file in yaml_files:
        with open(yaml_file, encoding="utf-8") as f:
            content = yaml.safe_load(f)
            assert content is not None, f"Config {yaml_file.name} must not be empty"
            assert isinstance(content, dict), f"Config {yaml_file.name} must parse to a dict"


@pytest.mark.validation
def test_governance_files_exist() -> None:
    """Verify all required governance files exist and are non-empty."""
    required_files = [
        "README.md",
        "AGENTS.md",
        "AI_RULES.md",
        "CLAUDE.md",
        "GEMINI.md",
        "CODEX.md",
        "VIBECODING.md",
        "PHASES.md",
        "CONTRIBUTING.md",
        "CODEOWNERS",
        "LICENSE",
        ".gitignore",
        ".env.example",
        "pyproject.toml",
        "Makefile",
    ]
    for rel_path in required_files:
        file_path = REPO_ROOT / rel_path
        assert file_path.is_file(), f"Missing required file: {rel_path}"
        assert file_path.stat().st_size > 0, f"File must not be empty: {rel_path}"


@pytest.mark.validation
def test_documentation_foundation_exists() -> None:
    """Verify all Phase 0 architectural, methodology, and decision docs exist."""
    required_docs = [
        "docs/research/literature-review.md",
        "docs/architecture/SYSTEM_ARCHITECTURE.md",
        "docs/architecture/SYNCHRONIZATION_ENGINE.md",
        "docs/architecture/TESTING_STRATEGY.md",
        "docs/methodology/DATA_PROTOCOL.md",
        "docs/methodology/REPRODUCIBILITY.md",
        "docs/methodology/STATISTICAL_PROTOCOL.md",
        "docs/decisions/ADR-0001-research-positioning.md",
        "docs/decisions/ADR-0002-platform-selection.md",
        "docs/onboarding/TEAM_ROLES.md",
        "docs/paper/PAPER_ALIGNMENT.md",
        "docs/paper/FIGURE_TABLE_STANDARD.md",
        "docs/experiments/EXPERIMENTS.md",
        "docs/experiments/EXPERIMENT_MATRIX.md",
    ]
    for rel_path in required_docs:
        doc_path = REPO_ROOT / rel_path
        assert doc_path.is_file(), f"Missing required doc: {rel_path}"
        assert doc_path.stat().st_size > 50, f"Doc too short or empty: {rel_path}"


@pytest.mark.validation
def test_github_templates_exist() -> None:
    """Verify GitHub issue and pull request templates exist."""
    required_templates = [
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/ISSUE_TEMPLATE/experiment_request.md",
        ".github/ISSUE_TEMPLATE/research_question.md",
        ".github/ISSUE_TEMPLATE/methodology_change.md",
        ".github/pull_request_template.md",
    ]
    for rel_path in required_templates:
        template_path = REPO_ROOT / rel_path
        assert template_path.is_file(), f"Missing template: {rel_path}"
        assert template_path.stat().st_size > 50, f"Template too short: {rel_path}"


@pytest.mark.validation
def test_src_modules_importable() -> None:
    """Verify all src modules can be cleanly imported."""
    import src.anomaly_detection
    import src.cli
    import src.data
    import src.digital_twin
    import src.evaluation
    import src.experiments
    import src.forecasting
    import src.residuals
    import src.statistics
    import src.synchronization
    import src.utils
    import src.visualization

    assert src.__version__ == "0.1.0"
