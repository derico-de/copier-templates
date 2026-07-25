"""Tests for the controlpanel subtemplate.

Mirrors bobtemplates.plone controlpanel. Generates:
  src/<pkg>/controlpanels/__init__.py
  src/<pkg>/controlpanels/<module>.py     (settings schema + form wrapper)
  src/<pkg>/controlpanels/configure.zcml  (browser:page registration)
  src/<pkg>/profiles/default/controlpanel.xml  (GS controlpanel entry)
  src/<pkg>/profiles/default/registry/<module>.xml  (registry records)
"""
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestControlpanelRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, controlpanel_template):
        result = run_copier(
            controlpanel_template,
            temp_dir,
            data={"controlpanel_name": "MyFeatured"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestControlpanelCreation:
    def _apply(self, fresh_addon, controlpanel_template, **extra):
        data = {
            "controlpanel_name": "MyFeatured",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(
            controlpanel_template, fresh_addon, data=data
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_controlpanels_init(
        self, fresh_addon, controlpanel_template
    ):
        self._apply(fresh_addon, controlpanel_template)
        assert_file_exists(
            fresh_addon / "src/collective/mypackage/controlpanels/__init__.py"
        )

    def test_creates_controlpanel_module(
        self, fresh_addon, controlpanel_template
    ):
        self._apply(fresh_addon, controlpanel_template)
        module = (
            fresh_addon
            / "src/collective/mypackage/controlpanels/my_featured.py"
        )
        assert_file_exists(
            module,
            content_contains=[
                "class IMyFeaturedSettings",
                "class MyFeaturedControlPanelForm",
                "RegistryEditForm",
                "ControlPanelFormWrapper",
            ],
        )

    def test_creates_controlpanel_configure_zcml(
        self, fresh_addon, controlpanel_template
    ):
        self._apply(fresh_addon, controlpanel_template)
        zcml = (
            fresh_addon
            / "src/collective/mypackage/controlpanels/configure.zcml"
        )
        assert_file_exists(
            zcml,
            content_contains=[
                "<browser:page",
                'name="my-featured-controlpanel"',
                "MyFeaturedControlPanelView",
            ],
        )

    def test_creates_controlpanel_xml(self, fresh_addon, controlpanel_template):
        self._apply(fresh_addon, controlpanel_template)
        xml = (
            fresh_addon
            / "src/collective/mypackage/profiles/default/controlpanel.xml"
        )
        assert_file_exists(
            xml,
            content_contains=[
                "my-featured-controlpanel",
                "MyFeatured",
            ],
        )

    def test_creates_registry_xml(self, fresh_addon, controlpanel_template):
        self._apply(fresh_addon, controlpanel_template)
        reg = (
            fresh_addon
            / "src/collective/mypackage/profiles/default/registry/my_featured.xml"
        )
        assert_file_exists(reg, content_contains="IMyFeaturedSettings")


class TestControlpanelIntegration:
    def _apply(self, fresh_addon, controlpanel_template, name="MyFeatured"):
        result = apply_subtemplate(
            controlpanel_template,
            fresh_addon,
            data={
                "controlpanel_name": name,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_registers_in_pyproject(self, fresh_addon, controlpanel_template):
        self._apply(fresh_addon, controlpanel_template)
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "MyFeatured" in subtemplates["controlpanels"]

    def test_adds_parent_zcml_include(
        self, fresh_addon, controlpanel_template
    ):
        self._apply(fresh_addon, controlpanel_template)
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert_file_exists(
            parent_zcml,
            content_contains='<include package=".controlpanels" />',
        )

    def test_parent_include_not_duplicated_on_rerun(
        self, fresh_addon, controlpanel_template
    ):
        self._apply(fresh_addon, controlpanel_template, name="MyFeatured")
        self._apply(fresh_addon, controlpanel_template, name="OtherSettings")
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert parent_zcml.read_text().count(
            '<include package=".controlpanels" />'
        ) == 1


class TestControlpanelProfileMerge:
    """controlpanel.xml is merged idempotently (bobtemplates parity)."""

    def _apply(self, fresh_addon, controlpanel_template, name="MyFeatured", **extra):
        data = {
            "controlpanel_name": name,
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(
            controlpanel_template, fresh_addon, data=data
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def _controlpanel_xml(self, fresh_addon):
        return (
            fresh_addon
            / "src/collective/mypackage/profiles/default/controlpanel.xml"
        )

    def test_two_configlets_coexist(self, fresh_addon, controlpanel_template):
        self._apply(fresh_addon, controlpanel_template, name="MyFeatured")
        self._apply(fresh_addon, controlpanel_template, name="OtherPanel")
        content = self._controlpanel_xml(fresh_addon).read_text()
        assert 'action_id="my-featured-controlpanel"' in content
        assert 'action_id="other-panel-controlpanel"' in content

    def test_rerun_adds_no_duplicates(
        self, fresh_addon, controlpanel_template
    ):
        self._apply(fresh_addon, controlpanel_template, name="MyFeatured")
        self._apply(fresh_addon, controlpanel_template, name="MyFeatured")
        content = self._controlpanel_xml(fresh_addon).read_text()
        assert content.count('action_id="my-featured-controlpanel"') == 1

    def test_hostile_title_stays_wellformed(
        self, fresh_addon, controlpanel_template
    ):
        import xml.etree.ElementTree as ET

        self._apply(
            fresh_addon,
            controlpanel_template,
            name="MyFeatured",
            controlpanel_title='Featured & <special> "panel"',
        )
        ET.parse(self._controlpanel_xml(fresh_addon))
