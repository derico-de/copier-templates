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

    def test_camelcase_name_snake_case_module(self, addon_dir, content_type_template):
        """CamelCase names produce a snake_case module (bobtemplates parity)."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "MyContentType"},
        )

        ct_file = addon_dir / "src/collective/mypackage/content/my_content_type.py"
        assert_file_exists(ct_file, content_contains="IMyContentType")

    def test_multiword_name_snake_case_module(self, addon_dir, content_type_template):
        """Multi-word names keep their word boundaries ('Todo task' -> todo_task)."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Todo task"},
        )

        ct_file = addon_dir / "src/collective/mypackage/content/todo_task.py"
        assert_file_exists(ct_file)

    def test_creates_supermodel_xml_stub(self, addon_dir, content_type_template):
        """Content type ships a content-local supermodel XML stub (bobtemplates parity)."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "News Item"},
        )

        xml_file = addon_dir / "src/collective/mypackage/content/news_item.xml"
        assert_file_exists(
            xml_file,
            content_contains="http://namespaces.plone.org/supermodel/schema",
        )


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
                "activate_default_behaviors": False,
                "enable_dublin_core": False,
            },
        )

        fti_file = addon_dir / "src/collective/mypackage/profiles/default/types/Simple.xml"
        content = fti_file.read_text()
        assert "plone.dublincore" not in content

    def test_not_global_allow_updates_parent_fti(self, addon_dir, content_type_template):
        """When global_allow=False, parent FTI's allowed_content_types is updated."""
        # Step 1: create a parent container type
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Library"},
        )

        # Step 2: add a child type that is not globally addable, parented to Library
        run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": "Book",
                "global_allow": False,
                "parent_content_type": "Library",
            },
        )

        parent_fti = addon_dir / "src/collective/mypackage/profiles/default/types/Library.xml"
        assert_file_exists(parent_fti)
        content = parent_fti.read_text()
        assert '<element value="Book"' in content
        assert 'allowed_content_types' in content

        # Child's own FTI records global_allow=False
        child_fti = addon_dir / "src/collective/mypackage/profiles/default/types/Book.xml"
        assert '<property name="global_allow">False</property>' in child_fti.read_text()

        # Step 3: add a second child — both should appear with consistent indent
        run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": "Chapter",
                "global_allow": False,
                "parent_content_type": "Library",
            },
        )
        content = parent_fti.read_text()
        assert '<element value="Book"/>' in content
        assert '<element value="Chapter"/>' in content

    def test_not_global_allow_creates_parent_fti_override(self, addon_dir, content_type_template):
        """When parent is a default Plone type, a minimal FTI override is created."""
        run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": "Widget",
                "global_allow": False,
                "parent_content_type": "Folder",
            },
        )

        parent_fti = addon_dir / "src/collective/mypackage/profiles/default/types/Folder.xml"
        assert parent_fti.exists(), "Minimal FTI override should be created"
        content = parent_fti.read_text()
        assert 'name="Folder"' in content
        assert 'purge="False"' in content
        assert '<element value="Widget"/>' in content

    def test_not_global_allow_test_uses_parent_container(
        self, addon_dir, content_type_template
    ):
        """Generated test creates a parent and asserts addability when not global."""
        run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": "Book",
                "global_allow": False,
                "parent_content_type": "Folder",
            },
        )
        content = (addon_dir / "src/collective/mypackage/tests/test_ct_book.py").read_text()
        assert 'type="Folder"' in content
        assert "self.container = api.content.create(" in content
        assert "container=self.container," in content
        assert "def test_addable_in_parent" in content
        assert "allowedContentTypes()" in content

    def test_global_allow_test_uses_portal(
        self, addon_dir, content_type_template
    ):
        """Generated test creates directly in the portal when globally addable."""
        run_copier(
            content_type_template,
            addon_dir,
            data={"content_type_name": "Article", "global_allow": True},
        )
        content = (addon_dir / "src/collective/mypackage/tests/test_ct_article.py").read_text()
        assert "self.container = self.portal" in content
        assert "def test_addable_in_parent" not in content

    def test_disable_navigation(self, addon_dir, content_type_template):
        """Content type without navigation behavior."""
        run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": "Hidden",
                "activate_default_behaviors": False,
                "enable_navigation": False,
            },
        )

        fti_file = addon_dir / "src/collective/mypackage/profiles/default/types/Hidden.xml"
        content = fti_file.read_text()
        assert "plone.excludefromnavigation" not in content


