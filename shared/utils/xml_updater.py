#!/usr/bin/env python3
"""Utilities for updating XML configuration files."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .xml_escape import escape_xml_attr


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
            title=escape_xml_attr(title),
            description=escape_xml_attr(description),
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


class ZCMLConfigureExtender:
    """Generic extender for ``<configure>``-based ZCML files.

    This is the canonical way for subtemplates to *extend* (never
    overwrite) an existing ``configure.zcml`` file. It will:

    * create the file with a minimal ``<configure>`` root if it doesn't
      exist (declaring any required xmlns prefixes);
    * ensure additional xmlns prefixes are declared on an existing root;
    * check whether an element already exists (by tag + identifying
      attribute) so re-runs are idempotent;
    * append a raw ZCML element snippet before the closing
      ``</configure>`` tag, preserving all existing entries.
    """

    ZOPE_NS = "http://namespaces.zope.org/zope"

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._content: str | None = None
        self._modified = False

    def load(self) -> str:
        if self._content is None:
            self._content = self.path.read_text() if self.path.exists() else ""
        return self._content

    def create_if_missing(
        self,
        package_name: str,
        namespaces: dict[str, str] | None = None,
    ) -> None:
        if self.path.exists():
            return
        ns: dict[str, str] = {"": self.ZOPE_NS}
        if namespaces:
            ns.update(namespaces)
        lines = ["<configure"]
        for prefix, uri in ns.items():
            attr = f'xmlns:{prefix}="{uri}"' if prefix else f'xmlns="{uri}"'
            lines.append(f"    {attr}")
        lines[-1] = lines[-1] + f'\n    i18n_domain="{package_name}">'
        header = "\n".join(lines)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._content = f"{header}\n\n</configure>\n"
        self._modified = True

    def ensure_namespaces(self, namespaces: dict[str, str]) -> None:
        content = self.load()
        if not content:
            return
        match = re.search(r"<configure\b[^>]*>", content, re.DOTALL)
        if not match:
            return
        opening = match.group(0)
        new_opening = opening
        for prefix, uri in namespaces.items():
            attr = f'xmlns:{prefix}="{uri}"' if prefix else f'xmlns="{uri}"'
            if attr in new_opening:
                continue
            # Insert the new attribute just before the closing '>'
            new_opening = new_opening[:-1].rstrip() + f"\n    {attr}" + ">"
        if new_opening != opening:
            self._content = content.replace(opening, new_opening, 1)
            self._modified = True

    def has_element(
        self,
        tag: str,
        attr: str,
        value: str,
        extra_attrs: dict[str, str] | None = None,
    ) -> bool:
        """Return True if a matching ``<tag>`` element already exists.

        A match requires ``attr="value"`` and, when ``extra_attrs`` is given,
        every additional ``attr="value"`` pair to be present on the *same*
        element. This lets callers identify an element by a composite key
        (e.g. a ``browser:page`` by both ``name`` and ``for``), so two views
        sharing a ``name`` but registered ``for`` different interfaces are not
        treated as duplicates.
        """
        content = self.load()
        if not content:
            return False
        required = {attr: value}
        if extra_attrs:
            required.update(extra_attrs)
        # Iterate each element's opening tag (attribute values hold no '>').
        element_pattern = rf"<{re.escape(tag)}\b[^>]*?/?>"
        for match in re.finditer(element_pattern, content, re.DOTALL):
            block = match.group(0)
            if all(
                re.search(
                    rf'\b{re.escape(a)}\s*=\s*["\']{re.escape(v)}["\']', block
                )
                for a, v in required.items()
            ):
                return True
        return False

    def append_element(self, snippet: str) -> None:
        """Append a raw ZCML element snippet before ``</configure>``."""
        content = self.load()
        if not content:
            return
        snippet = snippet.rstrip() + "\n"
        closing = "</configure>"
        if closing not in content:
            return
        self._content = content.replace(closing, f"{snippet}\n{closing}", 1)
        self._modified = True

    def save(self) -> None:
        if self._modified and self._content is not None:
            self.path.write_text(self._content)


def extend_configure_zcml(
    zcml_path: Path | str,
    package_name: str,
    namespaces: dict[str, str],
    element_tag: str,
    identifying_attr: str,
    identifying_value: str,
    snippet: str,
    extra_identifying_attrs: dict[str, str] | None = None,
) -> tuple[bool, str]:
    """Create-if-missing and idempotently append a ZCML element.

    ``extra_identifying_attrs`` lets callers identify an element by a composite
    key (e.g. a ``browser:page`` by both ``name`` and ``for``), so distinct
    registrations that happen to share the primary attribute are not treated
    as duplicates.

    Returns ``(changed, message)`` — ``changed`` is True if anything
    was written; ``message`` is a human-readable status string.
    """
    ext = ZCMLConfigureExtender(zcml_path)
    ext.create_if_missing(package_name, namespaces=namespaces)
    ext.ensure_namespaces(namespaces)
    if ext.has_element(
        element_tag, identifying_attr, identifying_value, extra_identifying_attrs
    ):
        key = f"{identifying_attr}='{identifying_value}'"
        if extra_identifying_attrs:
            key += "".join(
                f", {a}='{v}'" for a, v in extra_identifying_attrs.items()
            )
        return False, (
            f"{element_tag} with {key} already exists in {zcml_path}."
        )
    ext.append_element(snippet)
    ext.save()
    return True, f"Extended {zcml_path} with {element_tag} '{identifying_value}'."


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


class ParentFTIUpdater:
    """Updates a parent type FTI XML to allow a new child portal type.

    Inserts ``<element value="ChildType" />`` inside the parent's
    ``allowed_content_types`` property.  When the parent FTI file does
    not exist yet (e.g. for default Plone types), a minimal override is
    created with ``purge="False"`` so it only appends without replacing
    the type's existing allowed list.
    """

    MINIMAL_FTI_TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8"?>
<object name="{portal_type}" meta_type="Dexterity FTI">
  <property name="allowed_content_types" purge="False">
    <element value="{child_type}"/>
  </property>
</object>
'''

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._content: str | None = None
        self._modified = False

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> str:
        if self._content is None:
            self._content = self.path.read_text() if self.path.exists() else ""
        return self._content

    def has_allowed_child(self, child_type: str) -> bool:
        content = self.load()
        escaped = re.escape(child_type)
        pattern = (
            r'<property\s+name\s*=\s*"allowed_content_types"[^>]*>'
            r'[\s\S]*?<element\s+value\s*=\s*"' + escaped + r'"\s*/>'
            r'[\s\S]*?</property>'
        )
        return bool(re.search(pattern, content))

    def create_minimal(self, portal_type: str, child_type: str) -> None:
        """Create a minimal FTI override that only appends to allowed_content_types."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._content = self.MINIMAL_FTI_TEMPLATE.format(
            portal_type=portal_type,
            child_type=child_type,
        )
        self._modified = True

    def add_allowed_child(self, child_type: str) -> bool:
        """Add ``child_type`` to ``allowed_content_types``. Return True on change."""
        if not self.path.exists():
            return False
        content = self.load()
        if self.has_allowed_child(child_type):
            return False

        # Case 1: self-closing <property name="allowed_content_types"/>
        self_closing = re.compile(
            r'([ \t]*)<property\s+name\s*=\s*"allowed_content_types"\s*/>'
        )
        match = self_closing.search(content)
        if match:
            prop_indent = match.group(1)
            elem_indent = prop_indent + "  "
            replacement = (
                f'{prop_indent}<property name="allowed_content_types">\n'
                f'{elem_indent}<element value="{child_type}"/>\n'
                f'{prop_indent}</property>'
            )
            self._content = content[: match.start()] + replacement + content[match.end():]
            self._modified = True
            return True

        # Case 2: existing open/close <property ...>...</property>
        open_close = re.compile(
            r'([ \t]*)(<property\s+name\s*=\s*"allowed_content_types"[^>]*>)'
            r'([\s\S]*?)(</property>)'
        )
        match = open_close.search(content)
        if match:
            prop_indent = match.group(1)
            elem_indent = prop_indent + "  "
            opening_tag = match.group(2)
            inner = match.group(3)
            new_element = f'{elem_indent}<element value="{child_type}"/>'
            if inner.strip():
                new_inner = inner.rstrip() + f"\n{new_element}\n{prop_indent}"
            else:
                new_inner = f"\n{new_element}\n{prop_indent}"
            self._content = (
                content[: match.start()]
                + prop_indent + opening_tag
                + new_inner
                + match.group(4)
                + content[match.end():]
            )
            self._modified = True
            return True

        return False

    def save(self) -> None:
        if self._modified and self._content is not None:
            self.path.write_text(self._content)


