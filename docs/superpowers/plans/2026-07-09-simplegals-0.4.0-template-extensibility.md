# simpleGals 0.4.0 Template Extensibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let custom simpleGals templates ship static assets and know each image's position, so a template can render with sliced images and "Page N of M (P%)".

**Architecture:** Three additive changes to one function, `render_gallery` in `simplegals/core/template.py`: make the `style.css` copy conditional, copy a template's `assets/` subdirectory into `out/assets/`, and add `image_number`/`total_images`/`percent` to the render context. No other modules change.

**Tech Stack:** Python >= 3.10, Jinja2, pytest. Assets copied with `shutil.copytree(..., dirs_exist_ok=True)`.

## Global Constraints

- Python >= 3.10. No new runtime dependencies.
- All changes are additive and backward compatible. The full existing test suite must stay green (currently ~205 tests); this release only adds tests.
- Asset copying uses an `assets/` subdirectory copied to `out/assets/`, not a flat copy of every file.
- `percent` is integer floor: `(image_number * 100) // total_images`. Image 1 of 89 renders `1`, image 2 renders `2`, the last image renders `100`.
- `css_path` stays the literal `"style.css"` regardless of whether the file exists.
- `VERSION` is a bare PEP 440 string, no `v` prefix, no trailing newline.
- Commits use conventional-commit prefixes (`feat:`, `test:`, `chore:`) to match repo history. Do NOT add any `Co-Authored-By` trailer or Claude/generated-by credit to any commit.
- Work happens on the `0.4.0` branch (already created; the spec is committed there as `d79ae1e`).

## File Structure

- `simplegals/core/template.py` (modify): `render_gallery` gains the conditional css copy, the assets copy, and the three context variables. This is the only source file touched.
- `tests/test_template.py` (modify): add a fixture-template helper and the new tests. Existing tests in this file are the regression guard (`test_render_gallery_copies_css` proves the default template still copies its css).
- `VERSION` (modify): `0.3.1` -> `0.4.0`, done last so the branding tests (which derive from `__version__`) are unaffected during feature work.

Reference: current `render_gallery` (`simplegals/core/template.py:52-129`). The css copy is lines 64-66; `base_ctx` is lines 77-94; the item loop is lines 117-127.

---

### Task 1: Shared fixture-template helper

**Files:**
- Test: `tests/test_template.py` (add one helper function near the top, after the existing `_make_records`)

**Interfaces:**
- Produces: `_make_template(dir_path, *, with_css, with_assets, page=..., item=...)` used by Tasks 1-3. Writes `page.html.j2` and `item.html.j2` (both required by `render_gallery`), and optionally `style.css` and an `assets/` tree.

- [ ] **Step 1: Add the fixture helper**

Add to `tests/test_template.py` (place it directly below `_make_records`):

```python
_FIXTURE_PAGE = "PAGE total={{ total_images }} {% for image in images %}{{ image.filename }} {% endfor %}"
_FIXTURE_ITEM = "ITEM n={{ image_number }} t={{ total_images }} p={{ percent }} f={{ image.filename }}"


def _make_template(dir_path, *, with_css, with_assets,
                   page=_FIXTURE_PAGE, item=_FIXTURE_ITEM):
    """Write a minimal custom template dir for render_gallery to consume."""
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "page.html.j2").write_text(page, encoding="utf-8")
    (dir_path / "item.html.j2").write_text(item, encoding="utf-8")
    if with_css:
        (dir_path / "style.css").write_text("body{}", encoding="utf-8")
    if with_assets:
        sub = dir_path / "assets" / "sub"
        sub.mkdir(parents=True, exist_ok=True)
        (dir_path / "assets" / "marker.png").write_bytes(b"PNG")
        (sub / "note.txt").write_text("hi", encoding="utf-8")
    return dir_path
```

- [ ] **Step 2: Confirm the suite still collects and passes**

Run: `.venv/bin/python -m pytest tests/test_template.py -q`
Expected: PASS (the helper is unused so far; this just verifies no syntax/import error).

- [ ] **Step 3: Commit**

```bash
git add tests/test_template.py
git commit -m "test(template): add custom-template fixture helper"
```

---

### Task 2: Make `style.css` optional

**Files:**
- Modify: `simplegals/core/template.py:64-66`
- Test: `tests/test_template.py`

**Interfaces:**
- Consumes: `_make_template` from Task 1.
- Produces: `render_gallery` no longer requires a `style.css` in the template dir.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_template.py`:

```python
def test_missing_style_css_does_not_crash(tmp_path):
    tpl = _make_template(tmp_path / "tpl", with_css=False, with_assets=False)
    out = tmp_path / "out"
    render_gallery(out, ProjectConfig(template=str(tpl)), _make_records(out, ["a.jpg"]))
    assert (out / "index.html").exists()
    assert not (out / "style.css").exists()


