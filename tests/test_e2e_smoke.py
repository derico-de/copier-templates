"""End-to-end smoke test: a generated addon installs into Plone and passes.

Generates a backend_addon, applies the feature subtemplates (content_type,
behavior, view, form, portlet, controlpanel, restapi_service, svelte_app,
theme), syncs the generated package's environment and runs its own
scaffolded test suite against a real Plone site.

This is the structural guard against registrations that render but do not
load: profile metadata dependencies, repositorytool/diff_tool import steps,
layer-bound browser registrations and behavior lookups all have to survive
an actual Zope/GenericSetup start, not just a render-level assertion.

Slow (downloads Plone on first run). Opt in with ``pytest -m integration``.
"""
import shutil
import subprocess

import pytest
from helpers import plone_subprocess_env, run_copier


@pytest.mark.integration
class TestGeneratedAddonInPloneSite:
    """Install a fully generated addon into Plone and run its tests."""

    def test_generated_addon_installs_and_passes_its_tests(
        self,
        temp_dir,
        backend_addon_template,
        content_type_template,
        behavior_template,
        view_template,
        form_template,
        portlet_template,
        controlpanel_template,
        restapi_service_template,
        svelte_app_template,
        theme_template,
    ):
        if shutil.which("uv") is None:
            pytest.skip("uv is required to run the Plone smoke test")

        addon_dir = temp_dir / "smokeaddon"
        package_name = "collective.smoketest"

        result = run_copier(
            backend_addon_template,
            addon_dir,
            data={"package_name": package_name},
        )
        assert result.returncode == 0, f"backend_addon failed: {result.stderr}"

        subtemplates = [
            (content_type_template, {"content_type_name": "Task"}),
            (behavior_template, {"behavior_name": "IFeatured"}),
            (view_template, {"view_name": "my-view"}),
            (form_template, {"form_name": "my-form"}),
            (portlet_template, {"portlet_name": "Weather"}),
            (controlpanel_template, {"controlpanel_name": "MyFeatured"}),
            (restapi_service_template, {"service_name": "stats"}),
            (svelte_app_template, {"svelte_app_name": "my-app"}),
            (theme_template, {"theme_name": "My Theme"}),
        ]
        for template, data in subtemplates:
            data["package_name"] = package_name
            result = run_copier(template, addon_dir, data=data)
            assert result.returncode == 0, (
                f"subtemplate {template} failed:\n{result.stderr}"
            )

        sync = subprocess.run(
            ["uv", "sync", "--extra", "test"],
            cwd=addon_dir,
            env=plone_subprocess_env(),
            capture_output=True,
            text=True,
            timeout=900,
        )
        assert sync.returncode == 0, (
            f"uv sync failed:\nSTDOUT:\n{sync.stdout}\nSTDERR:\n{sync.stderr}"
        )

        run = subprocess.run(
            ["uv", "run", "pytest", "tests/", "-v", "--tb=short"],
            cwd=addon_dir,
            env=plone_subprocess_env(),
            capture_output=True,
            text=True,
            timeout=1800,
        )
        assert run.returncode == 0, (
            "generated addon test suite failed:\n"
            f"STDOUT:\n{run.stdout}\nSTDERR:\n{run.stderr}"
        )