class MetadataXMLUpdater:
    """Reads and updates profiles/default/metadata.xml version and dependencies."""

    TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8"?>
<metadata>
  <version>1000</version>
  <dependencies>
  </dependencies>
</metadata>
'''

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def get_version(self) -> str | None:
        """Return the current profile version string, or None if not found."""
        if not self.path.exists():
            return None
        try:
            tree = ET.parse(self.path)
            version_el = tree.find("version")
            if version_el is not None and version_el.text:
                return version_el.text.strip()
        except ET.ParseError:
            pass
        return None

    def set_version(self, new_version: str) -> None:
        """Update the profile version in metadata.xml."""
        if not self.path.exists():
            return
        content = self.path.read_text()
        updated = re.sub(
            r"(<version>)\s*\S+\s*(</version>)",
            rf"\g<1>{new_version}\g<2>",
            content,
        )
        if updated != content:
            self.path.write_text(updated)

    def has_dependency(self, dependency: str) -> bool:
        """Return True if the profile already declares ``dependency``."""
        if not self.path.exists():
            return False
        content = self.path.read_text()
        pattern = (
            r"<dependency>\s*" + re.escape(dependency) + r"\s*</dependency>"
        )
        return bool(re.search(pattern, content))

    def add_dependency(self, dependency: str) -> bool:
        """Idempotently append ``dependency`` to ``<dependencies>``.

        Creates the metadata file (and the ``<dependencies>`` section)
        when absent. Returns True if the file was changed.
        """
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(self.TEMPLATE)
        if self.has_dependency(dependency):
            return False
        content = self.path.read_text()
        entry = f"    <dependency>{dependency}</dependency>\n"

        # Self-closing <dependencies/> -> expand to open/close form.
        match = re.search(r"([ \t]*)<dependencies\s*/>", content)
        if match:
            indent = match.group(1)
            replacement = (
                f"{indent}<dependencies>\n{entry}{indent}</dependencies>"
            )
            content = content[: match.start()] + replacement + content[match.end():]
            self.path.write_text(content)
            return True

        # Existing <dependencies>...</dependencies> section.
        match = re.search(r"[ \t]*</dependencies>", content)
        if match:
            content = content[: match.start()] + entry + content[match.start():]
            self.path.write_text(content)
            return True

        # No dependencies section yet: add one before </metadata>.
        closing = "</metadata>"
        if closing in content:
            section = f"  <dependencies>\n{entry}  </dependencies>\n"
            content = content.replace(closing, f"{section}{closing}", 1)
            self.path.write_text(content)
            return True

        return False


class RepositoryToolXMLUpdater:
    """Updates profiles/default/repositorytool.xml with versioning policies.

    Registers a portal type for CMFEditions versioning the way
    bobtemplates.plone did: ``at_edit_autoversion`` and
    ``version_on_revert`` policies inside ``<policymap>``.
    """

    TEMPLATE = '''\
