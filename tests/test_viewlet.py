"""Tests for the viewlet subtemplate.

Mirrors bobtemplates.plone viewlet. Generates:
  src/<pkg>/viewlets/__init__.py
  src/<pkg>/viewlets/<module>.py       (ViewletBase subclass)
  src/<pkg>/viewlets/<template-name>.pt  (optional, dash-separated)
  src/<pkg>/viewlets/configure.zcml    (browser:viewlet registration)
"""
import pytest
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestViewletRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, viewlet_template):
        result = run_copier(
            viewlet_template,
            temp_dir,
            data={"viewlet_name": "myviewlet"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestViewletCreation:
    def _apply(self, fresh_addon, viewlet_template, **extra):
        data = {
            "viewlet_name": "myviewlet",
            "viewlet_class_name": "MyViewlet",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(viewlet_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_viewlets_init(self, fresh_addon, viewlet_template):
        self._apply(fresh_addon, viewlet_template)
        assert_file_exists(
            fresh_addon / "src/collective/mypackage/viewlets/__init__.py"
        )

    def test_creates_viewlet_module(self, fresh_addon, viewlet_template):
        self._apply(fresh_addon, viewlet_template)
        module = fresh_addon / "src/collective/mypackage/viewlets/myviewlet.py"
        assert_file_exists(
            module,
            content_contains=[
                "class MyViewlet",
                "ViewletBase",
                'ViewPageTemplateFile("my-viewlet.pt")',
            ],
        )

    def test_creates_viewlet_template(self, fresh_addon, viewlet_template):
        self._apply(fresh_addon, viewlet_template)
        pt = fresh_addon / "src/collective/mypackage/viewlets/my-viewlet.pt"
        assert_file_exists(pt)

    def test_creates_viewlet_configure_zcml(self, fresh_addon, viewlet_template):
        self._apply(fresh_addon, viewlet_template)
        zcml = fresh_addon / "src/collective/mypackage/viewlets/configure.zcml"
        assert_file_exists(
            zcml,
            content_contains=[
                "<browser:viewlet",
                'name="myviewlet"',
                ".myviewlet.MyViewlet",
            ],
        )


class TestViewletIntegration:
    def _apply(
        self,
        fresh_addon,
        viewlet_template,
        name="myviewlet",
        class_name="MyViewlet",
    ):
        result = apply_subtemplate(
            viewlet_template,
            fresh_addon,
            data={
                "viewlet_name": name,
                "viewlet_class_name": class_name,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_registers_in_pyproject(self, fresh_addon, viewlet_template):
        self._apply(fresh_addon, viewlet_template)
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "myviewlet" in subtemplates["viewlets"]

    def test_adds_parent_zcml_include(self, fresh_addon, viewlet_template):
        self._apply(fresh_addon, viewlet_template)
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert_file_exists(
            parent_zcml,
            content_contains='<include package=".viewlets" />',
        )

    def test_parent_include_not_duplicated_on_rerun(
        self, fresh_addon, viewlet_template
    ):
        self._apply(
            fresh_addon, viewlet_template, name="first", class_name="First"
        )
        self._apply(
            fresh_addon, viewlet_template, name="second", class_name="Second"
        )
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert parent_zcml.read_text().count(
            '<include package=".viewlets" />'
        ) == 1


class TestViewletEdgeCases:
    def test_without_template(self, fresh_addon, viewlet_template):
        result = apply_subtemplate(
            viewlet_template,
            fresh_addon,
            data={
                "viewlet_name": "tplless",
                "viewlet_class_name": "TplLess",
                "viewlet_template": False,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        pt = fresh_addon / "src/collective/mypackage/viewlets/tpl-less.pt"
        assert not pt.exists()

    @pytest.mark.parametrize(
        "manager",
        [
            "plone.portalheader",
            "plone.portalfooter",
            "plone.abovecontent",
            "plone.belowcontent",
        ],
    )
    def test_different_managers(self, fresh_addon, viewlet_template, manager):
        result = apply_subtemplate(
            viewlet_template,
            fresh_addon,
            data={
                "viewlet_name": "myviewlet",
                "viewlet_class_name": "MyViewlet",
                "viewlet_manager": manager,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        zcml = fresh_addon / "src/collective/mypackage/viewlets/configure.zcml"
        assert manager in zcml.read_text()
