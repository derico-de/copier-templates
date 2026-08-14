"""Pre-render validation for mutually exclusive theme templates."""

import sys
import tomllib
from pathlib import Path

from exceptions import ValidationError

_shared = Path(__file__).resolve().parents[1]
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from utils.bobtemplate_cfg import get_subtemplates  # noqa: E402


def reject_other_theme(dest: Path, current_template: str) -> None:
    """Reject another theme variant before Copier reaches file conflicts."""
    pyproject = dest / "pyproject.toml"
    try:
        with pyproject.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError):
        document = {}

    subtemplates = (
        document.get("tool", {})
        .get("plone", {})
        .get("backend_addon", {})
        .get("settings", {})
        .get("subtemplates", {})
    )
    configured_templates = [
        str(value) for value in subtemplates.get("theme_templates", [])
    ] or get_subtemplates(dest / "bobtemplate.cfg", "theme_templates")
    configured_themes = [
        str(value) for value in subtemplates.get("themes", [])
    ] or get_subtemplates(dest / "bobtemplate.cfg", "themes")

    if current_template in configured_templates:
        return
    if not configured_templates and not configured_themes:
        return

    configured = ", ".join(configured_templates or configured_themes)
    raise ValidationError(
        f"A different theme is already configured ({configured}). Theme templates "
        "are alternatives; remove the existing theme before applying another."
    )