<?xml version="1.0"?>
<repositorytool>
  <policymap>
  </policymap>
</repositorytool>
'''

    TYPE_TEMPLATE = '''\
    <type name="{portal_type}">
      <policy name="at_edit_autoversion"/>
      <policy name="version_on_revert"/>
    </type>
'''

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def has_type(self, portal_type: str) -> bool:
        if not self.path.exists():
            return False
        content = self.path.read_text()
        pattern = rf'<type\s+name\s*=\s*["\']{re.escape(portal_type)}["\']'
        return bool(re.search(pattern, content))

    def add_type(self, portal_type: str) -> bool:
        """Idempotently register ``portal_type`` for versioning."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(self.TEMPLATE)
        if self.has_type(portal_type):
            return False
        content = self.path.read_text()
        entry = self.TYPE_TEMPLATE.format(portal_type=portal_type)

        match = re.search(r"([ \t]*)<policymap\s*/>", content)
        if match:
            indent = match.group(1)
            replacement = f"{indent}<policymap>\n{entry}{indent}</policymap>"
            content = content[: match.start()] + replacement + content[match.end():]
            self.path.write_text(content)
            return True

        match = re.search(r"[ \t]*</policymap>", content)
        if match:
            content = content[: match.start()] + entry + content[match.start():]
            self.path.write_text(content)
            return True

        return False


class DiffToolXMLUpdater:
    """Updates profiles/default/diff_tool.xml with compound-diff entries.

    Registers a portal type with the diff tool the way bobtemplates.plone
    did: a ``Compound Diff for Dexterity types`` field entry inside
    ``<difftypes>``.
    """

    TEMPLATE = '''\
