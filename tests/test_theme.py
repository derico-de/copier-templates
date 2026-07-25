"""Tests for the theme subtemplate.

Mirrors bobtemplates.plone theme — the full theme variant. Shares the
theme_basic layout but adds a webpack.config.js and a
scss/_variables.scss partial.
"""
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestThemeRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, theme_template):
        result = run_copier(
            theme_template,
            temp_dir,
            data={"theme_name": "My Theme"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestThemeCreation:
    def _apply(self, fresh_addon, theme_template, **extra):
        data = {
            "theme_name": "My Theme",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(theme_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_manifest(self, fresh_addon, theme_template):
        self._apply(fresh_addon, theme_template)
        manifest = fresh_addon / "src/collective/mypackage/theme/manifest.cfg"
        assert_file_exists(manifest, content_contains="[theme]")

    def test_creates_rules_xml(self, fresh_addon, theme_template):
        self._apply(fresh_addon, theme_template)
        rules = fresh_addon / "src/collective/mypackage/theme/rules.xml"
        assert_file_exists(rules, content_contains="diazo")

    def test_creates_theme_scss(self, fresh_addon, theme_template):
        self._apply(fresh_addon, theme_template)
        scss = fresh_addon / "src/collective/mypackage/theme/styles/theme.scss"
        assert_file_exists(scss, content_contains="variables")

    def test_creates_theme_profile_xml(self, fresh_addon, theme_template):
        self._apply(fresh_addon, theme_template)
        xml = fresh_addon / "src/collective/mypackage/profiles/default/theme.xml"
        assert_file_exists(xml, content_contains="my-theme")

    def test_creates_tinymce_registry(self, fresh_addon, theme_template):
        self._apply(fresh_addon, theme_template)
        reg = fresh_addon / "src/collective/mypackage/profiles/default/registry/tinymce.xml"
        assert_file_exists(reg, content_contains="bs-pricing.html")


class TestThemeIntegration:
    def test_registers_in_pyproject(self, fresh_addon, theme_template):
        result = apply_subtemplate(
            theme_template,
            fresh_addon,
            data={
                "theme_name": "Full Theme",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "Full Theme" in subtemplates["themes"]

    def test_registers_plone_static_in_parent_zcml(
        self, fresh_addon, theme_template
    ):
        result = apply_subtemplate(
            theme_template,
            fresh_addon,
            data={
                "theme_name": "My Theme",
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
                'name="my-theme"',
                'type="theme"',
            ],
        )


class TestThemeProfileDependency:
    """The generated profile depends on plone.app.theming."""

    def test_metadata_gains_theming_dependency(self, fresh_addon, theme_template):
        result = apply_subtemplate(
            theme_template,
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

    def test_theming_dependency_added_exactly_once(self, fresh_addon, theme_template):
        for _ in range(2):
            result = apply_subtemplate(
                theme_template,
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
