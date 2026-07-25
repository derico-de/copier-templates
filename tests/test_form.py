"""Tests for the form subtemplate.

Mirrors bobtemplates.plone form. Generates:
  src/<pkg>/forms/__init__.py
  src/<pkg>/forms/<form_module>.py       (z3c.form based form class)
  src/<pkg>/forms/configure.zcml         (browser:page registration)
"""
import pytest
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestFormRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, form_template):
        result = run_copier(
            form_template,
            temp_dir,
            data={"form_name": "my-form"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestFormCreation:
    def _apply(self, fresh_addon, form_template, **extra):
        data = {
            "form_name": "my-form",
            "form_class_name": "MyForm",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(form_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_forms_init(self, fresh_addon, form_template):
        self._apply(fresh_addon, form_template)
        assert_file_exists(
            fresh_addon / "src/collective/mypackage/forms/__init__.py"
        )

    def test_creates_form_module(self, fresh_addon, form_template):
        self._apply(fresh_addon, form_template)
        module = fresh_addon / "src/collective/mypackage/forms/my_form.py"
        assert_file_exists(
            module,
            content_contains=[
                "class MyForm",
                "from plone.autoform.form import AutoExtensibleForm",
                "form.Form",
            ],
        )

    def test_creates_form_configure_zcml(self, fresh_addon, form_template):
        self._apply(fresh_addon, form_template)
        zcml = fresh_addon / "src/collective/mypackage/forms/configure.zcml"
        assert_file_exists(
            zcml,
            content_contains=[
                "<browser:page",
                'name="my-form"',
                ".my_form.MyForm",
            ],
        )


class TestFormIntegration:
    def _apply(
        self, fresh_addon, form_template, name="my-form", class_name="MyForm"
    ):
        result = apply_subtemplate(
            form_template,
            fresh_addon,
            data={
                "form_name": name,
                "form_class_name": class_name,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_registers_in_pyproject(self, fresh_addon, form_template):
        self._apply(fresh_addon, form_template)
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "my-form" in subtemplates["forms"]

    def test_adds_parent_zcml_include(self, fresh_addon, form_template):
        self._apply(fresh_addon, form_template)
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert_file_exists(
            parent_zcml,
            content_contains='<include package=".forms" />',
        )

    def test_parent_include_not_duplicated_on_rerun(
        self, fresh_addon, form_template
    ):
        self._apply(fresh_addon, form_template, name="first", class_name="First")
        self._apply(
            fresh_addon, form_template, name="second", class_name="Second"
        )
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert parent_zcml.read_text().count(
            '<include package=".forms" />'
        ) == 1


class TestFormEdgeCases:
    @pytest.mark.parametrize(
        "for_iface",
        [
            "*",
            "plone.app.contenttypes.interfaces.IDocument",
            "plone.dexterity.interfaces.IDexterityContainer",
        ],
    )
    def test_different_for_interfaces(
        self, fresh_addon, form_template, for_iface
    ):
        result = apply_subtemplate(
            form_template,
            fresh_addon,
            data={
                "form_name": "my-form",
                "form_class_name": "MyForm",
                "form_for": for_iface,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        zcml = fresh_addon / "src/collective/mypackage/forms/configure.zcml"
        assert for_iface in zcml.read_text()


class TestFormPermissionAndLayer:
    """Forms keep the bobtemplates management permission and layer."""

    def _apply(self, fresh_addon, form_template, **extra):
        data = {"form_name": "my-form", "package_name": "collective.mypackage"}
        data.update(extra)
        result = apply_subtemplate(form_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_registration_has_manage_permission(
        self, fresh_addon, form_template
    ):
        self._apply(fresh_addon, form_template)
        zcml = fresh_addon / "src/collective/mypackage/forms/configure.zcml"
        assert_file_exists(
            zcml, content_contains='permission="cmf.ManagePortal"'
        )
        assert 'permission="zope2.View"' not in zcml.read_text()

    def test_registration_has_layer(self, fresh_addon, form_template):
        self._apply(fresh_addon, form_template)
        zcml = fresh_addon / "src/collective/mypackage/forms/configure.zcml"
        assert_file_exists(
            zcml,
            content_contains=(
                'layer="collective.mypackage.interfaces.'
                'ICollectiveMypackageLayer"'
            ),
        )

    def test_generated_test_marks_request_with_layer(
        self, fresh_addon, form_template
    ):
        self._apply(fresh_addon, form_template)
        test_file = fresh_addon / "tests/test_form_my_form.py"
        assert_file_exists(
            test_file,
            content_contains=[
                "alsoProvides",
                "ICollectiveMypackageLayer",
            ],
        )