<?xml version="1.0"?>
<object>
  <difftypes>
  </difftypes>
</object>
'''

    TYPE_TEMPLATE = '''\
    <type portal_type="{portal_type}">
      <field name="any" difftype="Compound Diff for Dexterity types"/>
    </type>
'''

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def has_type(self, portal_type: str) -> bool:
        if not self.path.exists():
            return False
        content = self.path.read_text()
        pattern = (
            rf'<type\s+portal_type\s*=\s*["\']{re.escape(portal_type)}["\']'
        )
        return bool(re.search(pattern, content))

    def add_type(self, portal_type: str) -> bool:
        """Idempotently register ``portal_type`` with the diff tool."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(self.TEMPLATE)
        if self.has_type(portal_type):
            return False
        content = self.path.read_text()
        entry = self.TYPE_TEMPLATE.format(portal_type=portal_type)

        match = re.search(r"([ \t]*)<difftypes\s*/>", content)
        if match:
            indent = match.group(1)
            replacement = f"{indent}<difftypes>\n{entry}{indent}</difftypes>"
            content = content[: match.start()] + replacement + content[match.end():]
            self.path.write_text(content)
            return True

        match = re.search(r"[ \t]*</difftypes>", content)
        if match:
            content = content[: match.start()] + entry + content[match.start():]
            self.path.write_text(content)
            return True

        return False


class PortletsXMLUpdater:
    """Updates profiles/default/portlets.xml with GS portlet entries.

    Shared idempotent merge (like types.xml / configure.zcml) so repeated
    portlet generation is additive instead of overwriting the file.
    """

    TEMPLATE = '''\
<?xml version="1.0"?>
<portlets
    xmlns:i18n="http://xml.zope.org/namespaces/i18n"
    i18n:domain="{package_name}">
</portlets>
'''

    PORTLET_TEMPLATE = '''\

  <portlet
      addview="{addview}"
      title="{title}"
      description="{description}"
      i18n:attributes="title title_{portlet_module};
                       description description_{portlet_module}"
      >

    <!-- This enables the portlet for right column,
         left column and the footer. -->
    <for interface="plone.app.portlets.interfaces.IColumn" />

    <!-- This would enable the portlet in the dashboard. -->
    <!--<for interface="plone.app.portlets.interfaces.IDashboard" />-->

  </portlet>
