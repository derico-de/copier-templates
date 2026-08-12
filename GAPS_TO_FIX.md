# Remaining gaps vs. bobtemplates.plone

Rule (user): **layout, file, and directory names must stay the same as in the old
(bobtemplates.plone) implementation unless explicitly stated otherwise.**

Reference comparison:
- legacy: `plonecli 2.4` + `bobtemplates.plone 6.4.3`  (`mr.bob`-based)
- new: `plonecli 7.x` + this copier-templates repo

Both were generated with the same answers on 2026-04-17. See `/tmp/compare/`.

Items already fixed in prior pass (for context): `interfaces.py`, `permissions.zcml`,
`profiles/default/{browserlayer,rolemap,catalog}.xml`,
`profiles/uninstall/browserlayer.xml`, `locales/` scaffold
(`__init__.py`, `README.rst`, `update.py`, `update.sh`, `<pkg>.pot`, `en/LC_MESSAGES/<pkg>.po`),
content_type permission patcher, mockup_pattern & svelte_app bundle registrations,
content_type robot test, mockup_pattern demo page.

---

## 0. Functional parity regressions — FIXED (2026-07)

Found by comparing every copier post-copy hook against its bobtemplates.plone
counterpart (spec: `plans/spec-bobtemplates-parity-regressions.md`). All fixed:

- **Profile dependencies**: content_type now declares
  `profile-plone.app.dexterity:default`, restapi_service
  `profile-plone.restapi:default`, and all three theme templates
  `profile-plone.app.theming:default` in `metadata.xml` (idempotent shared
  `MetadataXMLUpdater.add_dependency`).
- **Content type versioning/diff**: content_type registers the type in
  `repositorytool.xml` (`at_edit_autoversion`, `version_on_revert`) and
  `diff_tool.xml` (Compound Diff), as bobtemplates did.
- **Destructive profile renders**: `portlets.xml` and `controlpanel.xml` were
  static template renders — a second portlet/controlpanel overwrote the first.
  Both are now idempotent post-copy merges. portlets.xml also regained the
  bobtemplates `<for interface="...IColumn" />` entry and i18n attributes.
- **XML escaping**: free-text answers (titles, descriptions) are escaped in
  every hook/updater splice (`shared/utils/xml_escape.py`) and via explicit
  `| e` filters in XML-emitting Jinja templates.
- **behavior module name**: `my_behavior.py` instead of `imybehavior.py`
  (was §1.1 below).
- **form permission/layer**: form registrations restored to
  `cmf.ManagePortal`; view and form registrations are bound to the package
  browser layer again.
- **svelte_app static resources**: restored the `plone:static` registration
  for the bundle directory (`++plone++<pkg>.svelte`). Deviation from
  bobtemplates: the directory is `svelte_apps/static` (the vite build
  output) because `svelte_apps/` itself holds the Python mount-point
  modules in the copier layout; vite output filenames now match the bundle
  registry entries.
- **restapi_service description**: verified the asked description lands in
  the generated service module (regression report was against an older
  state); covered by a render test now.
- **CI**: new opt-in e2e smoke test (`tests/test_e2e_smoke.py`,
  `-m integration`) generates an addon with content_type + behavior + view +
  restapi_service, installs it into a real Plone site and runs the
  generated package's own test suite.

---

## 1. Subtemplate file/dir layout divergences (must-fix) — FIXED (2026-07)

All items below are fixed except the flagged parts of §1.10/§1.11 (see the
individual sections).

### 1.1 `behavior` — FIXED
| legacy | new |
|---|---|
| `src/<pkg>/behaviors/my_behavior.py` | `src/<pkg>/behaviors/my_behavior.py` ✓ |

`behavior_module` is now snake_case of the behavior class (`MyBehavior` →
`my_behavior`; `IMyBehavior` interface name kept inside the file).

### 1.2 `content_type` — FIXED
`content_type_module` is now snake_case of the class (`MyContentType` →
`my_content_type.py`), and `content/<snake>.xml` ships a plone.supermodel
schema stub (verified against the bobtemplates source — the content-local XML
is a supermodel model, not an FTI).

### 1.3 `controlpanel` — FIXED
Generates the subpackage `controlpanels/<snake>/` with `__init__.py`,
`controlpanel.py`, and a self-contained `configure.zcml` (browser:page bound
to the package browser layer + plone.restapi adapter).
`controlpanels/configure.zcml` only accumulates `<include package=".<snake>" />`
entries (idempotent merge).

