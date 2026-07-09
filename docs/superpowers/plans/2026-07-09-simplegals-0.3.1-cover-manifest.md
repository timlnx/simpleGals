# simpleGals 0.3.1 (Cover, Manifest, Branding) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add owner-selectable gallery cover images, a machine-readable `out/gallery.json` manifest, a sgui cover picker, a version-stamped promo footer, and always-on simpleGals generator branding on every page.

**Architecture:** Extend the `ProjectConfig` dataclass and the Jinja2 template context. A pure `resolve_cover()` helper in `template.py` is shared by both `render_gallery()` (for the index `og:image`) and `build()` (for the manifest), avoiding a `gallery -> template` circular import. Branding and version flow into templates through the render context sourced from `simplegals.__version__` and a new `simplegals.PROJECT_URL` constant.

**Tech Stack:** Python 3.10+, dataclasses, Jinja2, Pillow, urwid, pytest.

## Global Constraints

- Python >= 3.10.
- bitmath >= 2.0.0; NIST prefixes only (MiB, not MB).
- Bare version everywhere, no `v` prefix (VERSION file, git tag, Release name, promo text, generator meta).
- Branding/homepage URL: `https://github.com/simplegals/simpleGals` (org repo; GitHub redirects cover the pre-transfer `timlnx` path).
- No em-dashes in generated copy or comments; use plain punctuation (`|`, `,`, `.`, `()`).
- No `Co-Authored-By` or Claude attribution in commit messages.
- Test runner: `.venv/bin/python -m pytest tests/ -q`.
- Tests assert the version via `simplegals.__version__` (never a hardcoded `"0.3.1"`), so they pass regardless of the installed VERSION.
- All existing tests plus the new ones must pass at the end.

## File Structure

- `simplegals/__init__.py` — add `PROJECT_URL` constant next to `__version__`.
- `simplegals/core/config.py` — add `cover: str = ""` to `ProjectConfig`.
- `simplegals/core/template.py` — add `resolve_cover()`; add `version`, `project_url`, `cover_og_path` to the render context.
- `simplegals/template/page.html.j2` — generator meta, top/bottom comments, cover-based `og:image`/`twitter:image`, versioned promo.
- `simplegals/template/item.html.j2` — generator meta, top/bottom comments, versioned promo.
- `simplegals/core/gallery.py` — import `resolve_cover` and `__version__`; write `out/gallery.json`; warn on a missing cover name.
- `simplegals/tui/preview_panel.py` — add a `cover_field` to `GallerySettingsPanel`.
- `VERSION` — bump to `0.3.1`.
- `CLAUDE.md` — document the `cover` gallery setting.
- Tests: `tests/test_config.py`, `tests/test_template.py`, `tests/test_gallery.py`, `tests/test_tui_widgets.py`.

---

### Task 1: `cover` field on ProjectConfig

**Files:**
- Modify: `simplegals/core/config.py` (ProjectConfig, around line 25-26)
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `ProjectConfig.cover: str` (default `""`), serialized to and from `simpleGal.json` by the existing tolerant `load_project_config`/`save_project_config`.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_config.py`:

```python
def test_project_config_has_cover_default():
    assert ProjectConfig().cover == ""


def test_cover_roundtrips(tmp_path):
    p = tmp_path / "simpleGal.json"
    save_project_config(ProjectConfig(cover="hero.jpg"), p)
    assert load_project_config(p).cover == "hero.jpg"
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `.venv/bin/python -m pytest tests/test_config.py::test_project_config_has_cover_default tests/test_config.py::test_cover_roundtrips -v`
Expected: FAIL (`TypeError: ... unexpected keyword argument 'cover'` / `AttributeError`).

- [ ] **Step 3: Add the field**

In `simplegals/core/config.py`, in `ProjectConfig`, add `cover` right after `description`:

```python
@dataclass
class ProjectConfig:
    title: str = "Gallery"
    description: str = ""
    cover: str = ""
    layout: Layout = field(default_factory=Layout)
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `.venv/bin/python -m pytest tests/test_config.py -v`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add simplegals/core/config.py tests/test_config.py
git commit -m "feat(config): add cover field to ProjectConfig"
```

---

### Task 2: `PROJECT_URL` constant and `resolve_cover()` helper

**Files:**
- Modify: `simplegals/__init__.py`
- Modify: `simplegals/core/template.py` (add function near top, after `_get_env`)
- Test: `tests/test_template.py`

