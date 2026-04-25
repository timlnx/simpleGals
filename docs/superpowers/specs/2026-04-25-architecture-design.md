# simpleGals — Architecture Design

**2026-04-25**

---

The architecture is: one shared core library, two thin entry points. `cli.py` parses argparse. `tui.py` stands up a urwid app. Everything that actually matters lives in `simplegals/core/`.

This document is the authoritative record of how the pieces fit together. It covers the config storage strategy, metadata/caching, the image processing pipeline, the parallel worker setup, and how `sgui` is structured internally. The keyboard reference is at the end because I will definitely forget my own keybindings.

---

## Proof of concept goals

This initial build serves two purposes simultaneously. The first is obvious — get simpleGals working. The second is that simpleGals is the real-world integration test for the bitmath 2.0.0 pre-release refactoring. bitmath 2.0.0 does not exist on PyPI yet. We're installing it from `/Users/tbielawa/Projects/bitmath` during prototyping, and every place we print a file size or process a byte count is a live test of that release.

The publish sequence is strict and non-negotiable:

1. Build simpleGals prototype, validate bitmath 2.0.0 functionality
2. Publish bitmath 2.0.0 to PyPI (separately)
3. Update `pyproject.toml` to `bitmath>=2.0.0` from PyPI
4. Create the initial public GitHub project for simpleGals

Do NOT push simpleGals to GitHub before this sequence completes.

---

## Testing

Tests live in `tests/` at the project root. The runner is `pytest`. The platform matrix runs on GitHub Actions runners: `macos-latest`, `ubuntu-latest`, and `windows-latest` — all three on every push.

```
tests/
    conftest.py             # shared fixtures (tmp dirs, config factories, asset paths)
    assets/
        TEST.jpg            # full-size JPEG for resize, thumbnail, and cache tests
        TEST.png            # full-size PNG for the same
    test_config.py          # config load/merge/init/write
    test_metadata.py        # sidecar r/w, staleness algorithm
    test_processor.py       # thumbnail generation, output image, EXIF injection
    test_gallery.py         # build orchestration, task list generation
    test_template.py        # Jinja2 render output, pagination, all-page
```

Standard library only for test infrastructure — no third-party test helpers beyond `pytest` and `pytest-cov`. Use `pathlib.Path` throughout; no hardcoded path separators. Tests against `TEST.jpg` and `TEST.png` in `tests/assets/` cover the real Pillow operations against real image data.

## Documentation

Docs are built with Sphinx + MyST Parser (Markdown source) and hosted on ReadTheDocs. Configuration lives in `docs/conf.py`; the ReadTheDocs build config is `.readthedocs.yaml` at the project root. Theme is `sphinx-rtd-theme`.

**Build locally:**

```bash
pip install -e ".[docs]"
cd docs && make html
# output at docs/_build/html/index.html
```

**Live-reload dev server** (auto-rebuilds on save, served at `http://127.0.0.1:8000`):

```bash
cd docs && make live
```

The docs build job runs on `ubuntu-latest` in CI alongside the test matrix. `docs/superpowers/` (design specs and internal planning) is excluded from the Sphinx build via `exclude_patterns` in `conf.py`.

---

## Package structure

```
simplegals/
    cli.py                  # entry point: simpleGals
    tui.py                  # entry point: sgui
    core/
        config.py           # XDG global config + per-gallery simpleGal.json
        metadata.py         # sidecar r/w, staleness checks
        processor.py        # Pillow: thumbnails, output images, EXIF
        template.py         # Jinja2 rendering
        gallery.py          # build orchestrator, dispatches workers
    workers/
        pool.py             # concurrent.futures.ProcessPoolExecutor
        progress.py         # shared progress state
    tui/
        app.py              # urwid layout and event loop
        file_panel.py       # left panel: scrollable image list, marquee scroll
        preview_panel.py    # right panel: term-image preview + settings
        progress_bar.py     # worker queue visualization during builds
        state.py            # staged changes model
    template/
        style.css           # CSS settings
        page.html.j2        # table view template file (used for each paginated page and the 'all' page with default gallery-size preview, each item in the table links to matching generated item.html page w/ medium-size preview
        item.html.j2        # individual gallery item page with medium-size preview, links to full-size image

```

The core has no knowledge of whether a CLI or a TUI is running it. `gallery.py` doesn't import anything from `tui/`. Progress state flows out of the worker pool through a queue; whoever is listening decides what to do with it.

---

## Build flow

