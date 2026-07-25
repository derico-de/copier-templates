#!/usr/bin/env python3
"""XML escaping for free-text answers spliced into XML/ZCML.

Single code path for updaters and post-copy hooks that embed
user-provided text (titles, descriptions) into XML or ZCML.
Identifiers derived by validators stay unescaped.
"""
from xml.sax.saxutils import escape


def escape_xml_text(value: str) -> str:
    """Escape ``value`` for use as XML element text."""
    return escape(value)


def escape_xml_attr(value: str) -> str:
    """Escape ``value`` for use inside a double-quoted XML attribute."""
    return escape(value, {'"': "&quot;"})
