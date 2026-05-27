# History

## 0.2.0 (unreleased)


- Nothing changed yet.


## 0.1.0 (2026-05-27)


- Green, i18n-ready scaffolding across all templates and a new `language`
  subtemplate; pin an explicit short name on behavior registration.
  [MrTango]

- Add per-field test matrix and view tests that create the registered
  content type; fix generated tests to use the `integration` fixture and
  make test/dev deps resolvable for `uv`.
  [MrTango]

- Add GitHub Actions CI for lint and tests across all templates; support
  Python 3.11-3.13, drop 3.10.
  [MrTango]

- Add subtemplates mirroring bobtemplates.plone: `vocabulary`, `indexer`,
  `subscriber`, `view`, `viewlet`, `form`, `portlet`, `controlpanel`,
  `site_initialization`, `theme`, `theme_basic`, `theme_barceloneta`,
  `mockup_pattern`, `svelte_app`, `upgrade_step`, `restapi_service`.
  [MrTango]

- Add `addon` composite template chaining `backend_addon` + `zope-setup`,
  and a `zope_instance` template for additional Zope instances.
  [MrTango]

- Enable `zope-setup` as a dual-mode template (standalone + addon
  subtemplate); fetch Plone version choices dynamically from PyPI.
  [MrTango]

- Add `content_type` enhancements (behaviors, registry XML, parent content
  type handling) and per-template browser layer, permissions, locales,
  profiles and robot tests.
  [MrTango]

- Add plonecli integration metadata to all templates; support legacy
  bobtemplates.plone addons in subtemplate post-copy hooks.
  [MrTango]

- Initial multi-template Copier repository for Plone development with
  copier 9.x compatibility, hook refactor and devcontainer setup.
  [MrTango]
