"""Tests for Plone standards and plone.meta compliance."""
import xml.etree.ElementTree as ET

import pytest

from helpers import assert_file_exists, read_toml, run_copier


class TestRuffConfiguration:
    """Verify generated ruff config follows Plone standards."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        """Create addon for testing."""
        pkg_dir = temp_dir / "mypackage"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.mypackage"},
        )
        return pkg_dir

    def test_ruff_has_extended_lint_rules(self, addon_dir):
        """Generated pyproject.toml has extended ruff lint rules."""
        data = read_toml(addon_dir / "pyproject.toml")
        ruff_select = data["tool"]["ruff"]["lint"]["select"]
        for rule in ["E", "F", "I", "W", "C90", "B", "S", "UP", "SIM", "PGH"]:
            assert rule in ruff_select, f"Missing ruff rule: {rule}"

    def test_ruff_has_line_length_100(self, addon_dir):
        """Generated pyproject.toml uses line-length 100."""
        data = read_toml(addon_dir / "pyproject.toml")
        assert data["tool"]["ruff"]["line-length"] == 100

    def test_ruff_has_test_ignores(self, addon_dir):
        """Generated pyproject.toml ignores S101 in tests."""
        data = read_toml(addon_dir / "pyproject.toml")
        per_file = data["tool"]["ruff"]["lint"]["per-file-ignores"]
        assert "S101" in per_file["tests/**"]

    def test_ruff_has_isort_config(self, addon_dir):
        """Generated pyproject.toml has isort known-first-party."""
        data = read_toml(addon_dir / "pyproject.toml")
        isort = data["tool"]["ruff"]["lint"]["isort"]
        assert "collective" in isort["known-first-party"]


class TestEditorConfig:
    """Verify .editorconfig is present and correct."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        """Create addon for testing."""
        pkg_dir = temp_dir / "mypackage"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.mypackage"},
        )
        return pkg_dir

    def test_editorconfig_exists(self, addon_dir):
        """Backend addon generates .editorconfig."""
        assert_file_exists(addon_dir / ".editorconfig")

    def test_editorconfig_has_python_indent(self, addon_dir):
        """Editorconfig sets Python indent to 4."""
        assert_file_exists(
            addon_dir / ".editorconfig",
            content_contains="indent_size = 4",
        )

    def test_editorconfig_has_xml_indent(self, addon_dir):
        """Editorconfig sets XML/ZCML indent to 2."""
        content = (addon_dir / ".editorconfig").read_text()
        assert "*.{xml,zcml" in content
        assert "indent_size = 2" in content


class TestPreCommitConfig:
    """Verify .pre-commit-config.yaml is present and correct."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        """Create addon for testing."""
        pkg_dir = temp_dir / "mypackage"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.mypackage"},
        )
        return pkg_dir

    def test_pre_commit_config_exists(self, addon_dir):
        """Backend addon generates .pre-commit-config.yaml."""
        assert_file_exists(addon_dir / ".pre-commit-config.yaml")

    def test_pre_commit_has_ruff(self, addon_dir):
        """Pre-commit config includes ruff."""
        assert_file_exists(
            addon_dir / ".pre-commit-config.yaml",
            content_contains="ruff-pre-commit",
        )

    def test_pre_commit_has_hooks(self, addon_dir):
        """Pre-commit config includes standard hooks."""
        assert_file_exists(
            addon_dir / ".pre-commit-config.yaml",
            content_contains=["trailing-whitespace", "end-of-file-fixer"],
        )


class TestZCMLNamespaces:
    """Verify ZCML namespace declarations."""

    def test_addon_zcml_always_has_plone_namespace(
        self, temp_dir, backend_addon_template
    ):
        """Addon configure.zcml always has xmlns:plone."""
        pkg_dir = temp_dir / "mypackage"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={
                "package_name": "collective.mypackage",
                "is_headless": False,
            },
        )

        zcml = pkg_dir / "src/collective/mypackage/configure.zcml"
        assert_file_exists(zcml, content_contains="xmlns:plone")

    def test_headless_addon_has_plone_namespace(
        self, temp_dir, backend_addon_template
    ):
        """Headless addon configure.zcml also has xmlns:plone."""
        pkg_dir = temp_dir / "headless"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={
                "package_name": "collective.headless",
                "is_headless": True,
            },
        )

        zcml = pkg_dir / "src/collective/headless/configure.zcml"
        assert_file_exists(zcml, content_contains="xmlns:plone")

    def test_addon_zcml_is_valid_xml(self, temp_dir, backend_addon_template):
        """Addon configure.zcml is valid XML."""
        pkg_dir = temp_dir / "mypackage"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.mypackage"},
        )

        zcml = pkg_dir / "src/collective/mypackage/configure.zcml"
        try:
            ET.parse(zcml)
        except ET.ParseError as e:
            pytest.fail(f"Invalid XML in configure.zcml: {e}")


class TestZopeSetupRuffConfig:
    """Verify zope-setup template also has extended ruff config."""

    def test_zope_setup_has_extended_ruff(self, temp_dir, zope_setup_template):
        """Zope-setup pyproject.toml has extended ruff lint rules."""
        project_dir = temp_dir / "my-project"
        run_copier(
            zope_setup_template,
            project_dir,
            data={"project_name": "my-project"},
        )

        data = read_toml(project_dir / "pyproject.toml")
        ruff_select = data["tool"]["ruff"]["lint"]["select"]
        for rule in ["E", "F", "I", "W", "C90", "B", "S", "UP", "SIM", "PGH"]:
            assert rule in ruff_select, f"Missing ruff rule: {rule}"
