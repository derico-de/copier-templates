"""Tests for backend_addon template."""
import pytest

from helpers import assert_dir_exists, assert_file_exists, read_toml, run_copier


class TestBackendAddonIsolated:
    """Test backend_addon template in isolation."""

    def test_creates_package_structure(self, temp_dir, backend_addon_template):
        """Backend addon creates correct package structure."""
        result = run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )
        assert result.returncode == 0, f"Copier failed: {result.stderr}"

        # Verify structure
        pkg_dir = temp_dir / "mypackage"
        assert_file_exists(pkg_dir / "pyproject.toml")
        assert_file_exists(pkg_dir / "src/collective/mypackage/__init__.py")
        assert_file_exists(pkg_dir / "src/collective/mypackage/configure.zcml")

    def test_pyproject_has_addon_settings(self, temp_dir, backend_addon_template):
        """Backend addon includes custom settings namespace."""
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        pyproject = temp_dir / "mypackage/pyproject.toml"
        assert_file_exists(
            pyproject,
            content_contains="[tool.plone.backend_addon.settings]",
        )

    def test_flat_package_name_allowed(self, temp_dir, backend_addon_template):
        """Flat package names (without namespace) are allowed."""
        result = run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "mypackage"},  # No dot
        )
        assert result.returncode == 0, f"Copier failed: {result.stderr}"
        assert_file_exists(temp_dir / "mypackage/src/mypackage/__init__.py")

    def test_addon_settings_contain_package_info(self, temp_dir, backend_addon_template):
        """Addon settings include package name and folder."""
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        pyproject = temp_dir / "mypackage/pyproject.toml"
        data = read_toml(pyproject)
        settings = data["tool"]["plone"]["backend_addon"]["settings"]
        assert settings["package_name"] == "collective.mypackage"
        assert settings["package_folder"] == "collective/mypackage"

    def test_creates_configure_zcml(self, temp_dir, backend_addon_template):
        """Backend addon creates configure.zcml."""
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        zcml = temp_dir / "mypackage/src/collective/mypackage/configure.zcml"
        assert_file_exists(zcml, content_contains="<configure")

    def test_creates_testing_module(self, temp_dir, backend_addon_template):
        """Backend addon creates testing.py module."""
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        testing = temp_dir / "mypackage/src/collective/mypackage/testing.py"
        assert_file_exists(testing)

    def test_creates_readme(self, temp_dir, backend_addon_template):
        """Backend addon creates README.md."""
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        readme = temp_dir / "mypackage/README.md"
        assert_file_exists(readme, content_contains="collective.mypackage")

    def test_creates_changelog(self, temp_dir, backend_addon_template):
        """Backend addon creates CHANGELOG.md."""
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        changelog = temp_dir / "mypackage/CHANGELOG.md"
        assert_file_exists(changelog)

    def test_creates_copier_answers_file(self, temp_dir, backend_addon_template):
        """Backend addon creates copier answers file."""
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        answers = temp_dir / "mypackage/.copier-answers.yml"
        assert_file_exists(answers)

    def test_headless_option(self, temp_dir, backend_addon_template):
        """Backend addon handles headless option."""
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={
                "package_name": "collective.mypackage",
                "is_headless": True,
            },
        )

        pyproject = temp_dir / "mypackage/pyproject.toml"
        data = read_toml(pyproject)
        settings = data["tool"]["plone"]["backend_addon"]["settings"]
        assert settings["is_headless"] is True


class TestBackendAddonNamespaces:
    """Test namespace package handling."""

    def test_single_level_namespace(self, temp_dir, backend_addon_template):
        """Single level namespace package works."""
        run_copier(
            backend_addon_template,
            temp_dir / "pkg",
            data={"package_name": "collective.news"},
        )

        assert_file_exists(temp_dir / "pkg/src/collective/news/__init__.py")
        assert_dir_exists(temp_dir / "pkg/src/collective")

    def test_two_level_namespace(self, temp_dir, backend_addon_template):
        """Two level namespace package works."""
        run_copier(
            backend_addon_template,
            temp_dir / "pkg",
            data={"package_name": "plone.app.myfeature"},
        )

        assert_file_exists(temp_dir / "pkg/src/plone/app/myfeature/__init__.py")
        assert_dir_exists(temp_dir / "pkg/src/plone/app")
