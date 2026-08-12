"""Tests for the theme_barceloneta subtemplate.

Mirrors bobtemplates.plone theme_barceloneta — Barceloneta-based theme
variant. Shares the theme_basic file layout but with scss content that
imports Barceloneta.
"""
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestThemeBarcelonetaRequiresAddon:
    def test_fails_without_parent_addon(
        self, temp_dir, theme_barceloneta_template
    ):
        result = run_copier(
            theme_barceloneta_template,
            temp_dir,
            data={"theme_name": "My Barceloneta Theme"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestThemeBarcelonetaCreation:
    def _apply(self, fresh_addon, theme_barceloneta_template, **extra):
        data = {
            "theme_name": "My Barceloneta Theme",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(
            theme_barceloneta_template, fresh_addon, data=data
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_manifest(self, fresh_addon, theme_barceloneta_template):
        self._apply(fresh_addon, theme_barceloneta_template)
        manifest = fresh_addon / "src/collective/mypackage/theme/manifest.cfg"
        assert_file_exists(
            manifest,
            content_contains=["[theme]", "My Barceloneta Theme"],
        )

    def test_scss_imports_barceloneta(
        self, fresh_addon, theme_barceloneta_template
    ):
        self._apply(fresh_addon, theme_barceloneta_template)
        scss = fresh_addon / "src/collective/mypackage/theme/scss/theme.scss"
        assert_file_exists(scss, content_contains="barceloneta")

    def test_creates_theme_profile_xml(
        self, fresh_addon, theme_barceloneta_template
    ):
        self._apply(fresh_addon, theme_barceloneta_template)
        xml = fresh_addon / "src/collective/mypackage/profiles/default/theme.xml"
        assert_file_exists(xml, content_contains="my-barceloneta-theme")


class TestThemeBarcelonetaIntegration:
    def test_registers_in_pyproject(
        self, fresh_addon, theme_barceloneta_template
    ):
        result = apply_subtemplate(
            theme_barceloneta_template,
            fresh_addon,
            data={
                "theme_name": "Barc Theme",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "Barc Theme" in subtemplates["themes"]

    def test_registers_plone_static_in_parent_zcml(
        self, fresh_addon, theme_barceloneta_template
    ):
        result = apply_subtemplate(
            theme_barceloneta_template,
            fresh_addon,
            data={
                "theme_name": "My Barceloneta Theme",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert_file_exists(
            zcml,
            content_contains=[
                "<plone:static",
                'directory="theme"',
                'name="my-barceloneta-theme"',
                'type="theme"',
            ],
        )


class TestThemeProfileDependency:
    """The generated profile depends on plone.app.theming."""

    def test_metadata_gains_theming_dependency(self, fresh_addon, theme_barceloneta_template):
        result = apply_subtemplate(
            theme_barceloneta_template,
            fresh_addon,
            data={
                "theme_name": "My Theme",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        metadata = (
            fresh_addon
            / "src/collective/mypackage/profiles/default/metadata.xml"
        )
        assert_file_exists(
            metadata,
            content_contains=(
                "<dependency>profile-plone.app.theming:default</dependency>"
            ),
        )

    def test_theming_dependency_added_exactly_once(self, fresh_addon, theme_barceloneta_template):
        for _ in range(2):
            result = apply_subtemplate(
                theme_barceloneta_template,
                fresh_addon,
                data={
                    "theme_name": "My Theme",
                    "package_name": "collective.mypackage",
                },
            )
            assert result.returncode == 0, f"copier failed: {result.stderr}"
        content = (
            fresh_addon
            / "src/collective/mypackage/profiles/default/metadata.xml"
        ).read_text()
        assert content.count("profile-plone.app.theming:default") == 1
