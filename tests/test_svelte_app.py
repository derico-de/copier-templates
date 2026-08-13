"""Tests for the svelte_app subtemplate.

Mirrors bobtemplates.plone svelte_app — a Svelte application scaffold
packaged alongside an existing backend_addon. Minimal port: enough to
build a Svelte entry point with Vite, plus the Python-side registration.
"""
import json
import subprocess

import pytest
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestSvelteAppRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, svelte_app_template):
        result = run_copier(
            svelte_app_template,
            temp_dir,
            data={"svelte_app_name": "my-svelte-app"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestSvelteAppValidation:
    def test_rejects_invalid_app_name(
        self, fresh_addon, svelte_app_template
    ):
        result = apply_subtemplate(
            svelte_app_template,
            fresh_addon,
            data={
                "package_name": "collective.mypackage",
                "svelte_app_name": "Invalid App",
            },
        )

        assert result.returncode != 0
        assert "lowercase kebab-case" in result.stderr
        assert not (fresh_addon / "svelte_src").exists()

    def test_custom_element_name_requires_hyphen(
        self, fresh_addon, svelte_app_template
    ):
        result = apply_subtemplate(
            svelte_app_template,
            fresh_addon,
            data={
                "package_name": "collective.mypackage",
                "svelte_app_name": "dashboard",
                "svelte_app_custom_element": True,
            },
        )

        assert result.returncode != 0
        assert "must contain a hyphen" in result.stderr
        assert not (fresh_addon / "svelte_src").exists()

    def test_rejects_reserved_custom_element_name(
        self, fresh_addon, svelte_app_template
    ):
        result = apply_subtemplate(
            svelte_app_template,
            fresh_addon,
            data={
                "package_name": "collective.mypackage",
                "svelte_app_name": "font-face",
                "svelte_app_custom_element": True,
            },
        )

        assert result.returncode != 0
        assert "reserved by HTML" in result.stderr
        assert not (fresh_addon / "svelte_src").exists()


class TestSvelteAppCreation:
    def _apply(self, fresh_addon, svelte_app_template, **extra):
        data = {
            "svelte_app_name": "my-svelte-app",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(
            svelte_app_template, fresh_addon, data=data
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_svelte_main_component(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(fresh_addon, svelte_app_template)
        app = (
            fresh_addon
            / "svelte_src/my-svelte-app/src/App.svelte"
        )
        assert_file_exists(
            app,
            content_contains=["<script>", "$props()", "$state(0)", "onclick="],
        )
        assert "on:click=" not in app.read_text()

    def test_creates_svelte_entry_point(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(fresh_addon, svelte_app_template)
        main = fresh_addon / "svelte_src/my-svelte-app/src/main.js"
        assert_file_exists(
            main,
            content_contains=[
                'import { mount } from "svelte"',
                "import App",
                "mount(App, { target })",
            ],
        )
        assert "new App" not in main.read_text()
        index = fresh_addon / "svelte_src/my-svelte-app/index.html"
        assert_file_exists(
            index,
            content_contains=[
                '<div id="my-svelte-app"></div>',
                '<script type="module" src="/src/main.js"></script>',
            ],
        )

    def test_creates_svelte_package_json(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(fresh_addon, svelte_app_template)
        pkg = fresh_addon / "svelte_src/my-svelte-app/package.json"
        data = json.loads(pkg.read_text())

        assert data["private"] is True
        assert data["scripts"] == {"dev": "vite", "build": "vite build"}
        assert data["devDependencies"] == {
            "@sveltejs/vite-plugin-svelte": "^7.3.0",
            "svelte": "^5.56.9",
            "vite": "^8.2.1",
        }
        assert data["engines"]["node"] == "^20.19.0 || >=22.12.0"

    def test_escapes_description_for_json_and_svelte(
        self, fresh_addon, svelte_app_template
    ):
        description = 'A "quoted" app with <markup> and {braces}'
        self._apply(
            fresh_addon,
            svelte_app_template,
            svelte_app_description=description,
        )
        app_dir = fresh_addon / "svelte_src/my-svelte-app"

        package_data = json.loads((app_dir / "package.json").read_text())
        assert package_data["description"] == description
        app_source = (app_dir / "src/App.svelte").read_text()
        assert (
            'const description = "A \\"quoted\\" app with '
            '\\u003cmarkup\\u003e and {braces}";'
        ) in app_source
        assert "<p>{description}</p>" in app_source

    def test_creates_svelte_and_vite_config(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(fresh_addon, svelte_app_template)
        config_dir = fresh_addon / "svelte_src/my-svelte-app"
        assert_file_exists(
            config_dir / "svelte.config.js",
            content_contains="customElement: false",
        )
        assert_file_exists(
            config_dir / "vite.config.js",
            content_contains=[
                "plugins: [svelte()]",
                'entry: "src/main.js"',
                'name: "MySvelteApp"',
                'formats: ["iife"]',
                'fileName: () => "my-svelte-app-bundle.js"',
                'cssFileName: "my-svelte-app-bundle"',
            ],
        )

    def test_custom_element_uses_svelte_registration(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(
            fresh_addon,
            svelte_app_template,
            svelte_app_custom_element=True,
        )
        app_dir = fresh_addon / "svelte_src/my-svelte-app"
        assert_file_exists(
            app_dir / "svelte.config.js",
            content_contains="customElement: true",
        )
        assert_file_exists(
            app_dir / "src/App.svelte",
            content_contains=(
                '<svelte:options customElement="my-svelte-app" />'
            ),
        )
        assert (app_dir / "src/main.js").read_text() == (
            'import "./App.svelte";\n'
        )
        assert_file_exists(
            app_dir / "index.html",
            content_contains="<my-svelte-app></my-svelte-app>",
        )
        mount = (
            fresh_addon
            / "src/collective/mypackage/svelte_apps/my_svelte_app.pt"
        )
        assert_file_exists(
            mount,
            content_contains="<my-svelte-app></my-svelte-app>",
        )
        registry = (
            fresh_addon
            / "src/collective/mypackage/profiles/default/registry/my_svelte_app.xml"
        )
        assert "csscompilation" not in registry.read_text()

    @pytest.mark.integration
    @pytest.mark.parametrize("custom_element", [False, True])
    def test_frontend_builds(
        self,
        fresh_addon,
        svelte_app_template,
        custom_element,
    ):
        app_name = "custom-app" if custom_element else "standard-app"
        self._apply(
            fresh_addon,
            svelte_app_template,
            svelte_app_name=app_name,
            svelte_app_custom_element=custom_element,
        )
        app_dir = fresh_addon / f"svelte_src/{app_name}"

        subprocess.run(
            ["npm", "install", "--no-audit", "--no-fund"],
            cwd=app_dir,
            check=True,
        )
        subprocess.run(["npm", "run", "build"], cwd=app_dir, check=True)

        output_dir = (
            fresh_addon
            / f"src/collective/mypackage/svelte_apps/static/{app_name}"
        )
        assert (output_dir / f"{app_name}-bundle.js").is_file()
        assert (output_dir / f"{app_name}-bundle.css").is_file() is (
            not custom_element
        )

    def test_creates_python_mount_view(
        self, fresh_addon, svelte_app_template
    ):
        """A tiny Python view that serves as the mount point for the Svelte app."""
        self._apply(fresh_addon, svelte_app_template)
        mount = (
            fresh_addon
            / "src/collective/mypackage/svelte_apps/my_svelte_app.py"
        )
        assert_file_exists(
            mount, content_contains="class MySvelteAppView"
        )


class TestSvelteAppIntegration:
    def test_registers_in_pyproject(self, fresh_addon, svelte_app_template):
        result = apply_subtemplate(
            svelte_app_template,
            fresh_addon,
            data={
                "svelte_app_name": "dashboard-ui",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "dashboard-ui" in subtemplates["svelte_apps"]


class TestSvelteStaticResource:
    """The bundle directory is registered as a plone static resource."""

    def _apply(self, fresh_addon, svelte_app_template):
        result = apply_subtemplate(
            svelte_app_template,
            fresh_addon,
            data={
                "svelte_app_name": "my-app",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_parent_zcml_registers_static_directory_and_view(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(fresh_addon, svelte_app_template)
        package_dir = fresh_addon / "src/collective/mypackage"
        parent_zcml = package_dir / "configure.zcml"
        assert_file_exists(
            parent_zcml,
            content_contains=[
                "<plone:static",
                'directory="svelte_apps/static"',
                'name="collective.mypackage.svelte"',
                '<include package=".svelte_apps" />',
            ],
        )
        assert_file_exists(
            package_dir / "svelte_apps/configure.zcml",
            content_contains=[
                "<browser:page",
                'name="my-app"',
                'class=".my_app.MyAppView"',
                'permission="zope2.View"',
                'layer="collective.mypackage.interfaces.ICollectiveMypackageLayer"',
            ],
        )

    def test_static_registration_not_duplicated_on_rerun(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(fresh_addon, svelte_app_template)
        self._apply(fresh_addon, svelte_app_template)
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        content = parent_zcml.read_text()
        assert content.count('name="collective.mypackage.svelte"') == 1
        assert content.count('<include package=".svelte_apps" />') == 1
        views_zcml = (
            fresh_addon
            / "src/collective/mypackage/svelte_apps/configure.zcml"
        ).read_text()
        assert views_zcml.count('name="my-app"') == 1

    def test_static_directory_shipped(self, fresh_addon, svelte_app_template):
        self._apply(fresh_addon, svelte_app_template)
        static_dir = (
            fresh_addon / "src/collective/mypackage/svelte_apps/static"
        )
        assert static_dir.is_dir()

    def test_vite_builds_bundle_names_registry_expects(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(fresh_addon, svelte_app_template)
        vite_config = fresh_addon / "svelte_src/my-app/vite.config.js"
        assert_file_exists(
            vite_config,
            content_contains=[
                'fileName: () => "my-app-bundle.js"',
                'cssFileName: "my-app-bundle"',
            ],
        )