class TestContentTypeProfileWiring:
    """metadata.xml dependency, versioning and diff-tool wiring."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        pkg_dir = temp_dir / "mypackage"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.mypackage"},
        )
        return pkg_dir

    def _apply(self, addon_dir, content_type_template, name="Task"):
        result = run_copier(
            content_type_template,
            addon_dir,
            data={
                "content_type_name": name,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def _profile(self, addon_dir):
        return addon_dir / "src/collective/mypackage/profiles/default"

    def test_metadata_gains_dexterity_dependency(
        self, addon_dir, content_type_template
    ):
        self._apply(addon_dir, content_type_template)
        metadata = self._profile(addon_dir) / "metadata.xml"
        assert_file_exists(
            metadata,
            content_contains=(
                "<dependency>profile-plone.app.dexterity:default</dependency>"
            ),
        )

    def test_metadata_dependency_added_exactly_once(
        self, addon_dir, content_type_template
    ):
        self._apply(addon_dir, content_type_template, name="Task")
        self._apply(addon_dir, content_type_template, name="Note")
        content = (self._profile(addon_dir) / "metadata.xml").read_text()
        assert content.count("profile-plone.app.dexterity:default") == 1

    def test_repositorytool_registers_versioning_policies(
        self, addon_dir, content_type_template
    ):
        self._apply(addon_dir, content_type_template)
        repo = self._profile(addon_dir) / "repositorytool.xml"
        assert_file_exists(
            repo,
            content_contains=[
                '<type name="Task">',
                '<policy name="at_edit_autoversion"/>',
                '<policy name="version_on_revert"/>',
            ],
        )

    def test_difftool_registers_compound_diff(
        self, addon_dir, content_type_template
    ):
        self._apply(addon_dir, content_type_template)
        diff = self._profile(addon_dir) / "diff_tool.xml"
        assert_file_exists(
            diff,
            content_contains=[
                '<type portal_type="Task">',
                'difftype="Compound Diff for Dexterity types"',
            ],
        )

    def test_second_type_added_to_existing_files(
        self, addon_dir, content_type_template
    ):
        self._apply(addon_dir, content_type_template, name="Task")
        self._apply(addon_dir, content_type_template, name="Note")
        repo = (self._profile(addon_dir) / "repositorytool.xml").read_text()
        diff = (self._profile(addon_dir) / "diff_tool.xml").read_text()
        assert '<type name="Task">' in repo
        assert '<type name="Note">' in repo
        assert '<type portal_type="Task">' in diff
        assert '<type portal_type="Note">' in diff

    def test_rerun_adds_no_duplicates(self, addon_dir, content_type_template):
        self._apply(addon_dir, content_type_template, name="Task")
        self._apply(addon_dir, content_type_template, name="Task")
        repo = (self._profile(addon_dir) / "repositorytool.xml").read_text()
        diff = (self._profile(addon_dir) / "diff_tool.xml").read_text()
        assert repo.count('<type name="Task">') == 1
        assert diff.count('<type portal_type="Task">') == 1

    def test_profile_xml_files_are_wellformed(
        self, addon_dir, content_type_template
    ):
        import xml.etree.ElementTree as ET

        self._apply(addon_dir, content_type_template, name="Task")
        self._apply(addon_dir, content_type_template, name="Note")
        profile = self._profile(addon_dir)
        for name in ("metadata.xml", "repositorytool.xml", "diff_tool.xml"):
            ET.parse(profile / name)
