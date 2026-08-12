# Spec: Close undocumented bobtemplates.plone parity regressions

Labels: `ready-for-agent`

## Problem Statement

Plone developers who scaffold packages and features with plonecli expect the copier
templates to produce the same working results as their bobtemplates.plone
predecessors. Today, several templates silently generate incomplete or broken
output that bobtemplates got right:

- Feature templates no longer declare their GenericSetup profile dependencies, so
  a generated content type, REST service, or theme installs without pulling in
  `plone.app.dexterity`, `plone.restapi`, or `plone.app.theming` — the profile
  only works by accident if something else installed them first.
- A generated content type no longer gets versioning (`repositorytool.xml`) or
  compound-diff (`diff_tool.xml`) wiring, features bobtemplates configured
  automatically.
- Generating a second portlet or controlpanel overwrites the first one's profile
  registration, because those profile XML files are shipped as static renders
  instead of being merged idempotently.
- Free-text answers (descriptions, titles) containing `&`, `<`, `>`, or `"`
  produce malformed XML/ZCML, both in rendered templates and in the post-copy
  merge layer.
- The behavior template names its module after the interface
  (`imybehavior.py` instead of `my_behavior.py`).
- The restapi_service template asks for a service description and then discards
  the answer.
- The form template silently changed the registration permission from
  `cmf.ManagePortal` to `zope2.View`, and view/form registrations dropped the
  browser-layer restriction bobtemplates applied.
- Nothing in CI ever installs a generated package into Plone, so all of the
  above passed the existing render-level test suite.

None of the metadata/versioning/diff regressions are tracked in GAPS_TO_FIX.md.

## Solution

Bring the affected templates back to functional parity with bobtemplates.plone:
every generated feature declares the profile dependencies it needs, content
types get versioning and diff support, repeated generation of portlets and
controlpanels is additive instead of destructive, arbitrary user text is safe in
generated XML, questions that are asked are honored, and registration
permissions/layers match the bobtemplates behavior. A new end-to-end smoke test
installs a generated addon into Plone and runs its scaffolded test suite, so
this class of regression is caught structurally in CI, not by field reports.

## User Stories

1. As a Plone add-on developer, I want a generated content type's profile to depend on the Dexterity profile, so that installing my add-on works on a site where Dexterity content types were not already configured.
2. As a Plone add-on developer, I want a generated REST API service's profile to depend on the plone.restapi profile, so that my service is registered and functional immediately after installing my add-on.
3. As a Plone themer, I want a generated theme package's profile to depend on the theming profile, so that my theme can be activated right after install without manual profile edits.
4. As a Plone add-on developer, I want a generated content type to be registered for versioning, so that editors get working version history on my type without me hand-editing repositorytool XML.
5. As a Plone add-on developer, I want a generated content type to be registered with the diff tool, so that editors can compare versions of my type out of the box.
6. As a Plone add-on developer, I want to generate a second portlet in the same package without losing the first portlet's profile registration, so that I can build packages with several portlets incrementally.
7. As a Plone add-on developer, I want to generate a second controlpanel in the same package without losing the first controlpanel's configlet registration, so that repeated scaffolding is always additive.
8. As a Plone add-on developer, I want to type an ampersand or angle bracket in a content type description, so that the generated profile XML is still well-formed and loads in Zope.
9. As a Plone add-on developer, I want free-text answers to be escaped everywhere they land in ZCML or profile XML, so that no answer I give can produce a package that fails to import.
10. As a Plone add-on developer, I want the behavior template to create a snake_case module named after the behavior, so that the generated file layout matches Plone community conventions and the bobtemplates layout my team knows.
11. As a Plone add-on developer, I want the service description I typed to appear in the generated REST service, so that my answers are never silently discarded.
12. As a Plone add-on developer, I want a generated form to be protected by the management permission as it was in bobtemplates, so that scaffolding a form does not accidentally expose it to anonymous users.
13. As a Plone add-on developer, I want generated view and form registrations bound to my package's browser layer, so that they do not leak into other sites in the same Zope instance.
14. As a Plone add-on developer, I want a generated svelte app to include the static-directory registration bobtemplates produced, so that its resources are actually served.
15. As a template maintainer, I want a shared helper that appends a dependency to a profile's metadata file idempotently, so that every feature template can declare its dependencies through one tested code path.
16. As a template maintainer, I want portlet and controlpanel profile XML handled by the same idempotent merge machinery as ZCML and types XML, so that no template ships destructive static renders of shared files.
17. As a template maintainer, I want a CI smoke test that installs a generated addon into Plone and runs its scaffolded tests, so that a registration that renders but does not load fails the build.
18. As a template maintainer, I want the hostile-input test matrix to include XML-structural characters in description and title fields, so that escaping regressions are caught at the render seam.
19. As a template maintainer, I want the newly found regressions recorded in the gap-tracking document, so that the backlog reflects reality.
20. As a plonecli user running `copier update`, I want post-copy merges to remain idempotent when re-applied, so that updating a template does not duplicate or corrupt previously merged registrations.
21. As a Plone add-on developer upgrading an old bobtemplates package, I want the copier subtemplates to produce equivalent registrations, so that mixed-era packages behave consistently.