**Interfaces:**
- Produces: `simplegals.PROJECT_URL: str`.
- Produces: `simplegals.core.template.resolve_cover(cover_name: str, records: list[dict]) -> dict | None` — returns the record whose `filename == cover_name`, else the first record; `None` only when `records` is empty. Does not log; callers warn on a missing name.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_template.py`:

```python
from simplegals import PROJECT_URL, __version__
from simplegals.core.template import resolve_cover


def test_project_url_is_org_url():
    assert PROJECT_URL == "https://github.com/simplegals/simpleGals"


def test_resolve_cover_defaults_to_first():
    recs = [{"filename": "a.jpg"}, {"filename": "b.jpg"}]
    assert resolve_cover("", recs)["filename"] == "a.jpg"


def test_resolve_cover_selects_named():
    recs = [{"filename": "a.jpg"}, {"filename": "b.jpg"}]
    assert resolve_cover("b.jpg", recs)["filename"] == "b.jpg"


def test_resolve_cover_missing_falls_back_to_first():
    recs = [{"filename": "a.jpg"}, {"filename": "b.jpg"}]
    assert resolve_cover("ghost.jpg", recs)["filename"] == "a.jpg"


def test_resolve_cover_empty_returns_none():
    assert resolve_cover("x.jpg", []) is None
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `.venv/bin/python -m pytest tests/test_template.py -k "project_url or resolve_cover" -v`
Expected: FAIL (`ImportError: cannot import name 'PROJECT_URL'` / `resolve_cover`).

- [ ] **Step 3: Add the constant and helper**

In `simplegals/__init__.py`, add after the version block:

```python
PROJECT_URL = "https://github.com/simplegals/simpleGals"
```

In `simplegals/core/template.py`, add after the `_get_env` function (before `build_image_records`):

```python
def resolve_cover(cover_name: str, records: list[dict]) -> dict | None:
    """Pick the cover record from a list of (included) image records.

    cover_name is a source filename (e.g. "milkyway.jpg"). When it is empty or
    not present among records, the first record is used. Returns None only when
    records is empty. Callers are responsible for warning on a missing name.
    """
    if not records:
        return None
    if cover_name:
        for r in records:
            if r.get("filename") == cover_name:
                return r
    return records[0]
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `.venv/bin/python -m pytest tests/test_template.py -k "project_url or resolve_cover" -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add simplegals/__init__.py simplegals/core/template.py tests/test_template.py
git commit -m "feat(template): add PROJECT_URL and resolve_cover helper"
```

---

### Task 3: Version-stamped promo and always-on generator branding

**Files:**
- Modify: `simplegals/core/template.py` (`render_gallery` base context, around line 59-73)
- Modify: `simplegals/template/page.html.j2`
- Modify: `simplegals/template/item.html.j2`
- Test: `tests/test_template.py`

**Interfaces:**
- Consumes: `simplegals.__version__`, `simplegals.PROJECT_URL`.
- Produces: render context keys `version` and `project_url` available to all templates. Every generated page carries `<meta name="generator" content="simpleGals {version}">`, a `<!-- Generated with simpleGals {version} | {url} -->` comment right after `<!DOCTYPE html>` and as the last line, and (when `simple_gals_promo`) a footer reading `Generated with simpleGals {version}` linking to `project_url`.

- [ ] **Step 1: Write/adjust tests**

In `tests/test_template.py`, replace the two existing promo tests (`test_promo_footer_hidden_by_default`, `test_promo_footer_shown_when_enabled`) with the versions below, and add the branding tests. (`__version__` / `PROJECT_URL` are already imported from Task 2.)

```python
def test_promo_footer_hidden_by_default(tmp_path):
    out = _render(tmp_path, [_rec()])  # simple_gals_promo defaults to False
    for page in ("index.html", "a_item.html"):
        assert 'class="generated-by"' not in (out / page).read_text(encoding="utf-8")


def test_promo_footer_shown_with_version_and_url(tmp_path):
    out = _render(tmp_path, [_rec()], simple_gals_promo=True)
    for page in ("index.html", "a_item.html"):
        html = (out / page).read_text(encoding="utf-8")
        assert 'class="generated-by"' in html
        assert f"Generated with simpleGals {__version__}" in html
        assert PROJECT_URL in html


