# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`simpleGals` is a command-line static HTML image gallery generator. It takes directories of images and produces simple HTML files with thumbnails. There are two entry points:

- `simpleGals` — batch-mode CLI
- `sgui` — interactive TUI setup utility

Both commands operate in the current working directory, auto-creating `in/` (input images), `out/` (generated HTML), and `.meta/` (image metadata/cache).

## Tech Stack

- Python >= 3.10
- [`term-image`](https://github.com/AnonymouX47/term-image) for terminal image rendering (requires Kitty graphics protocol, iTerm2 inline image protocol, or Unicode truecolor support)

## Planned Architecture

- **`sgui`**: TUI with a split layout — scrollable file tree (left, ~20% width) and settings/preview panel (right). Navigation via arrow keys and Tab to switch focus. Escape toggles between image selection mode and general gallery settings.
- **Template system**: A default HTML template ships with the tool; users can fork it and point to a custom template via `--template/-t <TEMPLATE_DIR>` or the `sgui` settings panel.
- **Thumbnail caching**: `.meta/` stores image metadata and cached thumbnails. On repeat runs, thumbnails are regenerated only when the input file's last-modified time has changed.
- **Preview behavior**: A configurable delay (`preview_delay`, default 75ms) prevents rapid thumbnail generation while paging through files. First-load generates and caches; subsequent views are instant if unchanged.

## Key Configuration Settings (in `sgui`)

| Setting | Type | Default | Description |
|---|---|---|---|
| `file_panel_width` | `int` or `int%` | `30` | Width of the file tree panel |
| `scroll_rate` | `float` | `2.0` | Marquee scroll rate (chars/sec) for truncated filenames |
| `preview_delay` | `int` (ms) | `75` | Delay before generating a thumbnail for the first time |
