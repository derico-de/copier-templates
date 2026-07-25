"""Tests for restapi_service subtemplate."""
import pytest
from helpers import assert_file_exists, read_toml, run_copier


class TestRestapiServiceRequiresAddon:
    """REST API service subtemplate requires parent addon."""

    def test_succeeds_with_parent_addon(self, temp_dir, backend_addon_template, restapi_service_template):
        """REST API service succeeds when parent addon exists."""
        # First create parent addon
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        # Then add service
        result = run_copier(
            restapi_service_template,
            temp_dir / "mypackage",
            data={
                "service_name": "stats",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"Copier failed: {result.stderr}"

        # Verify service created
        service_file = temp_dir / "mypackage/src/collective/mypackage/services/stats.py"
        assert_file_exists(service_file)


class TestRestapiServiceCreation:
    """Test REST API service file creation."""

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

    def test_creates_service_module(self, addon_dir, restapi_service_template):
        """Service creates service module."""
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "health-check",
                "package_name": "collective.mypackage",
            },
        )

        service_file = addon_dir / "src/collective/mypackage/services/health_check.py"
        assert_file_exists(service_file)

    def test_creates_services_init(self, addon_dir, restapi_service_template):
        """Service creates services __init__.py."""
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "stats",
                "package_name": "collective.mypackage",
            },
        )

        init_file = addon_dir / "src/collective/mypackage/services/__init__.py"
        assert_file_exists(init_file)

    def test_creates_services_configure_zcml(self, addon_dir, restapi_service_template):
        """Service creates services configure.zcml."""
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "stats",
                "package_name": "collective.mypackage",
            },
        )

        zcml_file = addon_dir / "src/collective/mypackage/services/configure.zcml"
        assert_file_exists(zcml_file)

    def test_service_has_get_method(self, addon_dir, restapi_service_template):
        """Service file contains GET method."""
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "stats",
                "package_name": "collective.mypackage",
                "http_get": True,
            },
        )

        service_file = addon_dir / "src/collective/mypackage/services/stats.py"
        assert_file_exists(service_file, content_contains="def reply")

    def test_service_endpoint_name(self, addon_dir, restapi_service_template):
        """Service has correct endpoint name."""
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "my-custom-endpoint",
                "package_name": "collective.mypackage",
            },
        )

        zcml_file = addon_dir / "src/collective/mypackage/services/configure.zcml"
        assert_file_exists(zcml_file, content_contains="@my-custom-endpoint")


class TestRestapiServiceIntegration:
    """Test REST API service registers in parent addon."""

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

    def test_updates_addon_settings(self, addon_dir, restapi_service_template):
        """Service registered in addon settings."""
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "stats",
                "package_name": "my.pkg",
            },
        )

        pyproject = addon_dir / "pyproject.toml"
        data = read_toml(pyproject)
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"]["subtemplates"]
        assert "@stats" in subtemplates["services"]

    def test_adds_parent_zcml_include(self, addon_dir, restapi_service_template):
        """Service adds include to parent configure.zcml."""
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "stats",
                "package_name": "my.pkg",
            },
        )

        parent_zcml = addon_dir / "src/my/pkg/configure.zcml"
        assert_file_exists(parent_zcml, content_contains='<include package=".services" />')


class TestRestapiServiceEdgeCases:
    """Test REST API service edge cases and options."""

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

    def test_service_with_post_method(self, addon_dir, restapi_service_template):
        """Service with POST method support."""
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "submit",
                "package_name": "collective.mypackage",
                "http_post": True,
            },
        )

        service_file = addon_dir / "src/collective/mypackage/services/submit.py"
        assert_file_exists(service_file, content_contains="def POST(self)")

        zcml_file = addon_dir / "src/collective/mypackage/services/configure.zcml"
        assert_file_exists(zcml_file, content_contains='method="POST"')

    def test_service_with_delete_method(self, addon_dir, restapi_service_template):
        """Service with DELETE method support."""
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "cleanup",
                "package_name": "collective.mypackage",
                "http_delete": True,
            },
        )

        service_file = addon_dir / "src/collective/mypackage/services/cleanup.py"
        assert_file_exists(service_file, content_contains="def DELETE(self)")

        zcml_file = addon_dir / "src/collective/mypackage/services/configure.zcml"
        assert_file_exists(zcml_file, content_contains='method="DELETE"')

    def test_service_for_site_root(self, addon_dir, restapi_service_template):
        """Service registered for IPloneSiteRoot."""
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "site-info",
                "package_name": "collective.mypackage",
                "service_for": "Products.CMFPlone.interfaces.IPloneSiteRoot",
            },
        )

        zcml_file = addon_dir / "src/collective/mypackage/services/configure.zcml"
        assert_file_exists(
            zcml_file,
            content_contains="Products.CMFPlone.interfaces.IPloneSiteRoot",
        )

    def test_service_for_own_content_type_interface(
        self, addon_dir, content_type_template, restapi_service_template
    ):
        """service_for can target a content type interface from this package."""
        run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": "Article",
                "package_name": "collective.mypackage",
            },
        )
        own_iface = "collective.mypackage.content.article.IArticle"
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "article-info",
                "package_name": "collective.mypackage",
                "service_for": own_iface,
            },
        )
        zcml_file = addon_dir / "src/collective/mypackage/services/configure.zcml"
        assert_file_exists(zcml_file, content_contains=f'for="{own_iface}"')

    def test_service_for_manual_entry(
        self, addon_dir, restapi_service_template
    ):
        """'<enter manually>' resolves to the custom interface dotted name."""
        custom = "my.package.interfaces.ICustom"
        run_copier(
            restapi_service_template,
            addon_dir,
            data={
                "service_name": "custom-svc",
                "package_name": "collective.mypackage",
                "service_for": "<enter manually>",
                "service_for_manual": custom,
            },
        )
        zcml_file = addon_dir / "src/collective/mypackage/services/configure.zcml"
        assert_file_exists(zcml_file, content_contains=f'for="{custom}"')


class TestRestapiServiceProfileWiring:
    """metadata.xml dependency and description propagation."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        pkg_dir = temp_dir / "mypackage"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.mypackage"},
        )
        return pkg_dir

    def _apply(self, addon_dir, restapi_service_template, **extra):
        data = {
            "service_name": "stats",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = run_copier(restapi_service_template, addon_dir, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_metadata_gains_restapi_dependency(
        self, addon_dir, restapi_service_template
    ):
        self._apply(addon_dir, restapi_service_template)
        metadata = (
            addon_dir
            / "src/collective/mypackage/profiles/default/metadata.xml"
        )
        assert_file_exists(
            metadata,
            content_contains=(
                "<dependency>profile-plone.restapi:default</dependency>"
            ),
        )

    def test_metadata_dependency_added_exactly_once(
        self, addon_dir, restapi_service_template
    ):
        self._apply(addon_dir, restapi_service_template, service_name="stats")
        self._apply(addon_dir, restapi_service_template, service_name="info")
        content = (
            addon_dir
            / "src/collective/mypackage/profiles/default/metadata.xml"
        ).read_text()
        assert content.count("profile-plone.restapi:default") == 1

    def test_service_description_lands_in_module(
        self, addon_dir, restapi_service_template
    ):
        self._apply(
            addon_dir,
            restapi_service_template,
            service_description="Aggregated usage statistics",
        )
        service = (
            addon_dir / "src/collective/mypackage/services/stats.py"
        )
        assert_file_exists(
            service, content_contains="Aggregated usage statistics"
        )