### 1.4 `restapi_service` — `api/` vs `services/` tree
Legacy nests services under `api/services/<name>/` with per-service files:
```
src/<pkg>/api/__init__.py
src/<pkg>/api/configure.zcml
src/<pkg>/api/services/__init__.py
src/<pkg>/api/services/configure.zcml
src/<pkg>/api/services/<name>/__init__.py
src/<pkg>/api/services/<name>/configure.zcml
src/<pkg>/api/services/<name>/get.py  # or post.py, etc. per HTTP verb
```
New is flat:
```
src/<pkg>/services/__init__.py
src/<pkg>/services/configure.zcml
src/<pkg>/services/<name>.py
```

**FIXED:** the nested `api/services/<name>/` layout is generated with one
Python module per HTTP verb (`get.py`/`post.py`/`patch.py`/`delete.py`, each a
`Service` subclass with `reply()` — also fixing that POST/PATCH/DELETE
handlers were previously methods plone.restapi never called), a per-service
`configure.zcml`, and the include chain parent → `.api` → `.services` →
`.<module>`. Verb classes follow bobtemplates naming (`StatsGet`).

### 1.5 `portlet`
| legacy | new |
|---|---|
| `portlets/myportlet.py` | `portlets/my_portlet.py` |
| `portlets/myportlet.pt` | `portlets/my_portlet.pt` |

**FIXED:** module name follows bobtemplates (`snakecase(slugify(name))`):
`MyPortlet` → `myportlet.py`/`myportlet.pt`, `My Portlet` → `my_portlet.py`.
The generated test file is `test_<module>.py` (`test_myportlet.py`).

### 1.6 `viewlet`
| legacy | new |
|---|---|
| `viewlets/myviewlet.py` | `viewlets/my_viewlet.py` |
| `viewlets/my-viewlet.pt` *(dash!)* | `viewlets/my_viewlet.pt` |

**FIXED:** the Python module is snake_case of `viewlet_name`
(default `myviewlet` → `myviewlet.py`) and the template file is
dash-separated from the class name (`MyViewlet` → `my-viewlet.pt`). The
mismatched separators reproduce the legacy behavior exactly.

### 1.7 `vocabulary`
| legacy | new |
|---|---|
| `vocabularies/available_things.py` (default name) | `vocabularies/my_vocabulary.py` |

**FIXED** (prior pass): default `vocabulary_name` is `AvailableThings`, so the
generated module is `available_things.py` and the test
`test_vocab_available_things.py`.

### 1.8 `upgrade_step`
| legacy | new |
|---|---|
| `upgrades/1001/.gitkeep` | — |

**FIXED:** `upgrades/<dest_version>/` ships both `.gitkeep` and the (empty)
`metadata.txt` — the legacy template contains both.

### 1.9 `indexer`
| legacy | new |
|---|---|
| `indexers/my_indexer.zcml` (separate) + included in `indexers/configure.zcml` | zcml inlined in `indexers/configure.zcml` |

**FIXED:** the adapters (dummy guard + indexer) live in a per-indexer
`indexers/<name>.zcml`; `indexers/configure.zcml` accumulates
`<include file="<name>.zcml" />` entries (idempotent merge).

### 1.10 `mockup_pattern`
| legacy | new |
|---|---|
| `browser/pattern-demo.pt` | `browser/pat-<name>-demo.pt` *(just fixed, wrong name)* |
| `resources/pat-<name>/my-pattern.{js,scss,test.js}`, `resources/bundle.js`, `resources/pat-<name>/documentation.md` | `src/<pkg>/patterns/…` (no top-level `resources/`) |

**Partially FIXED:**
- `browser/pattern-demo.pt` (fixed legacy filename) — done.
- The top-level `resources/` relocation is deliberately NOT done: the
  self-contained `src/<pkg>/patterns/` tree (webpack/babel/package.json) was
  established together with the bundle registrations in the §0 pass, and the
  legacy `resources/` layout only works with the legacy top-level npm/webpack
  scaffold (§3.4), which is flagged as probably out of scope. Revisit together
  with the §3 decision.