## Implementation Decisions

- Extend the shared metadata updater with an idempotent "append dependency"
  operation (currently it can only bump the profile version). Wire it into the
  post-copy hooks of content_type (`profile-plone.app.dexterity:default`),
  restapi_service (`profile-plone.restapi:default`), and all three theme
  templates (`profile-plone.app.theming:default`). Creating the metadata file
  when absent and skipping when the dependency already exists are both required.
- Port bobtemplates' repositorytool and diff-tool mutations into the
  content_type post-copy hook as new shared updaters, following the existing
  updater class pattern: register the new type for versioning
  (at_edit_autoversion, version_on_revert policies) and for Compound Diff.
- Convert portlets.xml and controlpanel.xml from static template renders into
  idempotent merges performed by the post-copy hook, matching how types.xml and
  configure.zcml are handled. Restore the column-interface `<for>` entries and
  i18n attributes bobtemplates emitted in portlets.xml.
- Introduce a single escaping utility (XML text and attribute escaping) used by
  every shared updater and hook that splices free-text answers into XML/ZCML.
  Jinja templates that emit XML apply explicit escaping filters to free-text
  variables; identifiers derived by validators remain unescaped.
- Change the behavior template's derived module name from the lowercased
  interface name to the snake_case behavior name, and update the gap-tracking
  document entry for it.
- Thread the already-asked service description answer through the
  restapi_service post-copy task into the generated service registration, the
  same way the theme description fix was done.
- Restore the form registration permission to the management permission and add
  the package browser-layer binding to form and view registrations, matching
  bobtemplates.
- Verify and, if confirmed missing, restore the svelte app's static-directory
  ZCML registration.
- Add the new e2e smoke job to CI: generate a backend addon, apply content_type
  plus at least one more subtemplate, sync its environment, and run the
  generated package's own scaffolded test suite against Plone. Keep it a single
  job so CI cost stays bounded.
- Record all regressions fixed here (and the svelte finding) in the
  gap-tracking document so the backlog stays truthful.

## Testing Decisions

- Good tests assert on external behavior of generation: the contents of the
  generated package (profile XML semantics, registration attributes), never on
  hook internals or updater call sequences.
- Primary seam: the existing render-test suite (in-process copier runs plus
  assertions on generated files and XML well-formedness). Every fix gets its
  assertions here: metadata gains the expected dependency exactly once even on
  re-run; two portlets/controlpanels coexist after two generations; behavior
  module name; service description present; form permission and layer values;
  repositorytool and diff-tool entries present.
- Extend the existing hostile-input matrix with XML-structural characters
  (`&`, `<`, `>`, `"`, `'`) in description/title fields, asserting the
  generated XML parses.
- Secondary, new seam (the only new one): one CI smoke test that installs a
  fully generated addon into Plone and runs its scaffolded tests. Prior art:
  the existing combination test that applies multiple subtemplates to one
  addon, and the generated-package lint test — the smoke test extends that
  pattern from "renders and lints" to "loads and passes".
- Idempotency tests re-run the post-copy hooks twice and assert no duplicate
  entries, following the existing merge-idempotency test pattern.

## Out of Scope

- The documented layout/naming divergences in GAPS_TO_FIX.md sections 1.2–1.11
  (controlpanel subpackage, nested REST service layout, indexer per-file ZCML,
  mockup/svelte tree layout, theme_barceloneta prebuilt assets) — tracked
  backlog, not regressions of this spec.
- Restoring dropped feature modes: supermodel-based content types,
  schema-only content-type classes, class-less (template-only) views.
- Tests-inside-package layout (GAPS section 2) and the backend_addon namespace
  and browser-skeleton items (GAPS section 3).
- A full `copier update` migration story for previously generated projects.
- Any plonecli CLI changes (separate spec in the plonecli repository).
- Consolidating duplicated ZCML snippets into shared Jinja macros (worthwhile
  refactor, but independent of these behavioral fixes).

## Further Notes

- The metadata-dependency and content-type versioning/diff regressions are not
  in GAPS_TO_FIX.md today; this spec is their tracking document until the gap
  file is updated.
- The e2e smoke test is intentionally minimal (one generated addon, one Plone
  version) — broadening the matrix is a follow-up once it exists.
- Analysis source: comparison of every copier template's post-copy hook against
  the corresponding bobtemplates.plone hook module (July 2026).