def test_style_css_copied_when_present(tmp_path):
    tpl = _make_template(tmp_path / "tpl", with_css=True, with_assets=False)
    out = tmp_path / "out"
    render_gallery(out, ProjectConfig(template=str(tpl)), _make_records(out, ["a.jpg"]))
    assert (out / "style.css").exists()
```

- [ ] **Step 2: Run tests to verify the first one fails**

Run: `.venv/bin/python -m pytest tests/test_template.py::test_missing_style_css_does_not_crash -v`
Expected: FAIL with `FileNotFoundError` (the current unconditional `shutil.copy` of a missing `style.css`).

- [ ] **Step 3: Make the css copy conditional**

In `simplegals/core/template.py`, replace lines 64-66:

```python
    css_src = tpl_dir / "style.css"
    css_dest = out_dir / "style.css"
    shutil.copy(css_src, css_dest)
```

with:

```python
    css_src = tpl_dir / "style.css"
    if css_src.exists():
        shutil.copy(css_src, out_dir / "style.css")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_template.py::test_missing_style_css_does_not_crash tests/test_template.py::test_style_css_copied_when_present tests/test_template.py::test_render_gallery_copies_css -v`
Expected: PASS (all three, including the existing default-template css test).

- [ ] **Step 5: Commit**

```bash
git add simplegals/core/template.py tests/test_template.py
git commit -m "feat(template): make style.css optional in templates"
```

---

### Task 3: Copy template `assets/` into `out/assets/`

**Files:**
- Modify: `simplegals/core/template.py` (add the assets copy immediately after the css block from Task 2)
- Test: `tests/test_template.py`

**Interfaces:**
- Consumes: `_make_template` from Task 1.
- Produces: a template's `assets/` tree is mirrored to `out/assets/`, structure preserved. Consumed later by the site's retro-fruit template (sub-project 2).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_template.py`:

```python
def test_template_assets_copied_recursively(tmp_path):
    tpl = _make_template(tmp_path / "tpl", with_css=False, with_assets=True)
    out = tmp_path / "out"
    render_gallery(out, ProjectConfig(template=str(tpl)), _make_records(out, ["a.jpg"]))
    assert (out / "assets" / "marker.png").exists()
    assert (out / "assets" / "sub" / "note.txt").exists()


def test_no_assets_dir_produces_no_output(tmp_path):
    tpl = _make_template(tmp_path / "tpl", with_css=False, with_assets=False)
    out = tmp_path / "out"
    render_gallery(out, ProjectConfig(template=str(tpl)), _make_records(out, ["a.jpg"]))
    assert not (out / "assets").exists()


def test_assets_copy_on_rebuild_does_not_fail(tmp_path):
    tpl = _make_template(tmp_path / "tpl", with_css=False, with_assets=True)
    out = tmp_path / "out"
    recs = _make_records(out, ["a.jpg"])
    render_gallery(out, ProjectConfig(template=str(tpl)), recs)
    render_gallery(out, ProjectConfig(template=str(tpl)), recs)  # rebuild into populated out/
    assert (out / "assets" / "marker.png").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_template.py::test_template_assets_copied_recursively -v`
Expected: FAIL (`out/assets/marker.png` does not exist; nothing copies it yet).

- [ ] **Step 3: Add the assets copy**

In `simplegals/core/template.py`, immediately after the css block (the `if css_src.exists():` block from Task 2), add:

```python
    assets_src = tpl_dir / "assets"
    if assets_src.is_dir():
        shutil.copytree(assets_src, out_dir / "assets", dirs_exist_ok=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_template.py::test_template_assets_copied_recursively tests/test_template.py::test_no_assets_dir_produces_no_output tests/test_template.py::test_assets_copy_on_rebuild_does_not_fail -v`
Expected: PASS (all three).

- [ ] **Step 5: Commit**

```bash
git add simplegals/core/template.py tests/test_template.py
git commit -m "feat(template): copy template assets/ into out/assets/"
```

---

### Task 4: Expose `image_number`, `total_images`, `percent`

**Files:**
- Modify: `simplegals/core/template.py` (`base_ctx` and the item loop)
- Test: `tests/test_template.py`

**Interfaces:**
- Consumes: `_make_template` from Task 1 (its item fixture emits `n={{ image_number }} t={{ total_images }} p={{ percent }}`, its page fixture emits `total={{ total_images }}`).
- Produces: item render context gains `image_number` (1-based) and `percent` (floor); `base_ctx` gains `total_images` (available to grid and item pages).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_template.py`:

```python
def test_item_position_context(tmp_path):
    tpl = _make_template(tmp_path / "tpl", with_css=False, with_assets=False)
    out = tmp_path / "out"
    render_gallery(out, ProjectConfig(template=str(tpl)), _make_records(out, ["a.jpg", "b.jpg", "c.jpg"]))
    assert "n=1 t=3 p=33" in (out / "a_item.html").read_text(encoding="utf-8")
    assert "n=3 t=3 p=100" in (out / "c_item.html").read_text(encoding="utf-8")