### 1.11 `svelte_app`
| legacy | new |
|---|---|
| `src/<pkg>/svelte_apps/<app>/{README.md,favicon.png,global.css,index.html}` | `src/<pkg>/svelte_apps/__init__.py`, `<module>.py`, `<module>.pt` |
| `svelte_src/<app>/{rollup.config.js,.gitignore,README.md,scripts/setupTypeScript.js}` | `svelte_src/<app>/vite.config.js` (only) |

**Deliberately NOT changed** — conflicts with the newer §0 decision: the
copier layout keeps vite (`svelte_src/<app>/vite.config.js`) with build output
in `svelte_apps/static/` and the Python mount-point modules in
`svelte_apps/`, because the vite output filenames are matched to the bundle
registry entries (documented deviation in §0). Converting to the legacy
rollup layout would undo that fix. Needs an explicit maintainer decision;
revisit together with §3/§4.

---

## 2. `tests/` location — top-level vs inside package — FIXED (2026-07)

All templates now emit their generated tests inside the package at
`src/<pkg>/tests/` (legacy layout), including `robot/`. The generated
`pyproject.toml` points pytest (`testpaths`) and the ruff `S101` per-file
ignore at the new location.

Filename parity: `test_behavior_<snake>.py`, `test_ct_<snake>.py`,
`test_vocab_available_things.py`, `test_viewlet_<modname>.py`, and
`robot/test_ct_<snake>.robot` follow the module-name fixes from §1;
the portlet test is `test_<portlet_modname>.py` (`test_myportlet.py`)
and the upgrade test was renamed to `test_upgrade_step_<version>.py`.

Decisions taken:
- `conftest.py` is kept (moved to `src/<pkg>/tests/conftest.py`) — the
  copier templates use pytest fixtures on top of plone.testing layers.
- New-only test files without a legacy counterpart are kept
  (`test_controlpanel_<snake>.py`, `test_service_<snake>.py`,
  `test_theme_my_barceloneta.py`) — additive coverage, no layout conflict.

---

## 3. `backend_addon` base scaffold — legacy top-level files

The new addon uses a modern `pyproject.toml`-only layout. The legacy addon ships
a large pile of buildout/tox/npm config files. **If the rule "layout must stay
the same" is absolute**, these all need to be added back. Flagging for review
because several are obsolete (Python 3.7 buildout, `setup.py`/`setup.cfg`
duplication):

### 3.1 Buildout + tox (probably obsolete)
- `base.cfg`, `buildout.cfg`
- `bobtemplate.cfg`
- `test_plone52.cfg`, `test_plone60.cfg`
- `constraints.txt`, `constraints_plone52.txt`, `constraints_plone60.txt`
- `requirements.txt`, `requirements_plone52.txt`, `requirements_plone60.txt`
- `tox.ini`

### 3.2 Packaging (duplicated with pyproject.toml)
- `setup.py`, `setup.cfg`, `MANIFEST.in`

### 3.3 Docs / legal (legacy-style naming)
- `README.rst` *(new has `README.md`)*
- `CHANGES.rst` *(new has `CHANGELOG.md`)*
- `CONTRIBUTORS.rst`, `DEVELOP.rst`
- `LICENSE.rst`, `LICENSE.GPL`
- `docs/conf.py`, `docs/index.rst`

### 3.4 CI / git / editor
- `.coveragerc`, `.gitattributes`, `.gitignore`, `.prettierignore`
- `.github/ISSUE_TEMPLATE.md`, `.github/workflows/plone-package.yml`
- `.gitlab-ci.yml`, `.travis.yml`
- `.release-it.js`
- `.eslintrc.js`, `babel.config.js`, `jest.config.js`, `prettier.config.js`,
  `webpack.config.js`, `package.json`

### 3.5 Namespace
- `src/collective/__init__.py` — namespace package `__init__.py` at namespace
  level. New has nothing at `src/collective/`. Legacy emits a minimal
  namespace declaration. **Add** this.

### 3.6 `browser/` skeleton
Missing from new:
- `src/<pkg>/browser/__init__.py`
- `src/<pkg>/browser/configure.zcml`
- `src/<pkg>/browser/overrides/.gitkeep`
- `src/<pkg>/browser/static/.gitkeep`
- `src/<pkg>/browser/static/bundles/.gitkeep`

