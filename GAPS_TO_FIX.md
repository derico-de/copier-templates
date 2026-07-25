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

## 1. Subtemplate file/dir layout divergences (must-fix)

### 1.1 `behavior` — FIXED
| legacy | new |
|---|---|
| `src/<pkg>/behaviors/my_behavior.py` | `src/<pkg>/behaviors/my_behavior.py` ✓ |

`behavior_module` is now snake_case of the behavior class (`MyBehavior` →
`my_behavior`; `IMyBehavior` interface name kept inside the file).

### 1.2 `content_type`
| legacy | new |
|---|---|
| `src/<pkg>/content/my_content_type.py` | `src/<pkg>/content/mycontenttype.py` |
| `src/<pkg>/content/my_content_type.xml` (FTI in `content/`) | `src/<pkg>/profiles/default/types/MyContentType.xml` only |

**Fix:**
- Module filename must be `snake_case(content_type_name).py` (`MyContentType` → `my_content_type`).
- Also emit `content/<snake>.xml` with an FTI stub (legacy emits both content-local FTI and
  the profile-level one).

### 1.3 `controlpanel` — flattened to module, should be subpackage
| legacy | new |
|---|---|
| `controlpanels/my_control_panel/__init__.py` | — |
| `controlpanels/my_control_panel/configure.zcml` | — |
| `controlpanels/my_control_panel/controlpanel.py` | `controlpanels/my_control_panel.py` |

**Fix:** generate a subpackage `controlpanels/<snake>/` with `__init__.py`,
`configure.zcml`, and `controlpanel.py`. Parent `controlpanels/configure.zcml`
should include the subpackage.

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

**Fix:** generate the nested `api/services/<name>/` layout with one Python file
per HTTP verb (`get.py`/`post.py`/...). `services/` → `api/services/` everywhere
(including the include added to parent `configure.zcml`).

### 1.5 `portlet`
| legacy | new |
|---|---|
| `portlets/myportlet.py` | `portlets/my_portlet.py` |
| `portlets/myportlet.pt` | `portlets/my_portlet.pt` |

**Fix:** module name has no underscore (`MyPortlet` → `myportlet`, *lower-concat*,
not snake_case). The test file is `tests/test_myportlet.py` in legacy.

### 1.6 `viewlet`
| legacy | new |
|---|---|
| `viewlets/myviewlet.py` | `viewlets/my_viewlet.py` |
| `viewlets/my-viewlet.pt` *(dash!)* | `viewlets/my_viewlet.pt` |

**Fix:** Python module is lower-concat (`myviewlet.py`); template file uses
dash-separated name (`my-viewlet.pt`). Mismatched separators are intentional in
the legacy template — reproduce exactly.

### 1.7 `vocabulary`
| legacy | new |
|---|---|
| `vocabularies/available_things.py` (default name) | `vocabularies/my_vocabulary.py` |

**Fix:** default `vocabulary_name` in copier.yml is `AvailableThings` so the
generated module is `available_things.py` (match legacy default). Also the test
name follows: `tests/test_vocab_available_things.py`.

### 1.8 `upgrade_step`
| legacy | new |
|---|---|
| `upgrades/1001/.gitkeep` | — |

**Fix:** emit an empty `.gitkeep` inside `upgrades/<dest_version>/` so the
per-version directory exists even before any file-based upgrade handlers are added.

### 1.9 `indexer`
| legacy | new |
|---|---|
| `indexers/my_indexer.zcml` (separate) + included in `indexers/configure.zcml` | zcml inlined in `indexers/configure.zcml` |

**Fix:** emit a per-indexer zcml file `indexers/<snake>.zcml`; the folder-level
`indexers/configure.zcml` should `<include file="<snake>.zcml" />` the new one.

