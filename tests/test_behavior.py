"""Tests for behavior subtemplate."""
import pytest

from helpers import assert_file_exists, read_toml, run_copier


class TestBehaviorRequiresAddon:
    """Behavior subtemplate requires parent addon."""

    def test_fails_without_parent_addon(self, temp_dir, behavior_template):
        """Behavior fails if no parent addon detected."""
        result = run_copier(
            behavior_template,
            temp_dir,  # No addon here
            data={"behavior_name": "IFeatured"},
        )
        # The template may fail during tasks or produce incomplete output
        # Either way, check that it doesn't work properly
        behaviors_dir = temp_dir / "src"
        assert not behaviors_dir.exists() or result.returncode != 0

    def test_succeeds_with_parent_addon(self, temp_dir, backend_addon_template, behavior_template):
        """Behavior succeeds when parent addon exists."""
        # First create parent addon
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        # Then add behavior
        result = run_copier(
            behavior_template,
            temp_dir / "mypackage",
            data={
                "behavior_name": "IFeatured",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"Copier failed: {result.stderr}"

        # Verify behavior created
        behavior_file = temp_dir / "mypackage/src/collective/mypackage/behaviors/ifeatured.py"
        assert_file_exists(behavior_file)


class TestBehaviorCreation:
    """Test behavior file creation."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        """Create a parent addon for testing."""
        pkg_dir = temp_dir / "mypackage"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.mypackage"},
        )
        return pkg_dir

    def test_creates_behavior_module(self, addon_dir, behavior_template):
        """Behavior creates behavior module."""
        run_copier(
            behavior_template,
            addon_dir,
            data={
                "behavior_name": "ITaggable",
                "package_name": "collective.mypackage",
            },
        )

        behavior_file = addon_dir / "src/collective/mypackage/behaviors/itaggable.py"
        assert_file_exists(behavior_file)

    def test_creates_behaviors_init(self, addon_dir, behavior_template):
        """Behavior creates behaviors __init__.py."""
        run_copier(
            behavior_template,
            addon_dir,
            data={
                "behavior_name": "ITaggable",
                "package_name": "collective.mypackage",
            },
        )

        init_file = addon_dir / "src/collective/mypackage/behaviors/__init__.py"
        assert_file_exists(init_file)

    def test_creates_behaviors_configure_zcml(self, addon_dir, behavior_template):
        """Behavior creates behaviors configure.zcml."""
        run_copier(
            behavior_template,
            addon_dir,
            data={
                "behavior_name": "ITaggable",
                "package_name": "collective.mypackage",
            },
        )

        zcml_file = addon_dir / "src/collective/mypackage/behaviors/configure.zcml"
        assert_file_exists(zcml_file)

    def test_behavior_has_interface(self, addon_dir, behavior_template):
        """Behavior file contains interface."""
        run_copier(
            behavior_template,
            addon_dir,
            data={
                "behavior_name": "ITaggable",
                "package_name": "collective.mypackage",
            },
        )

        behavior_file = addon_dir / "src/collective/mypackage/behaviors/itaggable.py"
        assert_file_exists(behavior_file, content_contains="ITaggable")


class TestBehaviorIntegration:
    """Test behavior registers in parent addon."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        """Create a parent addon for testing."""
        pkg_dir = temp_dir / "pkg"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "my.pkg"},
        )
        return pkg_dir

    def test_updates_addon_settings(self, addon_dir, behavior_template):
        """Behavior registered in addon settings."""
        run_copier(
            behavior_template,
            addon_dir,
            data={
                "behavior_name": "ITaggable",
                "package_name": "my.pkg",
            },
        )

        pyproject = addon_dir / "pyproject.toml"
        data = read_toml(pyproject)
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"]["subtemplates"]
        assert "ITaggable" in subtemplates["behaviors"]

    def test_adds_parent_zcml_include(self, addon_dir, behavior_template):
        """Behavior adds include to parent configure.zcml."""
        run_copier(
            behavior_template,
            addon_dir,
            data={
                "behavior_name": "ITaggable",
                "package_name": "my.pkg",
            },
        )

        parent_zcml = addon_dir / "src/my/pkg/configure.zcml"
        assert_file_exists(parent_zcml, content_contains='<include package=".behaviors" />')


class TestBehaviorEdgeCases:
    """Test behavior edge cases and options."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        """Create a parent addon for testing."""
        pkg_dir = temp_dir / "mypackage"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.mypackage"},
        )
        return pkg_dir

    def test_behavior_without_marker(self, addon_dir, behavior_template):
        """Behavior without marker interface."""
        run_copier(
            behavior_template,
            addon_dir,
            data={
                "behavior_name": "ISimple",
                "package_name": "collective.mypackage",
                "behavior_marker": False,
            },
        )

        behavior_file = addon_dir / "src/collective/mypackage/behaviors/isimple.py"
        content = behavior_file.read_text()
        assert "ISimpleMarker" not in content

        zcml_file = addon_dir / "src/collective/mypackage/behaviors/configure.zcml"
        content = zcml_file.read_text()
        assert "marker=" not in content

    def test_behavior_without_factory(self, addon_dir, behavior_template):
        """Behavior without factory/adapter."""
        run_copier(
            behavior_template,
            addon_dir,
            data={
                "behavior_name": "ILight",
                "package_name": "collective.mypackage",
                "behavior_factory": False,
            },
        )

        behavior_file = addon_dir / "src/collective/mypackage/behaviors/ilight.py"
        content = behavior_file.read_text()
        assert "@implementer" not in content
        assert "@adapter" not in content

        zcml_file = addon_dir / "src/collective/mypackage/behaviors/configure.zcml"
        content = zcml_file.read_text()
        assert "factory=" not in content
