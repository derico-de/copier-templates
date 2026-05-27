"""Tests for the language subtemplate.

Adds a translation locale (``locales/<code>/LC_MESSAGES/<domain>.po``) to an
existing backend addon.
"""
from helpers import apply_subtemplate, assert_file_exists, run_copier


class TestLanguageRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, language_template):
        result = run_copier(
            language_template,
            temp_dir,  # No addon here
            data={"language_code": "de"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestLanguageCreation:
    def _apply(self, fresh_addon, language_template, **extra):
        data = {"language_code": "de", "package_name": "collective.mypackage"}
        data.update(extra)
        result = apply_subtemplate(language_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_po_catalog(self, fresh_addon, language_template):
        self._apply(fresh_addon, language_template)
        po = (
            fresh_addon
            / "src/collective/mypackage/locales/de/LC_MESSAGES/collective.mypackage.po"
        )
        assert_file_exists(po, content_contains="Language-Code: de")
        assert_file_exists(po, content_contains="Domain: collective.mypackage")

    def test_language_name_recorded(self, fresh_addon, language_template):
        self._apply(fresh_addon, language_template, language_name="German")
        po = (
            fresh_addon
            / "src/collective/mypackage/locales/de/LC_MESSAGES/collective.mypackage.po"
        )
        assert_file_exists(po, content_contains="Language-Name: German")

    def test_addon_has_message_factory(self, fresh_addon, language_template):
        """The addon ships an i18n module with a MessageFactory (not in __init__)."""
        i18n = fresh_addon / "src/collective/mypackage/i18n.py"
        assert_file_exists(i18n, content_contains='MessageFactory("collective.mypackage")')
        init = fresh_addon / "src/collective/mypackage/__init__.py"
        assert "MessageFactory" not in init.read_text()
