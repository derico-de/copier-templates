"""Tests for multi-subtemplate combinations."""
import pytest

from helpers import assert_dir_exists, assert_file_exists, read_toml, run_copier


class TestMultipleSubtemplates:
    """Test applying multiple subtemplates to same addon."""

    def test_addon_with_content_type_and_behavior(
        self, temp_dir, backend_addon_template, content_type_template, behavior_template
    ):
        """Addon with content type and behavior works together."""
        pkg_dir = temp_dir / "mypackage"

        # Create addon
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.news"},
        )

        # Add content type
        run_copier(
            content_type_template,
            pkg_dir,
            data={
                "content_type_name": "News Item",
                "package_name": "collective.news",
            },
        )

        # Add behavior
        run_copier(
            behavior_template,
            pkg_dir,
            data={
                "behavior_name": "IFeatured",
                "package_name": "collective.news",
            },
        )

        # Verify both exist
        assert_file_exists(pkg_dir / "src/collective/news/content/news_item.py")
        assert_file_exists(pkg_dir / "src/collective/news/behaviors/ifeatured.py")

        # Verify both registered in settings
        pyproject = pkg_dir / "pyproject.toml"
        data = read_toml(pyproject)
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"]["subtemplates"]
        assert "News Item" in subtemplates["content_types"]
        assert "IFeatured" in subtemplates["behaviors"]

    def test_addon_with_all_subtemplates(
        self,
        temp_dir,
        backend_addon_template,
        content_type_template,
        behavior_template,
        restapi_service_template,
    ):
        """Addon with all subtemplates works together."""
        pkg_dir = temp_dir / "mypackage"

        # Create addon
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.portal"},
        )

        # Add content type
        run_copier(
            content_type_template,
            pkg_dir,
            data={
                "content_type_name": "Article",
                "package_name": "collective.portal",
            },
        )

        # Add behavior
        run_copier(
            behavior_template,
            pkg_dir,
            data={
                "behavior_name": "ISocial",
                "package_name": "collective.portal",
            },
        )

        # Add service
        run_copier(
            restapi_service_template,
            pkg_dir,
            data={
                "service_name": "analytics",
                "package_name": "collective.portal",
            },
        )

        # Verify all exist
        assert_file_exists(pkg_dir / "src/collective/portal/content/article.py")
        assert_file_exists(pkg_dir / "src/collective/portal/behaviors/isocial.py")
        assert_file_exists(pkg_dir / "src/collective/portal/services/analytics.py")

        # Verify all registered
        pyproject = pkg_dir / "pyproject.toml"
        data = read_toml(pyproject)
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"]["subtemplates"]
        assert "Article" in subtemplates["content_types"]
        assert "ISocial" in subtemplates["behaviors"]
        assert "@analytics" in subtemplates["services"]