Even if downstream subtemplates don't use `browser/`, the `__init__.py` +
`configure.zcml` + `static/bundles/.gitkeep` are expected by tooling (CSS/JS
bundle registration, overrides).

---

## 4. Extra output in new (not in legacy) — review & reconcile

Flagged because the rule says "stay the same". Each needs an explicit decision:
keep (document as deliberate enhancement) or drop.

### Added by `backend_addon`
- `.copier-answers.yml`, `.pre-commit-config.yaml`
- `CHANGELOG.md`, `README.md`, `pyproject.toml` — replace `*.rst` / `setup.py`
- `tests/__init__.py`, `tests/conftest.py`, `tests/test_setup.py`

### Added by `content_type`
- `src/<pkg>/content/configure.zcml`
- `src/<pkg>/profiles/default/registry/plone.displayed_types.<Class>.xml`

### Added by `restapi_service`
- `src/<pkg>/services/{__init__.py,configure.zcml,my_service.py}` (instead of
  `api/services/<name>/…`)

### Added by `theme_barceloneta`
Pre-built theme assets shipped directly in the package:
- `src/<pkg>/theme/barceloneta-*.{png,ico}` (×7 icons)
- `src/<pkg>/theme/css/theme.{css,css.map,min.css,min.css.map}`
- `src/<pkg>/theme/js/theme.{js,min.js}`
- `src/<pkg>/theme/preview.png`
- `src/<pkg>/theme/scss/{_base,_custom,_maps,_variables,theme}.scss`
- `src/<pkg>/theme/tinymce-templates/{README.rst,card-group.html,list.html}`

Legacy `theme_barceloneta` doesn't ship pre-built assets — it provides a
`rules.xml` + scss source only. Decide whether the pre-built output should be
`.gitignore`'d and regenerated, or removed from the template entirely.

### Added by `theme_basic`
- `src/<pkg>/browser/overrides/plone.app.layout.viewlets.sections.pt`
- `src/<pkg>/browser/overrides/plone.app.portlets.browser.templates.footer.pt`

Legacy theme_basic emits only `.gitkeep` placeholders in `overrides/`. New
ships actual override stubs. Decide keep/drop.

### Added by `backend_addon` profiles
- `src/<pkg>/profiles/uninstall/metadata.xml`  
  (Legacy uninstall profile has no `metadata.xml`.)

### Added by `svelte_app`
- `src/<pkg>/svelte_apps/__init__.py`, `my_svelte_app.py`, `my_svelte_app.pt`
- `svelte_src/<app>/vite.config.js` — replaces legacy `rollup.config.js`

---

## 5. Priority suggestion

1. ~~**Layout / naming fixes** (§1 + §2)~~ — DONE (2026-07), except the
   flagged parts of §1.10/§1.11 which depend on the §3/§4 decisions.
2. **`browser/` skeleton + namespace `__init__.py`** (§3.5, §3.6): needed for
   static resources and namespace packaging to work as expected.
3. **Extras-to-review** (§4): each needs a one-line decision (keep / drop /
   gitignore) and either a removal or a CHANGES note.
4. **Buildout / tox / legacy packaging files** (§3.1 – §3.4): these conflict
   with the modern `pyproject.toml` approach. Probably **explicitly out of
   scope** for the new implementation, but confirm with the maintainer since
   the "same layout" rule is currently written without exceptions.

## 6. How to re-run the comparison

```bash
# Legacy (bobtemplates):
uv tool install 'plonecli==2.4' --with 'bobtemplates.plone' --with 'mr.bob' \
  --with 'setuptools<81' --with 'case_conversion<3' --python 3.10 --force
export PATH="/home/node/.local/share/uv/tools/plonecli/bin:$PATH"
mrbob -w -n -c /tmp/compare/addon_answers.ini -O collective.testaddon \
  bobtemplates.plone:addon
cd collective.testaddon
for t in behavior content_type controlpanel form indexer mockup_pattern \
         portlet restapi_service site_initialization subscriber svelte_app \
         theme upgrade_step view viewlet vocabulary; do
  mrbob -w -n -c /tmp/compare/sub_answers.ini bobtemplates.plone:$t
done

# New (copier):
bash /tmp/compare/run_new.sh

# Diff:
diff <(cd legacy && find . -type f | sort) <(cd new && find . -type f | sort)
```
