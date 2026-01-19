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
