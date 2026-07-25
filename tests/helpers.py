"""Test helper utilities for copier-templates tests."""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def plone_subprocess_env() -> dict[str, str]:
    """Environment for running a generated addon's own uv/pytest.

    Strips this repo's PYTHONPATH/VIRTUAL_ENV so the generated addon's
    environment doesn't import the outer test venv's (potentially
    incompatible) packages.
    """
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    return env


def run_copier(
    template_path: Path | str,
    dest_path: Path | str,
    data: dict[str, Any] | None = None,
    defaults: bool = True,
    vcs_ref: str | None = None,
    overwrite: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run copier with given parameters.

    Args:
        template_path: Path to the template directory
        dest_path: Destination path for generated files
        data: Dictionary of answers to copier prompts
        defaults: Whether to use default values for prompts
        vcs_ref: Git reference to use (None for local templates)
        overwrite: Whether to overwrite existing files without asking

    Returns:
        CompletedProcess with stdout, stderr, and returncode
    """
    cmd = [
        sys.executable,
        "-m",
        "copier",
        "copy",
        "--trust",
        str(template_path),
        str(dest_path),
    ]

    if defaults:
        cmd.append("--defaults")

    if overwrite:
        cmd.append("--overwrite")

    if vcs_ref:
        cmd.extend(["--vcs-ref", vcs_ref])

    if data:
        for key, value in data.items():
            # Handle boolean values
            if isinstance(value, bool):
                value = "true" if value else "false"
            cmd.extend(["--data", f"{key}={value}"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def assert_file_exists(path: Path, content_contains: str | list[str] | None = None) -> None:
    """
    Assert file exists and optionally contains text.

    Args:
        path: Path to the file
        content_contains: String or list of strings that must be in the file

    Raises:
        AssertionError: If file doesn't exist or doesn't contain expected content
    """
    assert path.exists(), f"File {path} does not exist"

    if content_contains:
        content = path.read_text()
        if isinstance(content_contains, str):
            content_contains = [content_contains]
        for expected in content_contains:
            assert expected in content, f"'{expected}' not found in {path}"


def assert_file_not_exists(path: Path) -> None:
    """
    Assert file does not exist.

    Args:
        path: Path to the file

    Raises:
        AssertionError: If file exists
    """
    assert not path.exists(), f"File {path} should not exist but does"


def assert_dir_exists(path: Path) -> None:
    """
    Assert directory exists.

    Args:
        path: Path to the directory

    Raises:
        AssertionError: If directory doesn't exist
    """
    assert path.exists(), f"Directory {path} does not exist"
    assert path.is_dir(), f"{path} exists but is not a directory"


def read_toml(path: Path) -> dict:
    """
    Read and parse a TOML file.

    Args:
        path: Path to the TOML file

    Returns:
        Parsed TOML content as dictionary
    """
    import tomllib

    with open(path, "rb") as f:
        return tomllib.load(f)


def generate_addon(
    backend_addon_template: Path | str,
    dest: Path,
    package_name: str = "collective.mypackage",
    extra: dict[str, Any] | None = None,
) -> Path:
    """
    Generate a fresh backend_addon at ``dest`` and return its path.

    Thin wrapper around :func:`run_copier` used by subtemplate tests.
    """
    data = {"package_name": package_name}
    if extra:
        data.update(extra)
    result = run_copier(backend_addon_template, dest, data=data)
    assert result.returncode == 0, f"backend_addon generation failed: {result.stderr}"
    return dest


def apply_subtemplate(
    template_path: Path | str,
    addon_dir: Path,
    data: dict[str, Any] | None = None,
) -> subprocess.CompletedProcess:
    """
    Apply a subtemplate on top of an existing addon directory.

    Thin wrapper around :func:`run_copier` that exists so tests read naturally
    ("apply the vocabulary template to my addon") and so we have a single place
    to add cross-cutting options later if needed.
    """
    return run_copier(template_path, addon_dir, data=data or {})


def copy_tree(src: Path, dst: Path) -> Path:
    """Copy a directory tree, replacing ``dst`` if it already exists."""
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def get_nested_value(data: dict, *keys: str, default: Any = None) -> Any:
    """
    Get a nested value from a dictionary.

    Args:
        data: Dictionary to search
        keys: Keys to traverse
        default: Default value if key not found

    Returns:
        Value at the nested key path or default
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current
