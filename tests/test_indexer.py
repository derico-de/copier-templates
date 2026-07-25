"""Tests for the indexer subtemplate.

Mirrors bobtemplates.plone indexer. Upstream generates:
  src/<pkg>/indexers/__init__.py
  src/<pkg>/indexers/<indexer_name>.py  (@indexer-decorated function + dummy)
  src/<pkg>/indexers/configure.zcml     (zope:adapter registrations)

Upstream questions:
  - indexer_name   (snake_case, default "my_custom_index")
"""
import pytest
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestIndexerRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, indexer_template):
        result = run_copier(
            indexer_template,
            temp_dir,
            data={"indexer_name": "my_index"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestIndexerCreation:
    def _apply(self, fresh_addon, indexer_template, **extra):
        data = {
            "indexer_name": "my_custom_index",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(indexer_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_indexers_init(self, fresh_addon, indexer_template):
        self._apply(fresh_addon, indexer_template)
        assert_file_exists(
            fresh_addon / "src/collective/mypackage/indexers/__init__.py"
        )

    def test_creates_indexer_module(self, fresh_addon, indexer_template):
        self._apply(fresh_addon, indexer_template)
        module = (
            fresh_addon / "src/collective/mypackage/indexers/my_custom_index.py"
        )
        assert_file_exists(
            module,
            content_contains=[
                "@indexer",
                "def my_custom_index",
                "from plone.indexer import indexer",
            ],
        )

    def test_creates_per_indexer_zcml(self, fresh_addon, indexer_template):
        """bobtemplates parity: adapters live in a per-indexer <name>.zcml."""
        self._apply(fresh_addon, indexer_template)
        zcml = fresh_addon / "src/collective/mypackage/indexers/my_custom_index.zcml"
        assert_file_exists(
            zcml,
            content_contains=[
                "<adapter",
                'name="my_custom_index"',
                ".my_custom_index.dummy",
                ".my_custom_index.my_custom_index",
            ],
        )

    def test_creates_indexer_configure_zcml(self, fresh_addon, indexer_template):
        self._apply(fresh_addon, indexer_template)
        zcml = fresh_addon / "src/collective/mypackage/indexers/configure.zcml"
        assert_file_exists(
            zcml,
            content_contains='<include file="my_custom_index.zcml" />',
        )


class TestIndexerIntegration:
    def _apply(self, fresh_addon, indexer_template, name="my_custom_index"):
        result = apply_subtemplate(
            indexer_template,
            fresh_addon,
            data={
                "indexer_name": name,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_registers_in_pyproject(self, fresh_addon, indexer_template):
        self._apply(fresh_addon, indexer_template)
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "my_custom_index" in subtemplates["indexers"]

    def test_adds_parent_zcml_include(self, fresh_addon, indexer_template):
        self._apply(fresh_addon, indexer_template)
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert_file_exists(
            parent_zcml,
            content_contains='<include package=".indexers" />',
        )

    def test_parent_zcml_include_not_duplicated_on_rerun(
        self, fresh_addon, indexer_template
    ):
        self._apply(fresh_addon, indexer_template, name="first_index")
        self._apply(fresh_addon, indexer_template, name="second_index")
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        content = parent_zcml.read_text()
        assert content.count('<include package=".indexers" />') == 1


class TestIndexerEdgeCases:
    @pytest.mark.parametrize(
        "name",
        ["my_index", "author_fullname", "search_score", "customField1"],
    )
    def test_accepts_various_names(self, fresh_addon, indexer_template, name):
        result = apply_subtemplate(
            indexer_template,
            fresh_addon,
            data={
                "indexer_name": name,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        module = fresh_addon / f"src/collective/mypackage/indexers/{name}.py"
        assert_file_exists(module, content_contains=f"def {name}")