def test_generator_meta_present_on_every_page(tmp_path):
    out = _render(tmp_path, [_rec()], social_previews=False, simple_gals_promo=False)
    for page in ("index.html", "a_item.html"):
        html = (out / page).read_text(encoding="utf-8")
        assert f'<meta name="generator" content="simpleGals {__version__}">' in html


def test_branding_comment_top_and_bottom(tmp_path):
    out = _render(tmp_path, [_rec()], social_previews=False, simple_gals_promo=False)
    marker = f"<!-- Generated with simpleGals {__version__} | {PROJECT_URL} -->"
    for page in ("index.html", "a_item.html"):
        html = (out / page).read_text(encoding="utf-8")
        assert html.count(marker) == 2          # top and bottom
        assert html.rstrip().endswith(marker)   # bottom is the last line
```

- [ ] **Step 2: Run tests, verify branding tests fail**

Run: `.venv/bin/python -m pytest tests/test_template.py -k "promo or generator_meta or branding_comment" -v`
Expected: FAIL on `test_generator_meta_present_on_every_page` and `test_branding_comment_top_and_bottom` (no meta/comment yet); the two promo tests pass already.

- [ ] **Step 3: Add version + project_url to the render context**

In `simplegals/core/template.py`, add the package import after the existing `from .config import ProjectConfig` line:

```python
from .. import PROJECT_URL, __version__
```

In `render_gallery`, extend `base_ctx` (add the two keys, keep the rest):

```python
    base_ctx = {
        "title": config.title,
        "description": config.description,
        "copyright": config.copyright,
        "author": config.author,
        "site_url": config.site_url.rstrip("/") if config.site_url else "",
        "columns": config.layout.columns,
        "css_path": "style.css",
        "total_pages": total_pages,
        "gallery_zip": gallery_zip,
        "gallery_zip_size": gallery_zip_size,
        "social_previews": config.social_previews,
        "exif_display": config.exif_display,
        "simple_gals_promo": config.simple_gals_promo,
        "version": __version__,
        "project_url": PROJECT_URL,
    }
```

- [ ] **Step 4: Update `page.html.j2`**

In `simplegals/template/page.html.j2`:

Change the doctype line (line 7) to add the top comment:

```html
<!DOCTYPE html>
<!-- Generated with simpleGals {{ version }} | {{ project_url }} -->
<html lang="en">
```

Add the generator meta in `<head>` right after the viewport meta:

```html
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="simpleGals {{ version }}">
```

Replace the promo footer line:

```html
    {% if simple_gals_promo %}<p class="generated-by"><a href="{{ project_url }}" target="_blank" rel="noopener noreferrer">Generated with simpleGals {{ version }}</a></p>{% endif %}
```

Add the bottom comment as the final line, after `</html>`:

```html
</html>
<!-- Generated with simpleGals {{ version }} | {{ project_url }} -->
```

- [ ] **Step 5: Update `item.html.j2`**

In `simplegals/template/item.html.j2`, apply the same four edits:

Top comment after the doctype (line 2):

```html
<!DOCTYPE html>
<!-- Generated with simpleGals {{ version }} | {{ project_url }} -->
<html lang="en">
```

Generator meta after the viewport meta:

```html
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="simpleGals {{ version }}">
```

Promo footer:

```html
      {% if simple_gals_promo %}<p class="generated-by"><a href="{{ project_url }}" target="_blank" rel="noopener noreferrer">Generated with simpleGals {{ version }}</a></p>{% endif %}
```

Bottom comment after `</html>`:

```html
</html>
<!-- Generated with simpleGals {{ version }} | {{ project_url }} -->
```

- [ ] **Step 6: Run tests, verify they pass**

Run: `.venv/bin/python -m pytest tests/test_template.py -v`
Expected: PASS (all, including the four new/updated tests).

- [ ] **Step 7: Commit**

```bash
git add simplegals/core/template.py simplegals/template/page.html.j2 simplegals/template/item.html.j2 tests/test_template.py
git commit -m "feat(template): version-stamped promo and always-on generator branding"
```

---

### Task 4: Cover-based index `og:image`

**Files:**
- Modify: `simplegals/core/template.py` (`render_gallery`, after `records = build_image_records(...)`)
- Modify: `simplegals/template/page.html.j2` (og:image and twitter:image blocks)
- Test: `tests/test_template.py`

**Interfaces:**
- Consumes: `resolve_cover` (Task 2), `ProjectConfig.cover` (Task 1).
- Produces: render context key `cover_og_path` (the resolved cover's `og_path`, or `None`). The gallery index/grid/all pages use it for `og:image`/`twitter:image` instead of `images[0].og_path`.

- [ ] **Step 1: Write failing test**

Append to `tests/test_template.py`:

```python
def test_index_og_image_uses_cover_not_first(tmp_path):
    recs = [
        _rec(filename="a.jpg", og_path="a_og.jpg", thumb_path="a_thumb.jpg"),
        _rec(filename="b.jpg", og_path="b_og.jpg", thumb_path="b_thumb.jpg"),
    ]
    out = _render(tmp_path, recs, social_previews=True, cover="b.jpg")
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'property="og:image" content="https://x.example/b_og.jpg"' in html
    assert "a_og.jpg" not in html.split("og:image")[1][:200]
