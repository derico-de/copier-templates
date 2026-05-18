# TODO's

- [x] read possible Plone version from PyPi in backend_addon / zope-setup
- [ ] extract the instance out into it's own template. Use it to create a single instance, with all features we currently have in zope-setup's instances: single instance, zeo server, client instances for ZEO and RelStorage. This template should bea able to create a ZEO server in the setup, a zeo client (instance1, instance2 aso), as well as single direct storage instance and relstorage clients (instance1, instance2 aso with relstorage backend).
- [ ] provide a docker compose setup and .devcontainer setup in zope-setup and backend_addon

## Testing

- [ ] **Full per-field coverage for every template.** For each template, test every question field, both with its default value and with a custom value. Custom values must include shell-/markup-hostile input (apostrophes, quotes, `$ ` `` ` `` `& ; | ( ) < >`, spaces, unicode) so the whole `_tasks` + Jinja + hook path is exercised, not just the happy path. Motivation: the `_tasks` shell-quoting bug (apostrophe in a description aborted the run) shipped only because no test ever set a description/title field — every test relied on copier defaults. Assert: copier exits 0 *and* the value lands unmangled in the generated files. Prefer a data-driven/parametrized matrix derived from each `copier.yml`'s questions over hand-written per-field tests. Also add an in-process `copier.run_copy(data=...)` case mirroring the actual plonecli entry point, not only the `copier --data` CLI path.




## Goals

- [ ] the combination of zope-setup and backend_addon should be useful to create the same file structure as cookieplone does:
        backend  # backend_addon with a build-in zope setup
        frontend  # volto frontend

## Not yet implemented bobtemplates.plone subtemplates

Reference: https://github.com/plone/bobtemplates.plone/

- [x] **site_initialization** — GenericSetup registry records for initial Plone site state (site title, language, mail)

Already implemented: `backend_addon` (≈addon), `behavior`, `content_type`, `restapi_service`, `upgrade_step` (plus Plone-specific `zope-setup`, `zope_instance`).

Rule: the generated output must stay as close as possible to the existing bobtemplates.plone structure — no structural deviations without explicit approval.

- [x] **controlpanel** — Plone control panel (registry-based configuration UI)
- [x] **form** — z3c.form based form
- [x] **indexer** — custom catalog indexer (`@indexer` decorator + ZCML)
- [x] **mockup_pattern** — Mockup JS pattern integration
- [x] **portlet** — classic Plone portlet
- [x] **subscriber** — event subscriber handler
- [x] **svelte_app** — Svelte application integration
- [x] **theme** — custom theme package
- [x] **theme_barceloneta** — Barceloneta-based theme variant
- [x] **theme_basic** — basic theme variant
- [x] **view** — custom browser view
- [x] **viewlet** — viewlet component
- [x] **vocabulary** — named vocabulary