When either entry point kicks off a gallery build, the execution path is the same:

1. `config.py` loads the merged config (global defaults overlaid with project overrides from `simpleGal.json`)
2. `gallery.py: build(project_dir, config)` takes over
3. `metadata.py` scans `in/`, loads each image's sidecar (if it exists), and checks staleness (see "Metadata and caching" below)
4. Stale images are sorted into two independent task lists: `thumb_tasks` (need `.meta/<filename>_thumb.<ext>` regenerated) and `output_tasks` (need `out/<filename>.<ext>` and `out/<filename>_thumb.<ext>` regenerated)
5. Both lists go to the worker pool simultaneously — they are independent and can run in parallel with each other
6. `processor.py` runs in each worker (Pillow ops, no shared state between workers)
7. Workers post status objects to a `multiprocessing.Queue`; the main thread drains it and passes updates to the frontend
8. As workers complete, `metadata.py` writes the updated sidecar for each finished image
9. Once all processing is done, `template.py` renders the Jinja2 HTML into `out/`

Step 9 is intentionally last. The template engine needs the full set of output image paths, captions, and alt text before it can render. `template.py` produces:

- `out/index.html` — the main entry page; first paginated view, links to `all.html`
- `out/page-N.html` — paginated pages sized by `layout.rows × layout.columns` images per page
- `out/all.html` — single-page view of all included images; respects `layout.columns` but ignores `layout.rows`; linked from `index.html`
- `out/<filename>_item.html` — per-image pages (medium-size preview, filename, date, size, Next/Previous)

