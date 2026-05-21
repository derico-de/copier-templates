"""Tests verifying subtemplates work for legacy addons.

A legacy addon is one created by the older ``bobtemplates.plone`` tool:
it has a ``bobtemplate.cfg`` and a ``setup.py`` (no ``pyproject.toml``).
The subtemplates here must:

- not bail out on the missing pyproject.toml,
- write subtemplate registrations into ``bobtemplate.cfg``'s
  ``[subtemplates]`` section,
- still wire generated files into the addon's ZCML / profile XML.
"""
from __future__ import annotations

import configparser
import textwrap
from pathlib import Path

import pytest
from helpers import apply_subtemplate, assert_file_exists

PACKAGE_NAME = "collective.legacypkg"
PACKAGE_FOLDER = "collective/legacypkg"


def _read_cfg(path: Path) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(path)
    return config


def _subtemplate_value(cfg_path: Path, subtemplate_type: str) -> list[str]:
    config = _read_cfg(cfg_path)
    if not config.has_section("subtemplates"):
        return []
    raw = config.get("subtemplates", subtemplate_type, fallback="")
    return [s.strip() for s in raw.split(",") if s.strip()]


@pytest.fixture
def legacy_addon(temp_dir: Path) -> Path:
    """A minimal bobtemplates.plone-style addon (no pyproject.toml)."""
    root = temp_dir / "legacypkg"
    pkg = root / "src" / PACKAGE_FOLDER
    (pkg / "profiles" / "default").mkdir(parents=True)

    (root / "bobtemplate.cfg").write_text(
        textwrap.dedent(
            f"""\
            [mr.bob]
            template = bobtemplates.plone:addon

            [variables]
            package.name = {PACKAGE_NAME}
            package.type = Addon
            """
        )
    )

    (root / "setup.py").write_text(
        textwrap.dedent(
            f"""\
            from setuptools import setup

            setup(
                name='{PACKAGE_NAME}',
                version='1.0',
                install_requires=['Plone'],
            )
            """
        )
    )

    (pkg / "__init__.py").write_text("")
    (pkg / "configure.zcml").write_text(
        textwrap.dedent(
            f"""\
            <configure
                xmlns="http://namespaces.zope.org/zope"
                xmlns:browser="http://namespaces.zope.org/browser"
                i18n_domain="{PACKAGE_NAME}">

            </configure>
            """
        )
    )
    (pkg / "profiles" / "default" / "metadata.xml").write_text(
        textwrap.dedent(
            """\
            <metadata>
              <version>1000</version>
            </metadata>
            """
        )
    )

    return root