def test_percent_floor_matches_source_export(tmp_path):
    tpl = _make_template(tmp_path / "tpl", with_css=False, with_assets=False)
    out = tmp_path / "out"
    names = [f"{i}.jpg" for i in range(1, 90)]  # 89 images, mirrors the retro source
    render_gallery(out, ProjectConfig(template=str(tpl)), _make_records(out, names))
    assert "n=1 t=89 p=1" in (out / "1_item.html").read_text(encoding="utf-8")
    assert "n=2 t=89 p=2" in (out / "2_item.html").read_text(encoding="utf-8")


def test_total_images_on_grid_page(tmp_path):
    tpl = _make_template(tmp_path / "tpl", with_css=False, with_assets=False)
    out = tmp_path / "out"
    render_gallery(out, ProjectConfig(template=str(tpl)), _make_records(out, ["a.jpg", "b.jpg"]))
    assert "total=2" in (out / "index.html").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_template.py::test_item_position_context tests/test_template.py::test_total_images_on_grid_page -v`
Expected: FAIL (the fixture renders `n=` / `p=` / `total=` as empty because those context keys are undefined).

- [ ] **Step 3: Add `total_images` to `base_ctx`**

In `simplegals/core/template.py`, inside the `base_ctx = { ... }` dict, add a line (for example right after `"total_pages": total_pages,`):

```python
        "total_images": len(records),
```

- [ ] **Step 4: Add `image_number` and `percent` to the item loop**

In the `for i, record in enumerate(records):` loop, extend the `ctx` dict so it reads:

```python
        ctx = {
            **base_ctx,
            "image": record,
            "prev_image": records[i - 1] if i > 0 else None,
            "next_image": records[i + 1] if i < len(records) - 1 else None,
            "image_number": i + 1,
            "percent": (i + 1) * 100 // len(records),
        }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_template.py::test_item_position_context tests/test_template.py::test_percent_floor_matches_source_export tests/test_template.py::test_total_images_on_grid_page -v`
Expected: PASS (all three).

- [ ] **Step 6: Run the full suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS (every existing test plus the eight new ones).

- [ ] **Step 7: Commit**

```bash
git add simplegals/core/template.py tests/test_template.py
git commit -m "feat(template): expose image_number, total_images, percent to templates"
```

---

### Task 5: Bump `VERSION` to 0.4.0

**Files:**
- Modify: `VERSION`

**Interfaces:**
- Consumes: nothing.
- Produces: `simplegals.__version__ == "0.4.0"`, which flows into the generator meta tag, branding comments, and promo footer automatically.

- [ ] **Step 1: Bump the version**

Edit `VERSION`: replace `0.3.1` with `0.4.0`. Keep it a single line with no trailing newline.

- [ ] **Step 2: Verify the version is read correctly**

Run: `.venv/bin/python -c "import simplegals; print(simplegals.__version__)"`
Expected: `0.4.0`

- [ ] **Step 3: Run the full suite once more**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS (the branding tests derive from `__version__`, so they now assert `0.4.0` and stay green).

- [ ] **Step 4: Commit**

```bash
git add VERSION
git commit -m "chore: bump VERSION to 0.4.0"
```

---

## Release (manual, after the plan is complete and reviewed)

Not code tasks; the maintainer runs these:

1. Merge `0.4.0` into `main` (fast-forward, matching the 0.3.1 release).
2. Tag `0.4.0` and publish the GitHub Release. `publish.yml` verifies the tag equals `VERSION` and publishes to PyPI via trusted publishing.
3. Confirm `0.4.0` appears at https://pypi.org/project/simplegals/ .

Then sub-project 2 (the demo site) can `pip install "simplegals>=0.4.0"` and build the retro-fruit gallery against it.

## Self-Review

- **Spec coverage:** Feature 1 (asset copying) -> Task 3. Feature 2 (position context) -> Task 4. Feature 3 (optional style.css) -> Task 2. Backward compatibility (suite green) -> Task 4 Step 6 and Task 5 Step 3. Release steps -> Task 5 plus the manual Release section. Testing strategy items (recursive assets, no-assets no-op, rebuild, css present/absent, percent floor with 89, total on grid) -> Tasks 2-4. No gaps.
- **Placeholder scan:** none; every code and command step is concrete.
- **Type consistency:** `_make_template` signature and the fixture context keys (`total_images`, `image_number`, `percent`) match between the helper (Task 1) and their assertions (Tasks 2-4). The impl adds exactly those keys.