`page.html.j2` is reused for both paginated pages and `all.html` — just different context (all images vs. one page's worth, pagination controls vs. none). Don't try to stream the render.

The `in/`, `out/`, and `.meta/` directories are created automatically on first run if they don't exist.

---

## Config system

Two layers, merged at runtime. The global config holds UI preferences; the project config holds gallery content and publishing settings. Neither should contain the other's concerns.

### Global config (sgui preferences)

Stored at the platform-appropriate location:

- **Linux**: `$XDG_CONFIG_HOME/simplegals/config.json` (falls back to `~/.config/simplegals/config.json` if `XDG_CONFIG_HOME` is unset)
- **macOS**: `~/Library/Application Support/simplegals/config.json`
- **Windows**: `%APPDATA%\simplegals\config.json`

This file holds `sgui` UI preferences: `file_panel_width`, `scroll_rate`, `preview_delay`. The batch CLI never reads or writes it. `sgui` writes to it when you change a UI setting.

### Per-gallery project config

`simpleGal.json` in the gallery's working directory by default. Override the path at runtime with `-c|--config <path>`. `sgui` reads and writes this file through the same `config.py` interface the CLI uses.

```json
{
  "title": "Summer 2026",
  "description": "Some photos from the summer.",
  "layout": {
    "columns": 4,
    "rows": 5
  },
  "quality": 90,
  "copyright": "© 2026 timlnx",
  "template": null,
  "images": {
    "IMG_1234.jpg": {
      "caption": "Sunset at the lake",
      "alt": "Orange sky over still water",
      "include": true
    }
  }
}
```

`template` is `null` unless you're pointing at a custom Jinja2 template directory. `images` is where per-image captions, alt text, and include/exclude flags live — NOT in the sidecar. The sidecar is a build cache artifact. Human-meaningful content belongs in the config you can read, edit by hand, and version-control.

Generate a stub config with `simpleGals --init`. `sgui` calls the same `config.py: init_project()` function when initializing a new project from the TUI — same result, different entry point.

---

## Metadata and caching

Avoiding unnecessary thumbnail regeneration is pretty much the whole point of `.meta/`. Nobody wants to wait through a 400-image gallery re-process because they tweaked a caption.

Each source image gets a sidecar at `.meta/<filename>.json`. Flat in `.meta/`, no subdirectories. (I tried a `sidecars/` subdir for about ten seconds before deciding it was pointless nesting that added zero value.)

```json
{
  "source": "IMG_1234.jpg",
  "mtime": "2026-04-25T15:30:00+00:00",
  "sha256": "abc123...",
  "settings_hash": "def456...",
  "thumb": {
    "path": ".meta/IMG_1234_thumb.jpg",
    "generated_at": "2026-04-25T15:30:01+00:00"
  },
  "output": {
    "path": "out/IMG_1234.jpg",
    "thumb_path": "out/IMG_1234_thumb.jpg",
    "generated_at": "2026-04-25T15:30:02+00:00"
  }
}
```

All timestamps are RFC 3339 — ISO 8601 format with UTC offset (e.g., `2026-04-25T15:30:00+00:00`). Python's `datetime.now(timezone.utc).isoformat()` produces this exactly. `settings_hash` is a hash of the publishing-relevant fields from `simpleGal.json` at the time the output was last generated — specifically `quality`, `copyright`, and `template`. Hashing the entire file would cause caption edits to invalidate output images, which is not what we want.

**Staleness check order** (short-circuits on first hit):

1. No sidecar → stale; generate everything
2. `mtime` unchanged → fresh; skip
3. `mtime` changed but `sha256` matches → still fresh (file was touched but content is identical); update the stored mtime and move on
4. `sha256` changed → stale; regenerate
5. `settings_hash` differs from current config hash → output is stale; thumb may still be fresh

Thumb staleness and output staleness are tracked independently. Changing a publishing setting only invalidates output images, not the `.meta/` previews `sgui` uses for display. That distinction saves a lot of time on repeat builds.

There is also a `.meta/build.jsonl` build log — one JSON object appended per completed build run (timestamp, images processed, errors, duration). Grep-friendly, appendable, easy to tail. Useful for debugging "why did that take so long."

---

## Image processing pipeline

`processor.py` does two distinct kinds of work. Keep them conceptually separate even though they both use Pillow.

### sgui preview thumbnails (`.meta/<filename>_thumb.<ext>`)

Open source image with Pillow, `thumbnail()` to fit within configured max dimensions (default: 300×300px). Save to `.meta/`. These are for displaying in the terminal via `term-image` and are NOT subject to publishing settings — quality is fixed at a reasonable value. PNG sources produce PNG previews; JPG sources produce JPG previews.

### Output images and HTML thumbnails

Open source image with Pillow. Apply publishing settings from `simpleGal.json`:

- **`quality`**: 0–100, applies to all output formats (Pillow maps this to JPEG quality or PNG compression level internally)
- **`copyright`**: injected as EXIF copyright field via `piexif`

Output full-size image → `out/<filename>.<ext>`. Output thumbnail (sized for the HTML gallery index) → `out/<filename>_thumb.<ext>`, next to it. Both PNG and JPG are supported.

The EXIF copyright injection on PNG files is a bit awkward (PNG doesn't handle EXIF the same way JPEG does), but Pillow manages it. Whether every image viewer reads it correctly is a question for later.

Publishing settings are intentionally kept minimal for now. Additional EXIF fields, and other deep-in-the-weeds options can be added to `simpleGal.json` without touching the core architecture — `processor.py` just reads whatever is in the config.

Template pages will have the image centered after a simple header with the gallery game. Next and Previous buttons below the image. Original file name, date, and size (using bitmath.best_prefix with 2 digits of precision)

---

## Worker pool and progress

Any processing messages including file sizes use the bitmath library with .best_prefix() applied with precision set to 2 digits. File sizes are read using bitmath.getsize(path, bestprefix=True)

Image processing is CPU-bound. `concurrent.futures.ProcessPoolExecutor` is the right call here — not threads. Pillow ops are heavy enough that the GIL would eat the parallelism gains. Each worker calls `processor.py` functions with no shared state; the only communication back to the main process is through a `multiprocessing.Queue`.

Workers post a small status object after each task:

```json
{"type": "thumb|output", "file": "IMG_1234.jpg", "status": "done|error", "ts": "2026-04-25T15:30:01+00:00"}
```

`workers/progress.py` maintains running counts (total, completed, failed, in-flight) from the queue. Both entry points read from the same state:

- **CLI**: renders a text progress bar to stdout, one line per worker queue (output tasks, thumb tasks)
- **sgui**: a background thread drains the queue and injects updates into urwid's event loop via a `pipe` file descriptor — that's urwid's mechanism for pushing events from outside the main loop without polling. The RightPanel switches to a progress view during a build: one bar for output tasks, one for thumbnail tasks, filenames ticking by as workers complete them

The little worker queue bar charts during a build are honestly the best part of this and I stand by spending time on them.

---

## sgui TUI

Built on urwid. The reference TUI for `term-image` is [termvisage](https://github.com/AnonymouX47/termvisage), which is also urwid-based. That's the main reason we're here instead of Textual. Textual looks nicer on the surface but takes over the terminal canvas in a way that fights `term-image`'s graphics protocols (Kitty, iTerm2). I didn't want to debug that. urwid is battle-tested for exactly this use case.

### Layout

```
Frame
├── header bar  (app name, current project path)
├── body: Columns
│     ├── left  [file_panel_width]: FilePanel
│     └── right [remainder]: RightPanel
│           ├── top: PreviewWidget  (UrwidImage from term-image, capped at 55% of panel)
│           └── bottom: SettingsPanel  (image mode or gallery mode)
└── footer bar  (key hints)
```

`term-image` ships a `UrwidImage` widget class — urwid integration is first-class in the library. `PreviewWidget` wraps it and caps rendering at 55% of the RightPanel's available width and height.

### FilePanel

`urwid.ListBox` + `urwid.SimpleListWalker`, one row per image found in `in/`. Filenames are truncated to panel width. When a row is selected and the name was truncated, a timer drives marquee scroll at `scroll_rate` chars/sec. `urwid.set_alarm_in` handles this in the main loop — no threads needed for this part.

### Preview delay

On selection change, cancel any pending preview timer and start a new one (`preview_delay` ms, default 75ms). When the timer fires: if `.meta/<filename>_thumb.<ext>` is fresh, display immediately. If it doesn't exist or is stale, run a single-threaded Pillow thumbnail generation inline (it's fast), write the sidecar, display. On-demand previews in `sgui` do NOT go through the worker pool — that's for batch builds only.

### Focus and mode model

The RightPanel has two modes:

- **Image mode**: preview + per-image properties for the selected file (caption, alt text, include/exclude, Save/Revert buttons)
- **Gallery mode**: gallery-level settings (title, description, columns, template path, quality, copyright)

Mode is a simple enum in app state, toggled by `Ctrl+G`. The SettingsPanel re-renders accordingly; the PreviewWidget stays visible in both modes.

Entering the RightPanel is intentional — you press `Enter` from the FilePanel to open the selected image in the RightPanel. `Escape` returns focus to the FilePanel. `Tab` cycles through interactive elements (input fields, buttons) within the RightPanel.

```
[ caption field      ]
[ alt text field     ]
[ include  ✓/✗      ]
< Save >  < Revert >
```

### Staged changes model (`tui/state.py`)

Nothing hits disk until you tell it to. All edits are staged in memory:

```python
staged: dict[str, dict[str, StagedValue]]
# key: image filename, or "gallery" for gallery-level settings
# StagedValue: dataclass with `new` and `original` fields
```

Staged items show a `*` dirty indicator in the FilePanel row and in the settings panel header. **Revert** (Tab to the button, activate with Space or Enter) removes the item's entry from `staged` and snaps fields back to their original values. **Save** (button or `Ctrl+S`) writes just that item's changes to `simpleGal.json` and removes its entry from `staged`. `Ctrl+|` writes everything in `staged` in one pass and clears the whole dict. `Ctrl+Q` with a non-empty `staged` prompts: save all, discard, or cancel.

---

## Keyboard reference

| Key | Context | Action |
|---|---|---|
| `↑` or `Ctrl+P` | FilePanel focused | Navigate up |
| `↓` or `Ctrl+N` | FilePanel focused | Navigate down |
| `Enter` | FilePanel focused | Move focus into RightPanel (image mode) |
| `Tab` | RightPanel focused | Cycle through fields and buttons |
| `Escape` | RightPanel focused | Return focus to FilePanel |
| `Ctrl+G` | Anywhere | Toggle image mode / gallery settings mode |
| `Ctrl+S` | Anywhere | Save current item's staged changes |
| `Ctrl+|` | Anywhere | Write all staged settings to disk |
| `Ctrl+Q` | Anywhere | Quit (prompts if staged changes exist) |

Footer hint string: `↑↓/^P^N navigate · Enter open · Tab cycle · Esc back · ^G settings · ^| save all · ^Q quit`

---

## See also

- [term-image](https://github.com/AnonymouX47/term-image) — terminal image rendering library; read this before touching `PreviewWidget`
- [termvisage](https://github.com/AnonymouX47/termvisage) — the reference urwid TUI built on term-image; worth studying before writing `tui/`
- [urwid](https://urwid.org/) — TUI framework docs, particularly the section on `pipe` and external event injection
- [Jinja2](https://jinja.palletsprojects.com/) — template engine; the available template context variables will be documented separately once the template system is built
- [piexif](https://piexif.readthedocs.io/) — EXIF manipulation paired with Pillow; used for copyright injection
- [bitmath](https://github.com/timlnx/bitmath/) - File size printing and parsing library