class TestUpgradeStepLegacy:
    """upgrade_step on a legacy addon wires ZCML and bumps metadata."""

    def test_creates_per_step_zcml(
        self, legacy_addon, upgrade_step_template
    ):
        result = apply_subtemplate(
            upgrade_step_template,
            legacy_addon,
            data={
                "package_name": PACKAGE_NAME,
                "package_folder": PACKAGE_FOLDER,
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )
        assert result.returncode == 0, result.stderr

        step_zcml = legacy_addon / f"src/{PACKAGE_FOLDER}/upgrades/1001.zcml"
        assert_file_exists(
            step_zcml,
            content_contains=[
                "genericsetup:upgradeStep",
                'destination="1001"',
                f'profile="{PACKAGE_NAME}:default"',
            ],
        )

    def test_updates_upgrade_configure_zcml(
        self, legacy_addon, upgrade_step_template
    ):
        result = apply_subtemplate(
            upgrade_step_template,
            legacy_addon,
            data={
                "package_name": PACKAGE_NAME,
                "package_folder": PACKAGE_FOLDER,
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )
        assert result.returncode == 0, result.stderr

        zcml = legacy_addon / f"src/{PACKAGE_FOLDER}/upgrades/configure.zcml"
        assert_file_exists(
            zcml, content_contains='<include file="1001.zcml" />'
        )

    def test_adds_parent_zcml_include(
        self, legacy_addon, upgrade_step_template
    ):
        result = apply_subtemplate(
            upgrade_step_template,
            legacy_addon,
            data={
                "package_name": PACKAGE_NAME,
                "package_folder": PACKAGE_FOLDER,
                "upgrade_step_title": "Add catalog index",
            },
        )
        assert result.returncode == 0, result.stderr

        parent_zcml = legacy_addon / f"src/{PACKAGE_FOLDER}/configure.zcml"
        assert_file_exists(
            parent_zcml, content_contains='<include package=".upgrades" />'
        )

    def test_bumps_metadata_version(
        self, legacy_addon, upgrade_step_template
    ):
        result = apply_subtemplate(
            upgrade_step_template,
            legacy_addon,
            data={
                "package_name": PACKAGE_NAME,
                "package_folder": PACKAGE_FOLDER,
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )
        assert result.returncode == 0, result.stderr

        metadata = (
            legacy_addon
            / f"src/{PACKAGE_FOLDER}/profiles/default/metadata.xml"
        )
        assert_file_exists(metadata, content_contains="<version>1001</version>")

    def test_does_not_create_pyproject(
        self, legacy_addon, upgrade_step_template
    ):
        result = apply_subtemplate(
            upgrade_step_template,
            legacy_addon,
            data={
                "package_name": PACKAGE_NAME,
                "package_folder": PACKAGE_FOLDER,
                "upgrade_step_title": "Add catalog index",
            },
        )
        assert result.returncode == 0, result.stderr
        assert not (legacy_addon / "pyproject.toml").exists()


class TestViewLegacy:
    """view subtemplate on a legacy addon wires ZCML and registers."""

    def test_view_zcml_and_registration(
        self, legacy_addon, view_template
    ):
        result = apply_subtemplate(
            view_template,
            legacy_addon,
            data={
                "package_name": PACKAGE_NAME,
                "package_folder": PACKAGE_FOLDER,
                "view_name": "my-view",
                "view_for_interface": "*",
                "view_module": "my_view",
                "view_class_name": "MyView",
                "view_template": "True",
                "view_marker": "False",
            },
        )
        assert result.returncode == 0, result.stderr

        views_zcml = legacy_addon / f"src/{PACKAGE_FOLDER}/views/configure.zcml"
        assert_file_exists(
            views_zcml,
            content_contains=[
                "browser:page",
                'name="my-view"',
                'class=".my_view.MyView"',
            ],
        )

        parent_zcml = legacy_addon / f"src/{PACKAGE_FOLDER}/configure.zcml"
        assert_file_exists(
            parent_zcml, content_contains='<include package=".views" />'
        )

        assert "my-view" in _subtemplate_value(
            legacy_addon / "bobtemplate.cfg", "views"
        )


class TestSetupPyOnlyAddon:
    """Pure setup.py addon (no bobtemplate.cfg) still gets ZCML wiring."""

    @pytest.fixture
    def setup_py_addon(self, temp_dir: Path) -> Path:
        root = temp_dir / "setuponly"
        pkg = root / "src" / PACKAGE_FOLDER
        (pkg / "profiles" / "default").mkdir(parents=True)
        (root / "setup.py").write_text(
            f"from setuptools import setup\nsetup(name='{PACKAGE_NAME}', "
            "version='1.0', install_requires=['Plone'])\n"
        )
        (pkg / "__init__.py").write_text("")
        (pkg / "configure.zcml").write_text(
            f'<configure xmlns="http://namespaces.zope.org/zope" '
            f'i18n_domain="{PACKAGE_NAME}"></configure>\n'
        )
        (pkg / "profiles" / "default" / "metadata.xml").write_text(
            "<metadata><version>1000</version></metadata>\n"
        )
        return root

    def test_upgrade_step_wires_zcml_without_bobtemplate(
        self, setup_py_addon, upgrade_step_template
    ):
        result = apply_subtemplate(
            upgrade_step_template,
            setup_py_addon,
            data={
                "package_name": PACKAGE_NAME,
                "package_folder": PACKAGE_FOLDER,
                "upgrade_step_title": "Add index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )
        assert result.returncode == 0, result.stderr

        # ZCML wiring still happens
        zcml = setup_py_addon / f"src/{PACKAGE_FOLDER}/upgrades/configure.zcml"
        assert_file_exists(
            zcml, content_contains='<include file="1001.zcml" />'
        )
        # Neither pyproject.toml nor bobtemplate.cfg should be created
        assert not (setup_py_addon / "pyproject.toml").exists()
        assert not (setup_py_addon / "bobtemplate.cfg").exists()
