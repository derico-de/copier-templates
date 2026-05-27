"""Unit tests for zope-setup full-version derivation in the composite."""
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_addon_context_hook():
    spec = importlib.util.spec_from_file_location(
        "zope_setup_extensions", REPO_ROOT / "zope-setup" / "extensions.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.AddonContextHook


ALL = ["6.1.2", "6.1.1", "6.0.10", "5.2.14"]


def test_derive_matches_addon_minor():
    hook = _load_addon_context_hook()
    assert hook._derive_full_version({"plone_version": "6.0"}, ALL) == "6.0.10"


def test_derive_picks_latest_for_minor():
    hook = _load_addon_context_hook()
    assert hook._derive_full_version({"plone_version": "6.1"}, ALL) == "6.1.2"


def test_derive_falls_back_to_latest_without_addon():
    hook = _load_addon_context_hook()
    assert hook._derive_full_version({}, ALL) == "6.1.2"


def test_derive_falls_back_when_minor_unavailable():
    hook = _load_addon_context_hook()
    assert hook._derive_full_version({"plone_version": "7.0"}, ALL) == "6.1.2"


def test_derive_empty_versions():
    hook = _load_addon_context_hook()
    assert hook._derive_full_version({"plone_version": "6.1"}, []) == ""
