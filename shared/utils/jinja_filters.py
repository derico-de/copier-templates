"""Jinja filters shared by Copier templates."""

import json


def toml_string(value) -> str:
    """Return a TOML basic string with valid Unicode scalar characters."""
    return json.dumps(str(value), ensure_ascii=False)


def python_string(value) -> str:
    """Return a Python string literal."""
    return repr(str(value))
