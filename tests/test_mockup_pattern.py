"""Tests for the mockup_pattern subtemplate.

Mirrors bobtemplates.plone mockup_pattern — a JavaScript pattern package
scaffold (pattern source + webpack/babel/eslint/jest configs + package.json).

This minimal port generates a structurally-aligned JS scaffold inside an
existing backend_addon; it is not a literal 1:1 copy of every upstream
config file.
"""
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestMockupPatternRequiresAddon:
    def test_fails_without_parent_addon(
        self, temp_dir, mockup_pattern_template
    ):
        result = run_copier(
            mockup_pattern_template,
            temp_dir,
            data={"pattern_name": "my-pattern"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestMockupPatternCreation:
    def _apply(self, fresh_addon, mockup_pattern_template, **extra):
        data = {
            "pattern_name": "my-pattern",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(
            mockup_pattern_template, fresh_addon, data=data
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_pattern_source(
        self, fresh_addon, mockup_pattern_template
    ):
        self._apply(fresh_addon, mockup_pattern_template)
        src = (
            fresh_addon
            / "src/collective/mypackage/patterns/pat-my-pattern.js"
        )
        assert_file_exists(
            src,
            content_contains=[
                "pat-my-pattern",
                "Base.extend",
            ],
        )

    def test_creates_demo_page(self, fresh_addon, mockup_pattern_template):
        """bobtemplates parity: the demo page filename is fixed."""
        self._apply(fresh_addon, mockup_pattern_template)
        assert_file_exists(
            fresh_addon / "src/collective/mypackage/browser/pattern-demo.pt",
            content_contains="pat-my-pattern",
        )

    def test_creates_package_json(self, fresh_addon, mockup_pattern_template):
        self._apply(fresh_addon, mockup_pattern_template)
        pkg = fresh_addon / "src/collective/mypackage/patterns/package.json"
        assert_file_exists(pkg, content_contains='"name"')

    def test_creates_webpack_config(
        self, fresh_addon, mockup_pattern_template
    ):
        self._apply(fresh_addon, mockup_pattern_template)
        wp = (
            fresh_addon
            / "src/collective/mypackage/patterns/webpack.config.js"
        )
        assert_file_exists(wp, content_contains="module.exports")

    def test_creates_babel_config(self, fresh_addon, mockup_pattern_template):
        self._apply(fresh_addon, mockup_pattern_template)
        babel = fresh_addon / "src/collective/mypackage/patterns/babel.config.js"
        assert_file_exists(babel)


class TestMockupPatternIntegration:
    def test_registers_in_pyproject(
        self, fresh_addon, mockup_pattern_template
    ):
        result = apply_subtemplate(
            mockup_pattern_template,
            fresh_addon,
            data={
                "pattern_name": "search-box",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "search-box" in subtemplates["mockup_patterns"]
