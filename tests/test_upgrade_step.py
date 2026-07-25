"""Tests for upgrade_step subtemplate."""
import shutil
import subprocess
import textwrap

import pytest
from helpers import assert_file_exists, plone_subprocess_env, run_copier


class TestUpgradeStepRequiresAddon:
    """Upgrade step subtemplate requires parent addon."""

    def test_fails_without_parent_addon(self, temp_dir, upgrade_step_template):
        """Upgrade step fails if no parent addon detected."""
        result = run_copier(
            upgrade_step_template,
            temp_dir,
            data={"upgrade_step_title": "Add index"},
        )
        assert result.returncode != 0
        error_msg = result.stderr.lower()
        assert (
            "parent addon" in error_msg
            or "no parent addon" in error_msg
            or "package_name" in error_msg
        )

    def test_succeeds_with_parent_addon(
        self, temp_dir, backend_addon_template, upgrade_step_template
    ):
        """Upgrade step succeeds when parent addon exists."""
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        result = run_copier(
            upgrade_step_template,
            temp_dir / "mypackage",
            data={"upgrade_step_title": "Add catalog index"},
        )
        assert result.returncode == 0, f"Copier failed: {result.stderr}"


class TestUpgradeStepCreation:
    """Test upgrade step file creation."""

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

    def test_creates_handler_module(self, addon_dir, upgrade_step_template):
        """Upgrade step creates versioned handler Python module."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        handler = (
            addon_dir
            / "src/collective/mypackage/upgrades/v1001.py"
        )
        assert_file_exists(handler, content_contains="def upgrade")

    def test_creates_per_step_zcml(self, addon_dir, upgrade_step_template):
        """Upgrade step creates per-step ZCML file."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        step_zcml = (
            addon_dir
            / "src/collective/mypackage/upgrades/1001.zcml"
        )
        assert_file_exists(step_zcml, content_contains=[
            "genericsetup:upgradeStep",
            'source="1000"',
            'destination="1001"',
            'handler=".v1001.upgrade"',
            'profile="collective.mypackage:default"',
        ])

    def test_creates_per_step_profile_dir(self, addon_dir, upgrade_step_template):
        """Upgrade step creates per-step profile directory with metadata.txt."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        metadata = (
            addon_dir
            / "src/collective/mypackage/upgrades/1001/metadata.txt"
        )
        assert metadata.exists()
        # bobtemplates parity: the version dir also ships a .gitkeep
        assert (
            addon_dir / "src/collective/mypackage/upgrades/1001/.gitkeep"
        ).exists()

    def test_creates_upgrades_init(self, addon_dir, upgrade_step_template):
        """Upgrade step creates upgrades __init__.py."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={"upgrade_step_title": "Add catalog index"},
        )

        init_file = addon_dir / "src/collective/mypackage/upgrades/__init__.py"
        assert init_file.exists()

    def test_handler_has_logging(self, addon_dir, upgrade_step_template):
        """Handler module includes logging setup."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        handler = (
            addon_dir
            / "src/collective/mypackage/upgrades/v1001.py"
        )
        assert_file_exists(handler, content_contains=[
            "import logging",
            "logger = logging.getLogger",
        ])

    def test_handler_has_version_info(self, addon_dir, upgrade_step_template):
        """Handler docstring includes version info."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        handler = (
            addon_dir
            / "src/collective/mypackage/upgrades/v1001.py"
        )
        assert_file_exists(handler, content_contains="1000")


class TestUpgradeStepIntegration:
    """Test upgrade step registers in parent addon."""

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

    def test_adds_parent_zcml_include(self, addon_dir, upgrade_step_template):
        """Upgrade step adds include to parent configure.zcml."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={"upgrade_step_title": "Add catalog index"},
        )

        parent_zcml = addon_dir / "src/my/pkg/configure.zcml"
        assert_file_exists(
            parent_zcml, content_contains='<include package=".upgrades" />'
        )

    def test_bumps_metadata_version(self, addon_dir, upgrade_step_template):
        """Upgrade step bumps metadata.xml profile version."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        metadata = addon_dir / "src/my/pkg/profiles/default/metadata.xml"
        assert_file_exists(metadata, content_contains="<version>1001</version>")

    def test_creates_upgrade_configure_zcml(self, addon_dir, upgrade_step_template):
        """Upgrade step creates upgrades/configure.zcml with file include."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        zcml = addon_dir / "src/my/pkg/upgrades/configure.zcml"
        assert_file_exists(zcml, content_contains=[
            '<include file="1001.zcml" />',
        ])

    def test_creates_per_step_zcml_with_registration(
        self, addon_dir, upgrade_step_template
    ):
        """Per-step ZCML contains the upgradeStep registration."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        step_zcml = addon_dir / "src/my/pkg/upgrades/1001.zcml"
        assert_file_exists(step_zcml, content_contains=[
            "genericsetup:upgradeStep",
            'source="1000"',
            'destination="1001"',
            'handler=".v1001.upgrade"',
            'profile="my.pkg:default"',
        ])