class TestFullStackIntegration:
    """Test full workflow: zope-setup + addon + subtemplates."""

    def test_full_stack_integration(
        self,
        temp_dir,
        zope_setup_template,
        backend_addon_template,
        content_type_template,
        behavior_template,
        restapi_service_template,
    ):
        """Full workflow: zope-setup + addon + subtemplates."""
        project_dir = temp_dir / "my-project"

        # Create zope-setup project
        result = run_copier(
            zope_setup_template,
            project_dir,
            data={"project_name": "my-project"},
        )
        assert result.returncode == 0, f"zope-setup failed: {result.stderr}"

        # Verify project structure
        assert_file_exists(project_dir / "pyproject.toml")
        assert_dir_exists(project_dir / "sources")

        # Create addon in sources/
        addon_dir = project_dir / "sources" / "mysite"
        result = run_copier(
            backend_addon_template,
            addon_dir,
            data={"package_name": "collective.mysite"},
        )
        assert result.returncode == 0, f"backend_addon failed: {result.stderr}"

        # Add multiple features
        result = run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": "Page",
                "package_name": "collective.mysite",
            },
        )
        assert result.returncode == 0, f"content_type failed: {result.stderr}"

        result = run_copier(
            behavior_template,
            addon_dir,
            data={
                "behavior_name": "ISocial",
                "package_name": "collective.mysite",
            },
        )
        assert result.returncode == 0, f"behavior failed: {result.stderr}"

        result = run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "stats",
                "package_name": "collective.mysite",
            },
        )
        assert result.returncode == 0, f"restapi_service failed: {result.stderr}"

        # Verify everything exists
        assert_file_exists(project_dir / "pyproject.toml")
        assert_file_exists(addon_dir / "pyproject.toml")
        assert_file_exists(addon_dir / "src/collective/mysite/content/page.py")
        assert_file_exists(addon_dir / "src/collective/mysite/behaviors/isocial.py")
        assert_file_exists(addon_dir / "src/collective/mysite/services/stats.py")

        # Verify project has correct settings
        project_pyproject = read_toml(project_dir / "pyproject.toml")
        assert "plone" in project_pyproject["tool"]
        assert "project" in project_pyproject["tool"]["plone"]

        # Verify addon has correct settings with all subtemplates
        addon_pyproject = read_toml(addon_dir / "pyproject.toml")
        subtemplates = addon_pyproject["tool"]["plone"]["backend_addon"]["settings"]["subtemplates"]
        assert "Page" in subtemplates["content_types"]
        assert "ISocial" in subtemplates["behaviors"]
        assert "@stats" in subtemplates["services"]


class TestSubtemplateMultipleInstances:
    """Test adding multiple instances of the same subtemplate type."""

    def test_multiple_content_types(
        self, temp_dir, backend_addon_template, content_type_template
    ):
        """Multiple content types can be added to same addon."""
        pkg_dir = temp_dir / "pkg"

        # Create addon
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "my.pkg"},
        )

        # Add first content type
        run_copier(
            content_type_template,
            pkg_dir,
            data={
                "content_type_name": "Article",
                "package_name": "my.pkg",
            },
        )

        # Add second content type
        run_copier(
            content_type_template,
            pkg_dir,
            data={
                "content_type_name": "News Item",
                "package_name": "my.pkg",
            },
        )

        # Verify both exist
        assert_file_exists(pkg_dir / "src/my/pkg/content/article.py")
        assert_file_exists(pkg_dir / "src/my/pkg/content/news_item.py")

        # Verify both registered
        pyproject = pkg_dir / "pyproject.toml"
        data = read_toml(pyproject)
        content_types = data["tool"]["plone"]["backend_addon"]["settings"]["subtemplates"]["content_types"]
        assert "Article" in content_types
        assert "News Item" in content_types

    def test_multiple_behaviors(
        self, temp_dir, backend_addon_template, behavior_template
    ):
        """Multiple behaviors can be added to same addon."""
        pkg_dir = temp_dir / "pkg"

        # Create addon
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "my.pkg"},
        )

        # Add behaviors
        for behavior in ["IFeatured", "ITaggable", "ISocial"]:
            run_copier(
                behavior_template,
                pkg_dir,
                data={
                    "behavior_name": behavior,
                    "package_name": "my.pkg",
                },
            )

        # Verify all exist
        assert_file_exists(pkg_dir / "src/my/pkg/behaviors/ifeatured.py")
        assert_file_exists(pkg_dir / "src/my/pkg/behaviors/itaggable.py")
        assert_file_exists(pkg_dir / "src/my/pkg/behaviors/isocial.py")

        # Verify all registered
        pyproject = pkg_dir / "pyproject.toml"
        data = read_toml(pyproject)
        behaviors = data["tool"]["plone"]["backend_addon"]["settings"]["subtemplates"]["behaviors"]
        assert "IFeatured" in behaviors
        assert "ITaggable" in behaviors
        assert "ISocial" in behaviors