```

- [ ] **Step 2: Run test, verify it fails**

Run: `.venv/bin/python -m pytest tests/test_template.py::test_index_og_image_uses_cover_not_first -v`
Expected: FAIL (index og:image still uses `images[0].og_path` = `a_og.jpg`).

- [ ] **Step 3: Resolve the cover in `render_gallery`**

In `simplegals/core/template.py`, right after `records = build_image_records(out_dir, config, raw_records)`:

```python
    records = build_image_records(out_dir, config, raw_records)
    cover_rec = resolve_cover(config.cover, records)
```

Add one key to `base_ctx`:

```python
        "cover_og_path": cover_rec.get("og_path") if cover_rec else None,
```

- [ ] **Step 4: Update `page.html.j2` og tags**

In `simplegals/template/page.html.j2`, replace the `og:image` block:

```html
  {% if site_url and cover_og_path %}
  <meta property="og:image" content="{{ site_url }}/{{ cover_og_path }}">
  {% endif %}
```

and the `twitter:image` line:

```html
  {% if site_url and cover_og_path %}<meta name="twitter:image" content="{{ site_url }}/{{ cover_og_path }}">{% endif %}
```

- [ ] **Step 5: Run tests, verify they pass**

Run: `.venv/bin/python -m pytest tests/test_template.py -v`
Expected: PASS (all; `test_page_og_image_uses_og_path_and_gated` still passes because a single-image cover defaults to the first image).

- [ ] **Step 6: Commit**

```bash
git add simplegals/core/template.py simplegals/template/page.html.j2 tests/test_template.py
git commit -m "feat(template): gallery index og:image uses the resolved cover"
```

---

### Task 5: `out/gallery.json` manifest

**Files:**
- Modify: `simplegals/core/gallery.py` (imports; manifest write after `render_gallery`, before `log("Build complete.")`)
- Test: `tests/test_gallery.py`

**Interfaces:**
- Consumes: `resolve_cover` (Task 2), `ProjectConfig.cover` (Task 1), `simplegals.__version__`, existing `now_rfc3339`.
- Produces: `out/gallery.json` with keys `title, description, author, slug, cover, cover_og, image_count, simplegals_version, site_url, built_at`. `cover`/`cover_og` are `out/`-relative filenames (or `None`). `image_count` is the number of included images.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_gallery.py`:

```python
import json as _json
from simplegals import __version__ as _sg_version


def _read_manifest(tmp_project):
    return _json.loads((tmp_project / "out" / "gallery.json").read_text(encoding="utf-8"))


def test_build_writes_gallery_json(tmp_project):
    build(tmp_project, ProjectConfig(title="Demo", author="Tim"))
    m = _read_manifest(tmp_project)
    assert m["title"] == "Demo"
    assert m["author"] == "Tim"
    assert m["slug"] == tmp_project.name
    assert m["image_count"] == 2
    assert m["simplegals_version"] == _sg_version
    assert m["built_at"]


def test_gallery_json_cover_defaults_to_first(tmp_project):
    build(tmp_project, ProjectConfig())
    # sorted sources: TEST.jpg precedes TEST.png
    assert _read_manifest(tmp_project)["cover"] == "TEST_thumb.jpg"


def test_gallery_json_cover_respects_config(tmp_project):
    build(tmp_project, ProjectConfig(cover="TEST.png", social_previews=True))
    m = _read_manifest(tmp_project)
    assert m["cover"] == "TEST_thumb.png"
    assert m["cover_og"] == "TEST_og.png"


def test_gallery_json_cover_og_null_when_social_off(tmp_project):
    build(tmp_project, ProjectConfig(cover="TEST.png", social_previews=False))
    assert _read_manifest(tmp_project)["cover_og"] is None


def test_gallery_json_warns_on_missing_cover(tmp_project):
    log_path, _ = build(tmp_project, ProjectConfig(cover="ghost.jpg"))
    assert "ghost.jpg" in log_path.read_text(encoding="utf-8")
    assert _read_manifest(tmp_project)["cover"] == "TEST_thumb.jpg"  # fell back to first
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `.venv/bin/python -m pytest tests/test_gallery.py -k gallery_json -v`
Expected: FAIL (no `out/gallery.json` written yet).

- [ ] **Step 3: Import the helpers**

In `simplegals/core/gallery.py`, update the template import and add the version import:

```python
from .template import render_gallery, resolve_cover
```

Add near the other package-relative imports (with `from ..workers.pool import dispatch`):

```python
from .. import __version__
```

- [ ] **Step 4: Write the manifest**

In `simplegals/core/gallery.py`, immediately after the `render_gallery(...)` call and before `log("Build complete.")`:

```python
    included = [r for r in raw_records if r.get("include", True)]
    if config.cover and config.cover not in {r["filename"] for r in included}:
        log(f"Cover '{config.cover}' not found among included images; using first image.")
    cover_rec = resolve_cover(config.cover, included)
    manifest = {
        "title": config.title,
        "description": config.description,
        "author": config.author,
        "slug": project_dir.name,
        "cover": cover_rec["thumb_path"] if cover_rec else None,
        "cover_og": cover_rec.get("og_path") if cover_rec else None,
        "image_count": len(included),
        "simplegals_version": __version__,
        "site_url": config.site_url.rstrip("/") if config.site_url else None,
        "built_at": now_rfc3339(),
    }
    (out_dir / "gallery.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log(f"Wrote gallery.json (images={manifest['image_count']}, cover={manifest['cover']})")
```

- [ ] **Step 5: Run tests, verify they pass**

Run: `.venv/bin/python -m pytest tests/test_gallery.py -v`
Expected: PASS (all).

- [ ] **Step 6: Commit**

```bash
git add simplegals/core/gallery.py tests/test_gallery.py
git commit -m "feat(gallery): emit out/gallery.json manifest with cover metadata"
```

---

### Task 6: sgui cover picker

**Files:**
- Modify: `simplegals/tui/preview_panel.py` (`GallerySettingsPanel`)
- Test: `tests/test_tui_widgets.py`

**Interfaces:**
- Consumes: `ProjectConfig.cover` (Task 1), existing `StagedChangesModel` gallery-key staging.
- Produces: `GallerySettingsPanel.cover_field` (an `urwid.Edit`); staging `("gallery", "cover")` commits to `ProjectConfig.cover` via the existing `_apply_to_config` gallery branch (`setattr` on any matching attr).

- [ ] **Step 1: Write failing tests**

Append to `tests/test_tui_widgets.py`:

```python
def test_gallery_settings_panel_cover_field():
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import GallerySettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(cover="hero.jpg")
    staged = StagedChangesModel()
    panel = GallerySettingsPanel(config, staged, on_save=lambda: None, on_revert=lambda: None)
    assert panel.cover_field.edit_text == "hero.jpg"


def test_gallery_settings_panel_cover_change_stages():
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import GallerySettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig()
    staged = StagedChangesModel()
    panel = GallerySettingsPanel(config, staged, on_save=lambda: None, on_revert=lambda: None)
    panel.cover_field.set_edit_text("pick.jpg")
    assert staged.get_current("gallery", "cover", None) == "pick.jpg"
    assert staged.is_dirty("gallery")


def test_gallery_settings_panel_cover_commits(tmp_path):
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import GallerySettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig()
    staged = StagedChangesModel()
    panel = GallerySettingsPanel(config, staged, on_save=lambda: None, on_revert=lambda: None)
    panel.cover_field.set_edit_text("pick.jpg")
    new_config = staged.commit_key("gallery", config, tmp_path / "simpleGal.json")
    assert new_config.cover == "pick.jpg"
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `.venv/bin/python -m pytest tests/test_tui_widgets.py -k cover -v`
Expected: FAIL (`AttributeError: 'GallerySettingsPanel' object has no attribute 'cover_field'`).

- [ ] **Step 3: Add the field, handler, signal**

In `simplegals/tui/preview_panel.py`, inside `GallerySettingsPanel.__init__`, create the field right after `self.desc_field`:

```python
        self.desc_field = urwid.Edit("Description: ", edit_text=_v("description", config.description))
        self.cover_field = urwid.Edit("Cover:       ", edit_text=_v("cover", config.cover))
```

Add the change handler alongside the others (near `_on_desc_change`):

```python
        def _on_cover_change(widget, _old):
            staged.stage("gallery", "cover", config.cover, widget.edit_text)
            _notify()
```

Connect the signal (near the other `connect_signal` calls):

```python
        urwid.connect_signal(self.cover_field, "postchange", _on_cover_change)
```

- [ ] **Step 4: Add the field to the pile**

In the `urwid.Pile([...])` layout, add the cover field and a hint just after `self.desc_field`:

```python
            self.title_field,
            self.desc_field,
            self.cover_field,
            urwid.Text("  (filename in in/ used as the gallery cover; blank = first image)"),
            self.copyright_field,
```

- [ ] **Step 5: Run tests, verify they pass**

Run: `.venv/bin/python -m pytest tests/test_tui_widgets.py -v`
Expected: PASS (all; existing tab-cycle tests still pass with the extra field).

- [ ] **Step 6: Commit**

```bash
git add simplegals/tui/preview_panel.py tests/test_tui_widgets.py
git commit -m "feat(sgui): add cover image picker to gallery settings"
```

---

### Task 7: Version bump, docs, and full-suite verification

**Files:**
- Modify: `VERSION`
- Modify: `CLAUDE.md` (gallery settings table)
- (No test file changes)

**Interfaces:**
- Consumes: everything above.
- Produces: a release-ready `0.3.1` tree with green tests and lint.

- [ ] **Step 1: Bump VERSION**

Set the sole contents of `VERSION` to `0.3.1` (bare, no `v`, no trailing newline is the existing convention).

- [ ] **Step 2: Reinstall so `__version__` reflects the bump**

Run: `.venv/bin/pip install -e . -q`
Rationale: `simplegals.__version__` reads installed package metadata; the reinstall makes the branding and manifest stamp `0.3.1` in real runs. (Tests use `__version__` dynamically, so they pass either way.)

- [ ] **Step 3: Document the `cover` setting**

In `CLAUDE.md`, in the "Gallery settings (`ProjectConfig`)" table, add a row (place it near `title`/`description`):

```markdown
| `cover` | `str` | `""` | Filename in `in/` used as the gallery cover (portfolio thumbnail and gallery-index `og:image`); blank uses the first image |
```

- [ ] **Step 4: Run the full suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS (all; original suite plus the new cover/manifest/branding/sgui tests).

- [ ] **Step 5: Commit**

```bash
git add VERSION CLAUDE.md
git commit -m "release: bump VERSION to 0.3.1 and document cover setting"
```

- [ ] **Step 6: Release (manual, after review)**

Tag and publish once the branch is merged and PyPI trusted publishing is confirmed for the current repo owner (see the initiative design's runbook). The bare version, tag, and Release name are all `0.3.1`; `publish.yml` fails if the tag does not equal `VERSION`.

---

## Self-Review

**Spec coverage:**
- Cover field (spec Feature 1) -> Task 1; cover resolution + default + missing-warning -> Tasks 2 (`resolve_cover`) and 5 (warning in `build`).
- `gallery.json` manifest (Feature 2) -> Task 5, all schema fields covered.
- sgui cover picker (Feature 3) -> Task 6.
- Version in opt-in promo (Feature 4) -> Task 3.
- Always-on generator branding: meta + top/bottom comments (Feature 5) -> Task 3.
- Gallery index `og:image` uses the cover (resolved decision) -> Task 4.
- Bare version, org URL, no em-dashes, no co-author (global constraints) -> honored in Task 3 copy, Task 7, and every commit message.

**Placeholder scan:** No TBD/TODO; every code and test step contains complete content.

**Type consistency:** `resolve_cover(cover_name, records)` signature is identical in Tasks 2, 4, 5. Context keys `version`, `project_url`, `cover_og_path` are defined in Task 3/4 and consumed by the same-named template variables. Manifest keys in Task 5 match the spec schema. `cover_field` is defined and consumed only within Task 6.