### 1.10 `mockup_pattern`
| legacy | new |
|---|---|
| `browser/pattern-demo.pt` | `browser/pat-<name>-demo.pt` *(just fixed, wrong name)* |
| `resources/pat-<name>/my-pattern.{js,scss,test.js}`, `resources/bundle.js`, `resources/pat-<name>/documentation.md` | `src/<pkg>/patterns/…` (no top-level `resources/`) |

**Fix:**
- Rename to `browser/pattern-demo.pt` (the legacy filename is fixed, does not include
  the pattern name).
- Also emit legacy top-level `resources/` layout with `pat-<name>/{<name>.js, <name>.scss,
  <name>.test.js, documentation.md}` and a root `resources/bundle.js`. The current
  `src/<pkg>/patterns/` tree is new-only.

### 1.11 `svelte_app`
| legacy | new |
|---|---|
| `src/<pkg>/svelte_apps/<app>/{README.md,favicon.png,global.css,index.html}` | `src/<pkg>/svelte_apps/__init__.py`, `<module>.py`, `<module>.pt` |
| `svelte_src/<app>/{rollup.config.js,.gitignore,README.md,scripts/setupTypeScript.js}` | `svelte_src/<app>/vite.config.js` (only) |

**Fix:**
- Ship app assets (`README.md`, `favicon.png`, `global.css`, `index.html`) inside
  `src/<pkg>/svelte_apps/<app>/` as well as the compile sources.
- In `svelte_src/<app>/` add `rollup.config.js`, `.gitignore`, `README.md`,
  `scripts/setupTypeScript.js` to match legacy. (Decide: keep `vite.config.js`
  alongside rollup, or drop vite — confirm with maintainer. Rule says
  "stay the same", so remove vite and use rollup.)
- `src/<pkg>/svelte_apps/__init__.py`, `<module>.py`, `<module>.pt` are new-only
  and should be removed unless a maintainer intentionally added them.

---

## 2. `tests/` location — top-level vs inside package

| legacy | new |
|---|---|
| `src/<pkg>/tests/**` | `tests/**` |

Legacy places tests *inside* the package so they ship in the distribution and
run via `plone.testing`. New places them at the repo root.

**Fix:** move the tests subtemplate output to `src/<pkg>/tests/` (same layout as
legacy). Keep files:
`__init__.py`, `test_setup.py`, `test_behavior_<snake>.py`,
`test_ct_<snake>.py`, `test_form_<snake>.py`, `test_indexer_<snake>.py`,
`test_<portlet_modname>.py` (`test_myportlet.py`),
`test_subscriber_<snake>.py`, `test_upgrade_step_<version>.py`,
`test_view_<snake>.py`, `test_viewlet_<modname>.py`,
`test_vocab_<snake>.py`, `robot/test_ct_<snake>.robot`.

Also reconcile existing `conftest.py` (new-only) — decide whether to drop it
(legacy has no pytest conftest; it uses `plone.testing`) or keep it at
`src/<pkg>/tests/conftest.py`.

Test filenames also need renaming to match legacy patterns:

| legacy name | new name |
|---|---|
| `test_behavior_my_behavior.py` | `test_behavior_imybehavior.py` |
| `test_ct_my_content_type.py` | `test_ct_mycontenttype.py` |
| `test_myportlet.py` | `test_portlet_my_portlet.py` |
| `test_upgrade_step_1001.py` | `test_upgrade_1001.py` |
| `test_viewlet_myviewlet.py` | `test_viewlet_my_viewlet.py` |
| `test_vocab_available_things.py` | `test_vocab_my_vocabulary.py` |
| `robot/test_ct_my_content_type.robot` | `robot/test_ct_mycontenttype.robot` |

New-only test files (have no legacy counterpart, decide whether to keep):
`test_controlpanel_my_control_panel.py`, `test_service_my_service.py`,
`test_theme_my_barceloneta.py`.

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

1. **Layout / naming fixes** (§1 + §2): these affect every addon generated and
   break assumptions downstream users have built up against bobtemplates. Do
   first.
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