class TestMultipleUpgradeSteps:
    """Test adding multiple upgrade steps."""

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

    def test_second_step_adds_include_to_zcml(
        self, addon_dir, upgrade_step_template
    ):
        """Second upgrade step adds its include to configure.zcml."""
        # First upgrade step
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        # Second upgrade step
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Migrate content",
                "source_version": "1001",
                "destination_version": "1002",
            },
        )

        zcml = addon_dir / "src/my/pkg/upgrades/configure.zcml"
        assert_file_exists(zcml, content_contains=[
            '<include file="1001.zcml" />',
            '<include file="1002.zcml" />',
        ])

    def test_second_step_creates_separate_files(
        self, addon_dir, upgrade_step_template
    ):
        """Each upgrade step gets its own handler, zcml, and profile dir."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Migrate content",
                "source_version": "1001",
                "destination_version": "1002",
            },
        )

        handler1 = addon_dir / "src/my/pkg/upgrades/v1001.py"
        handler2 = addon_dir / "src/my/pkg/upgrades/v1002.py"
        assert_file_exists(handler1, content_contains="def upgrade")
        assert_file_exists(handler2, content_contains="def upgrade")

        step_zcml1 = addon_dir / "src/my/pkg/upgrades/1001.zcml"
        step_zcml2 = addon_dir / "src/my/pkg/upgrades/1002.zcml"
        assert_file_exists(step_zcml1, content_contains='destination="1001"')
        assert_file_exists(step_zcml2, content_contains='destination="1002"')

        assert (addon_dir / "src/my/pkg/upgrades/1001/metadata.txt").exists()
        assert (addon_dir / "src/my/pkg/upgrades/1002/metadata.txt").exists()

    def test_metadata_version_is_latest(self, addon_dir, upgrade_step_template):
        """After multiple steps, metadata.xml has the latest version."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Migrate content",
                "source_version": "1001",
                "destination_version": "1002",
            },
        )

        metadata = addon_dir / "src/my/pkg/profiles/default/metadata.xml"
        assert_file_exists(metadata, content_contains="<version>1002</version>")


@pytest.mark.integration
class TestUpgradeStepInPloneSite:
    """End-to-end: install addon in a real Plone site, then run the upgrade.

    Generates a backend_addon, applies the upgrade_step template, runs
    ``uv sync`` to install Plone, then drives a pytest-based integration
    test inside the generated addon that:

    1. Boots a Plone test layer (which installs the addon at metadata
       version 1001 — the post-upgrade state).
    2. Rolls ``portal_setup``'s recorded version back to ``1000`` to
       simulate an addon that was installed before the upgrade step
       existed (creating the "starting profile" state).
    3. Calls ``portal_setup.upgradeProfile()`` to apply pending steps.
    4. Asserts the recorded profile version was bumped to ``1001``.

    Slow (downloads Plone on first run). Opt in with ``pytest -m integration``.
    """

    def test_upgrade_bumps_profile_version_in_plone_site(
        self, temp_dir, backend_addon_template, upgrade_step_template
    ):
        if shutil.which("uv") is None:
            pytest.skip("uv is required to run the Plone integration test")

        addon_dir = temp_dir / "myaddon"
        package_name = "collective.upgradetest"

        # 1. Generate parent addon (metadata.xml version = 1000).
        result = run_copier(
            backend_addon_template,
            addon_dir,
            data={"package_name": package_name},
        )
        assert result.returncode == 0, f"backend_addon failed: {result.stderr}"

        # 2. Generate upgrade step 1000 -> 1001 (bumps metadata.xml to 1001,
        #    registers handler + per-step ZCML in the addon's upgrades/).
        result = run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Bump to 1001",
                "upgrade_step_description": "Test upgrade step",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )
        assert result.returncode == 0, f"upgrade_step failed: {result.stderr}"

        # 3. Drop a Plone integration test alongside the generated tests.
        plone_test = (
            addon_dir
            / "src/collective/upgradetest/tests/test_upgrade_integration.py"
        )
        plone_test.write_text(textwrap.dedent(f'''\
            """Plone integration test for upgrade step 1000 -> 1001."""
            from plone.app.testing import setRoles, TEST_USER_ID


            class TestUpgradeProfileVersion:
                """Verify portal_setup bumps the profile version after upgrade."""

                profile_id = "{package_name}:default"

                def test_upgrade_step_bumps_profile_version(self, integration):
                    portal = integration["portal"]
                    setRoles(portal, TEST_USER_ID, ["Manager"])
                    setup_tool = portal.portal_setup

                    # Layer setUp already applied the default profile, so
                    # the recorded version is the current metadata.xml (1001).
                    # Simulate the pre-upgrade state by rolling it back to 1000.
                    setup_tool.setLastVersionForProfile(self.profile_id, "1000")
                    assert setup_tool.getLastVersionForProfile(
                        self.profile_id
                    ) == ("1000",)

                    pending = setup_tool.listUpgrades(self.profile_id)
                    assert pending, (
                        "Expected at least one pending upgrade step "
                        "from 1000 to 1001"
                    )

                    setup_tool.upgradeProfile(self.profile_id)

                    assert setup_tool.getLastVersionForProfile(
                        self.profile_id
                    ) == ("1001",), (
                        "Upgrade did not bump the profile version to 1001"
                    )
        '''))

        # 4. Install Plone + addon deps in the generated package.
        sync = subprocess.run(
            ["uv", "sync", "--extra", "test"],
            cwd=addon_dir,
            env=plone_subprocess_env(),
            capture_output=True,
            text=True,
            timeout=900,
        )
        assert sync.returncode == 0, (
            f"uv sync failed:\nSTDOUT:\n{sync.stdout}\nSTDERR:\n{sync.stderr}"
        )

        # 5. Run the integration test inside the generated addon.
        run = subprocess.run(
            [
                "uv", "run", "pytest",
                "src/collective/upgradetest/tests/test_upgrade_integration.py",
                "-v", "--tb=short",
            ],
            cwd=addon_dir,
            env=plone_subprocess_env(),
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert run.returncode == 0, (
            "Plone integration test failed:\n"
            f"STDOUT:\n{run.stdout}\nSTDERR:\n{run.stderr}"
        )
