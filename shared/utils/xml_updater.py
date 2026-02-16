#!/usr/bin/env python3
"""Utilities for updating XML configuration files."""
import re
from pathlib import Path


class ConfigureZCMLUpdater:
    """Updates content/configure.zcml with plone:behavior entries."""

    TEMPLATE = '''\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:plone="http://namespaces.plone.org/plone"
    i18n_domain="{package_name}">

</configure>
'''

    BEHAVIOR_TEMPLATE = '''\
  <plone:behavior
      title="{title}"
      description="{description}"
      provides="{provides}"
      />
'''

    def __init__(self, path: Path | str):
        """
        Initialize the updater.

        Args:
            path: Path to configure.zcml file
        """
        self.path = Path(path)
        self._content = None
        self._modified = False

    def load(self) -> str:
        """Load the configure.zcml file content."""
        if self._content is None:
            if self.path.exists():
                self._content = self.path.read_text()
            else:
                self._content = ""
        return self._content

    def create_if_missing(self, package_name: str) -> None:
        """
        Create the file with initial structure if it doesn't exist.

        Args:
            package_name: The package name for i18n_domain
        """
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._content = self.TEMPLATE.format(package_name=package_name)
            self._modified = True

    def has_behavior(self, provides: str) -> bool:
        """
        Check if a behavior with the given provides attribute exists.

        Args:
            provides: The provides attribute to check for

        Returns:
            True if behavior exists, False otherwise
        """
        content = self.load()
        # Escape dots for regex
        escaped_provides = re.escape(provides)
        pattern = rf'provides\s*=\s*["\']\.?{escaped_provides}["\']'
        return bool(re.search(pattern, content))

    def add_behavior(self, title: str, description: str, provides: str) -> None:
        """
        Add a behavior entry if it doesn't exist.

        Args:
            title: Behavior title (interface name)
            description: Behavior description
            provides: Interface path (e.g., ".article.IArticle")
        """
        if self.has_behavior(provides):
            return

        content = self.load()
        if not content:
            return

        behavior_entry = self.BEHAVIOR_TEMPLATE.format(
            title=title,
            description=description,
            provides=provides,
        )

        # Insert before closing </configure> tag
        closing_tag = "</configure>"
        if closing_tag in content:
            self._content = content.replace(
                closing_tag,
                f"{behavior_entry}\n{closing_tag}"
            )
            self._modified = True

    def save(self) -> None:
        """Save changes to the file."""
        if self._modified and self._content is not None:
            self.path.write_text(self._content)


class ParentZCMLUpdater:
    """Updates parent addon configure.zcml with include directives for subpackages."""

    INCLUDE_TEMPLATE = '  <include package="{subpackage}" />\n'

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._content = None
        self._modified = False

    def load(self) -> str:
        if self._content is None:
            if self.path.exists():
                self._content = self.path.read_text()
            else:
                self._content = ""
        return self._content

    def has_include(self, subpackage: str) -> bool:
        content = self.load()
        escaped = re.escape(subpackage)
        pattern = rf'<include\s+package\s*=\s*["\']\.?{escaped}["\']'
        return bool(re.search(pattern, content))

    def add_include(self, subpackage: str) -> None:
        if self.has_include(subpackage):
            return
        content = self.load()
        if not content:
            return
        include_entry = self.INCLUDE_TEMPLATE.format(subpackage=subpackage)
        closing_tag = "</configure>"
        if closing_tag in content:
            self._content = content.replace(
                closing_tag,
                f"\n{include_entry}\n{closing_tag}"
            )
            self._modified = True

    def save(self) -> None:
        if self._modified and self._content is not None:
            self.path.write_text(self._content)


class TypesXMLUpdater:
    """Updates profiles/default/types.xml with FTI references."""

    TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8"?>
<object name="portal_types">
</object>
'''

    FTI_TEMPLATE = '  <object name="{content_type_class}" meta_type="Dexterity FTI"/>\n'

    def __init__(self, path: Path | str):
        """
        Initialize the updater.

        Args:
            path: Path to types.xml file
        """
        self.path = Path(path)
        self._content = None
        self._modified = False

    def load(self) -> str:
        """Load the types.xml file content."""
        if self._content is None:
            if self.path.exists():
                self._content = self.path.read_text()
            else:
                self._content = ""
        return self._content

    def create_if_missing(self) -> None:
        """Create the file with initial structure if it doesn't exist."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._content = self.TEMPLATE
            self._modified = True

    def has_fti_reference(self, content_type_class: str) -> bool:
        """
        Check if an FTI reference for the content type exists.

        Args:
            content_type_class: The content type class name

        Returns:
            True if FTI reference exists, False otherwise
        """
        content = self.load()
        escaped_name = re.escape(content_type_class)
        pattern = rf'<object\s+name\s*=\s*["\']\.?{escaped_name}["\']'
        return bool(re.search(pattern, content))

    def add_fti_reference(self, content_type_class: str) -> None:
        """
        Add an FTI reference if it doesn't exist.

        Args:
            content_type_class: The content type class name
        """
        if self.has_fti_reference(content_type_class):
            return

        content = self.load()
        if not content:
            return

        fti_entry = self.FTI_TEMPLATE.format(content_type_class=content_type_class)

        # Insert before closing </object> tag
        closing_tag = "</object>"
        if closing_tag in content:
            self._content = content.replace(
                closing_tag,
                f"{fti_entry}{closing_tag}"
            )
            self._modified = True

    def save(self) -> None:
        """Save changes to the file."""
        if self._modified and self._content is not None:
            self.path.write_text(self._content)
