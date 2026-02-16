"""Tests for content_type subtemplate."""
import pytest

from helpers import assert_file_exists, read_toml, run_copier


class TestContentTypeRequiresAddon:
    """Content type subtemplate requires parent addon."""

    def test_fails_without_parent_addon(self, temp_dir, content_type_template):
        """Content type fails if no parent addon detected."""
        result = run_copier(
            content_type_template,
            temp_dir,  # No addon here
            data={"content_type_name": "Document"},
        )
        assert result.returncode != 0
        # Copier 9.x fails with "package_name is required" before custom validation
        error_msg = result.stderr.lower()
        assert (
            "parent addon" in error_msg
            or "no parent addon" in error_msg
            or "package_name" in error_msg
        )

    def test_succeeds_with_parent_addon(self, temp_dir, backend_addon_template, content_type_template):
        """Content type succeeds when parent addon exists."""
        # First create parent addon
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        # Then add content type
        result = run_copier(
            content_type_template,
            temp_dir / "mypackage",
            data={"content_type_name": "News Item"},
        )
        assert result.returncode == 0, f"Copier failed: {result.stderr}"

        # Verify content type created
        ct_file = temp_dir / "mypackage/src/collective/mypackage/content/news_item.py"
        assert_file_exists(ct_file)


class TestContentTypeCreation:
    """Test content type file creation."""

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

    def test_creates_content_module(self, addon_dir, content_type_template):
        """Content type creates content module."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Article"},
        )

        ct_file = addon_dir / "src/collective/mypackage/content/article.py"
        assert_file_exists(ct_file)

    def test_creates_content_init(self, addon_dir, content_type_template):
        """Content type creates content __init__.py."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Article"},
        )

        init_file = addon_dir / "src/collective/mypackage/content/__init__.py"
        assert_file_exists(init_file)

    def test_creates_content_configure_zcml(self, addon_dir, content_type_template):
        """Content type creates content configure.zcml."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Article"},
        )

        zcml_file = addon_dir / "src/collective/mypackage/content/configure.zcml"
        assert_file_exists(zcml_file)

    def test_content_type_has_schema(self, addon_dir, content_type_template):
        """Content type file contains schema interface."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Article"},
        )

        ct_file = addon_dir / "src/collective/mypackage/content/article.py"
        assert_file_exists(ct_file, content_contains="IArticle")

    def test_content_type_handles_spaces(self, addon_dir, content_type_template):
        """Content type handles names with spaces."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "News Item"},
        )

        ct_file = addon_dir / "src/collective/mypackage/content/news_item.py"
        assert_file_exists(ct_file, content_contains="INewsItem")


class TestContentTypeIntegration:
    """Test content type registers in parent addon."""

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

    def test_updates_addon_settings(self, addon_dir, content_type_template):
        """Content type registered in addon settings."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Article"},
        )

        pyproject = addon_dir / "pyproject.toml"
        data = read_toml(pyproject)
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"]["subtemplates"]
        assert "Article" in subtemplates["content_types"]

    def test_adds_parent_zcml_include(self, addon_dir, content_type_template):
        """Content type adds include to parent configure.zcml."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Article"},
        )

        parent_zcml = addon_dir / "src/my/pkg/configure.zcml"
        assert_file_exists(parent_zcml, content_contains='<include package=".content" />')


class TestContentTypeEdgeCases:
    """Test content type edge cases and options."""

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

    def test_creates_fti_xml(self, addon_dir, content_type_template):
        """Content type creates FTI XML file."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Article"},
        )

        fti_file = addon_dir / "src/collective/mypackage/profiles/default/types/Article.xml"
        assert_file_exists(fti_file, content_contains=[
            'name="Article"',
            'meta_type="Dexterity FTI"',
        ])

    def test_fti_xml_has_correct_klass(self, addon_dir, content_type_template):
        """FTI XML references the correct Python class."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Article"},
        )

        fti_file = addon_dir / "src/collective/mypackage/profiles/default/types/Article.xml"
        assert_file_exists(fti_file, content_contains=[
            "collective.mypackage.content.article.Article",
            "collective.mypackage.content.article.IArticle",
        ])

    def test_content_type_base_item(self, addon_dir, content_type_template):
        """Content type with Item base class."""
        run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": "Document",
                "content_type_base": "Item",
            },
        )

        ct_file = addon_dir / "src/collective/mypackage/content/document.py"
        assert_file_exists(ct_file, content_contains=["Item", "IDocument"])

    def test_disable_dublin_core(self, addon_dir, content_type_template):
        """Content type without Dublin Core behavior."""
        run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": "Simple",
                "enable_dublin_core": False,
            },
        )

        fti_file = addon_dir / "src/collective/mypackage/profiles/default/types/Simple.xml"
        content = fti_file.read_text()
        assert "plone.dublincore" not in content

    def test_disable_navigation(self, addon_dir, content_type_template):
        """Content type without navigation behavior."""
        run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": "Hidden",
                "enable_navigation": False,
            },
        )

        fti_file = addon_dir / "src/collective/mypackage/profiles/default/types/Hidden.xml"
        content = fti_file.read_text()
        assert "plone.excludefromnavigation" not in content
