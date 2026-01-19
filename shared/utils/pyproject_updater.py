#!/usr/bin/env python3
"""Utility for safely updating pyproject.toml files."""
from pathlib import Path
from typing import Any

try:
    import tomlkit
    from tomlkit import TOMLDocument
    TOMLKIT_AVAILABLE = True
except ImportError:
    TOMLKIT_AVAILABLE = False
    tomlkit = None
    TOMLDocument = None


class PyprojectUpdater:
    """Helper class for updating pyproject.toml files."""

    def __init__(self, path: Path | str):
        """
        Initialize the updater.

        Args:
            path: Path to pyproject.toml file
        """
        if not TOMLKIT_AVAILABLE:
            print("Warning: tomlkit not available. Pyproject updates will be skipped.")
            print("Install with: pip install tomlkit")
        self.path = Path(path)
        self._doc = None
        self._available = TOMLKIT_AVAILABLE

    def load(self):
        """
        Load the pyproject.toml file.

        Returns:
            Parsed TOML document or None if tomlkit not available
        """
        if not self._available:
            return None
        if self._doc is None:
            if self.path.exists():
                with open(self.path) as f:
                    self._doc = tomlkit.parse(f.read())
            else:
                self._doc = tomlkit.document()
        return self._doc

    def save(self) -> None:
        """Save changes to the pyproject.toml file."""
        if not self._available:
            return
        if self._doc is not None:
            with open(self.path, "w") as f:
                f.write(tomlkit.dumps(self._doc))

    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """
        Get a nested value from the document.

        Args:
            keys: Keys to traverse
            default: Default value if key not found

        Returns:
            Value at the nested key path or default
        """
        doc = self.load()
        if doc is None:
            return default
        current = doc
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def set_nested(self, *keys: str, value: Any) -> None:
        """
        Set a nested value in the document, creating intermediate tables as needed.

        Args:
            keys: Keys to traverse (last key is where value is set)
            value: Value to set
        """
        if not keys or not self._available:
            return

        doc = self.load()
        if doc is None:
            return
        current = doc

        # Navigate to parent, creating tables as needed
        for key in keys[:-1]:
            if key not in current:
                current[key] = tomlkit.table()
            current = current[key]

        # Set the value
        current[keys[-1]] = value

    def ensure_section(self, *keys: str):
        """
        Ensure a section exists, creating it if needed.

        Args:
            keys: Keys to the section

        Returns:
            The section table or None if tomlkit not available
        """
        if not self._available:
            return None
        doc = self.load()
        if doc is None:
            return None
        current = doc

        for key in keys:
            if key not in current:
                current[key] = tomlkit.table()
            current = current[key]

        return current

    def add_to_list(self, *keys: str, value: Any) -> None:
        """
        Add a value to a list, creating the list if it doesn't exist.

        Args:
            keys: Keys to the list (last key is the list name)
            value: Value to add
        """
        if not self._available:
            return
        existing = self.get_nested(*keys, default=[])
        if not isinstance(existing, list):
            existing = [existing] if existing else []

        if value not in existing:
            existing.append(value)
            self.set_nested(*keys, value=existing)

    def get_addon_settings(self) -> dict[str, Any]:
        """
        Get backend addon settings.

        Returns:
            Dictionary with addon settings
        """
        return dict(
            self.get_nested("tool", "plone", "backend_addon", "settings", default={})
        )

    def set_addon_setting(self, key: str, value: Any) -> None:
        """
        Set a backend addon setting.

        Args:
            key: Setting key
            value: Setting value
        """
        self.set_nested("tool", "plone", "backend_addon", "settings", key, value=value)

    def register_subtemplate(
        self, subtemplate_type: str, name: str
    ) -> None:
        """
        Register a subtemplate in addon settings.

        Args:
            subtemplate_type: Type of subtemplate (content_types, behaviors, services)
            name: Name of the item being registered
        """
        self.add_to_list(
            "tool", "plone", "backend_addon", "settings", "subtemplates", subtemplate_type,
            value=name
        )

    def get_project_settings(self) -> dict[str, Any]:
        """
        Get project settings (for zope-setup).

        Returns:
            Dictionary with project settings
        """
        return dict(
            self.get_nested("tool", "plone", "project", "settings", default={})
        )

    def set_project_setting(self, key: str, value: Any) -> None:
        """
        Set a project setting.

        Args:
            key: Setting key
            value: Setting value
        """
        self.set_nested("tool", "plone", "project", "settings", key, value=value)


def update_pyproject_setting(
    pyproject_path: Path | str,
    *keys: str,
    value: Any,
) -> None:
    """
    Update a setting in pyproject.toml.

    Convenience function for one-off updates.

    Args:
        pyproject_path: Path to pyproject.toml
        keys: Keys to the setting
        value: Value to set
    """
    updater = PyprojectUpdater(pyproject_path)
    updater.set_nested(*keys, value=value)
    updater.save()


def register_subtemplate_in_addon(
    pyproject_path: Path | str,
    subtemplate_type: str,
    name: str,
) -> None:
    """
    Register a subtemplate in the addon's pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml
        subtemplate_type: Type (content_types, behaviors, services)
        name: Name of the item
    """
    updater = PyprojectUpdater(pyproject_path)
    updater.register_subtemplate(subtemplate_type, name)
    updater.save()