'''

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def has_portlet(self, addview: str) -> bool:
        if not self.path.exists():
            return False
        content = self.path.read_text()
        pattern = rf'addview\s*=\s*["\']{re.escape(addview)}["\']'
        return bool(re.search(pattern, content))

    def add_portlet(
        self,
        package_name: str,
        addview: str,
        title: str,
        description: str,
        portlet_module: str,
    ) -> bool:
        """Idempotently append a ``<portlet>`` entry. Return True on change."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                self.TEMPLATE.format(package_name=package_name)
            )
        if self.has_portlet(addview):
            return False
        content = self._ensure_i18n_namespace(self.path.read_text())
        entry = self.PORTLET_TEMPLATE.format(
            addview=addview,
            title=escape_xml_attr(title),
            description=escape_xml_attr(description),
            portlet_module=portlet_module,
        )
        closing = "</portlets>"
        if closing not in content:
            return False
        self.path.write_text(content.replace(closing, f"{entry}\n{closing}", 1))
        return True

    @staticmethod
    def _ensure_i18n_namespace(content: str) -> str:
        """Declare xmlns:i18n on the root if a pre-merge file lacks it."""
        if "xmlns:i18n" in content:
            return content
        match = re.search(r"<portlets\b[^>]*>", content)
        if not match:
            return content
        opening = match.group(0)
        new_opening = (
            opening[:-1].rstrip()
            + '\n    xmlns:i18n="http://xml.zope.org/namespaces/i18n">'
        )
        return content.replace(opening, new_opening, 1)


class ControlPanelXMLUpdater:
    """Updates profiles/default/controlpanel.xml with configlet entries.

    Shared idempotent merge so repeated controlpanel generation is
    additive instead of overwriting the file.
    """

    TEMPLATE = '''\
<?xml version="1.0"?>
<object name="portal_controlpanel" meta_type="Plone Control Panel Tool">
</object>
'''

    CONFIGLET_TEMPLATE = '''\

  <configlet
      title="{title}"
      action_id="{action_id}"
      appId="{package_name}"
      category="Products"
      condition_expr=""
      url_expr="string:${{portal_url}}/@@{action_id}"
      visible="True"
      i18n:attributes="title"
      i18n:domain="{package_name}"
      xmlns:i18n="http://xml.zope.org/namespaces/i18n">
    <permission>Manage portal</permission>
  </configlet>
'''

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def has_configlet(self, action_id: str) -> bool:
        if not self.path.exists():
            return False
        content = self.path.read_text()
        pattern = rf'action_id\s*=\s*["\']{re.escape(action_id)}["\']'
        return bool(re.search(pattern, content))

    def add_configlet(
        self,
        package_name: str,
        action_id: str,
        title: str,
    ) -> bool:
        """Idempotently append a ``<configlet>`` entry. Return True on change."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(self.TEMPLATE)
        if self.has_configlet(action_id):
            return False
        content = self.path.read_text()
        entry = self.CONFIGLET_TEMPLATE.format(
            title=escape_xml_attr(title),
            action_id=action_id,
            package_name=package_name,
        )
        closing = "</object>"
        if closing not in content:
            return False
        self.path.write_text(content.replace(closing, f"{entry}\n{closing}", 1))
        return True


class UpgradeZCMLUpdater:
    """Manages file includes in upgrades/configure.zcml."""

    TEMPLATE = '''\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:genericsetup="http://namespaces.zope.org/genericsetup"
    i18n_domain="{package_name}">

</configure>
'''

    INCLUDE_TEMPLATE = '  <include file="{filename}" />\n'

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

    def create_if_missing(self, package_name: str) -> None:
        """Create the file with initial structure if it doesn't exist."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._content = self.TEMPLATE.format(package_name=package_name)
            self._modified = True

    def has_file_include(self, filename: str) -> bool:
        """Check if an include for the given filename already exists."""
        content = self.load()
        escaped = re.escape(filename)
        pattern = rf'<include\s+file\s*=\s*["\']\.?{escaped}["\']'
        return bool(re.search(pattern, content))

    def add_file_include(self, filename: str) -> None:
        """Add an <include file="..." /> entry before the closing </configure> tag."""
        if self.has_file_include(filename):
            return

        content = self.load()
        if not content:
            return

        include_entry = self.INCLUDE_TEMPLATE.format(filename=filename)

        closing_tag = "</configure>"
        if closing_tag in content:
            self._content = content.replace(
                closing_tag,
                f"{include_entry}\n{closing_tag}",
            )
            self._modified = True

    def save(self) -> None:
        if self._modified and self._content is not None:
            self.path.write_text(self._content)
