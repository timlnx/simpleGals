# simpleGals Demo Site (simplegals.github.io): Design

Date: 2026-07-09
Status: approved (brainstorming), pending spec review
Parent: 2026-07-09-simplegals-demo-initiative-design.md
Sub-project: 2 of the demo initiative (the showcase/portfolio site)
Depends on: simpleGals 0.4.0 (template assets + item position context), live on PyPI.

## Summary

A static GitHub Pages site, `simplegals.github.io`, that showcases one photo set
rendered three ways by simpleGals: a dark theme (stock), a bright inverse (forked
CSS), and "retro-fruit", a 1:1 revival of a 2010 Apple-style web gallery rebuilt
as a custom template. A branded landing page ("simpleGals Showcase") presents the
three galleries as cards. Everything derived is built fresh in CI; only source
originals live in git. The landing generator (`build_index.py`) consumes only
each gallery's `out/gallery.json` plus a site-level `site.json`, seeding a future
meta-gallery tool.

## Goal (from the initiative)

- Showcase real galleries built by the tool, including at least one custom
  template override.
- Rebuild automatically against the newest published simpleGals.
- Keep the repo lean: only source originals in git, never derived output.
- Define a machine-readable per-gallery data contract the landing consumes
  (already shipped: `out/gallery.json`).

## Locked decisions

From the initiative and this brainstorm:

- New repo named exactly `simplegals.github.io` (lowercase; required to serve at
  the org root). Prototyped locally at `/Users/tbielawa/Projects/simplegals.github.io`
  until wired to the `simpleGals` org.
- One shared input folder, symlinked into each gallery. Hook: "same photos, three
  ways".
- Three galleries: `dark` (stock template), `bright` (forked CSS), `retro-fruit`
  (custom template). Retro is the required custom-template override.
- Landing = "Direction A / Nightfall": dark editorial hero (wordmark + tagline +
  pitch + stats chip over a hero photo), a 3-up row of gallery cards, a fold, and
  a below-the-fold "how it's built" section, then a footer. Locked visually via
  the brainstorming visual companion.
- Deploy via GitHub Actions Pages artifact (no `gh-pages`, no Jekyll).
- Per-gallery `site_url = https://simplegals.github.io/<slug>/`.

## Repository layout

```
shared/in/*.jpg                 # the ONE photo set; the only binaries in git
galleries/
  dark/simpleGal.json           # in -> ../../shared/in  (relative symlink)
  bright/simpleGal.json         #   "         "
  retro-fruit/simpleGal.json    #   "         "
templates/
  index.html.j2                 # the landing (build_index.py renders this)
  bright/                       # page.html.j2, item.html.j2 (copied from stock), style.css (light)
  retro-fruit/                  # page.html.j2, item.html.j2, assets/*.png (18 slices)
site.json                       # landing config
build_index.py                  # renders index.html + assembles _site/
.github/workflows/pages.yml
.gitignore                      # out/  .meta/  .superpowers/  __pycache__/
README.md
```

Each `galleries/<slug>/in` is a relative symlink to `../../shared/in`, committed
to git (git stores symlinks; the Ubuntu runner preserves them; simpleGals reads
through them). Per-gallery `out/` and `.meta/` are generated and gitignored, so
the same input yields three different rendered galleries.

## Shared input and placeholder images

`shared/in/` holds 36 throwaway synthetic JPEGs generated with Pillow (varied
solid/gradient backgrounds, varied dimensions, each labeled with its index) so
every gallery paginates: dark/bright at 4x5 = 20/page (2 pages), retro at 3x10 =
30/page (2 pages). These are replaced wholesale when real photos are dropped into
`shared/in/`; nothing else changes. A `shared/in/README.md` explains this.

## The three galleries

Each `simpleGal.json` sets `title`, `site_url = https://simplegals.github.io/<slug>/`,
and a `cover`. Same shared input, different presentation.

| slug | template | columns x rows | social_previews | exif_display | title |
|---|---|---|---|---|---|
| `dark` | builtin (stock) | 4 x 5 | true | true | `Dark` |
| `bright` | `../../templates/bright` | 4 x 5 | true | true | `Bright` |
| `retro-fruit` | `../../templates/retro-fruit` | 3 x 10 | false | false | `Retro-fruit` |

The `template` value is relative to the gallery directory (CI runs
`simpleGals build --force` with cwd = the gallery dir; the processor resolves
`config.template` against cwd).

`cover`: each gallery names a cover from the shared set. The `dark` cover is the
representative shot AND the site hero (see Hero). For the prototype, `dark` and
`bright` share one cover; `retro-fruit` names a different one, so the demo shows
cover selection varying per gallery. All three are trivially swappable once real
photos land. The plan pins the exact placeholder filenames.

## The `bright` template

`bright` cannot override only CSS: the `template` field swaps the whole template
directory. So `templates/bright/` contains `page.html.j2` and `item.html.j2`
copied verbatim from the stock template plus a light `style.css` (the inverse
palette: light background, dark text, inverted accents). This duplication is
deliberate: it doubles as a working demo of "fork the template and restyle." A
comment at the top of each copied `.j2` notes it is a fork of the stock template
for the demo.

## The `retro-fruit` template (1:1 revival)

A faithful reproduction of the 2010 export at
`/Users/tbielawa/Projects/Minecraft-GrandLibrary`, expressed as a simpleGals
custom template. Source characteristics: HTML 4.01 table markup, no CSS, styled
entirely by 18 sliced PNGs; a gradient nav bar with prev/next/home image buttons
(state `0` = disabled, `1` = enabled) and an "N images" counter; a 3-column grid
of 9-slice rounded thumbnail boxes at 30/page; item pages showing the full image
with "Page: N of M (P%)".

Assets: copy the 18 `Resources/*.png` slices verbatim into
`templates/retro-fruit/assets/` (`top_left`, `top_middle`, `top_right`, `left`,
`right`, `bottom_left`, `bottom_middle`, `bottom_right`, `bottom_left_2`,
`bottom_middle_2`, `bottom_right_2`, `bottom_middle_stretch`, `button_gradient`,
`home`, `next0`, `next1`, `previous0`, `previous1`). simpleGals 0.4.0 copies
`assets/` to `out/assets/`; the template references them as `assets/<name>.png`.
No `style.css` (0.4.0 makes it optional).

`page.html.j2` (grid): reproduce the original top nav table
(`background="assets/button_gradient.png"`) with:
- previous button: `assets/previous1.png` linking to the prior grid page
  (`index.html` when going to page 1, else `page-{{ current_page - 1 }}.html`)
  when `current_page > 1`, else `assets/previous0.png` (no link).
- next button: `assets/next1.png` linking to `page-{{ current_page + 1 }}.html`
  when `current_page < total_pages`, else `assets/next0.png`.
- home button: `assets/home.png` linking to `index.html`.
- right-aligned `{{ total_images }}&nbsp;images`.
Then the centered `<h2>{{ title }}</h2>`, then the 3-column table of 9-slice
rounded boxes, each cell wrapping `<a href="{{ image.item_page }}"><img width=240
src="{{ image.thumb_path }}"></a>` in the slice-image scaffold, looping over
`images` three per row.

`item.html.j2`: the same nav bar, but previous/next keyed off `prev_image` /
`next_image` (present -> `previous1`/`next1` linking to `prev_image.item_page` /
`next_image.item_page`; absent -> `previous0`/`next0`), home to `index.html`.
Below: the display image `<img src="{{ image.display_path }}">`. Below that:
`Page: {{ image_number }} of {{ total_images }} ({{ percent }}%)`.

Filenames follow simpleGals conventions (`index.html`, `page-N.html`,
`<stem>_item.html`), not the original's (`index2.html`, `Pages/N.html`); the look
is what is reproduced 1:1, not the file naming.

Branding: the retro `.j2` files include the invisible simpleGals generator
markers (the `<meta name="generator">` and the top/bottom HTML comments) to keep
branding consistent across templates. These are invisible and do not alter the
2010 visual reproduction.

## `site.json`

Landing configuration consumed by `build_index.py` (this is site config, not a
simpleGals output; `build_index.py` still reads only `gallery.json` for
per-gallery data):

```json
{
  "title": "simpleGals Showcase",
  "tagline": "the same photos, three ways",
  "pitch": "A tiny static-HTML gallery generator. One photo set below, rendered by three templates: a dark theme, its bright inverse, and a 2010 revival brought back to life.",
  "chip": "3 templates · same photo set · rebuilt on every release",
  "hero_gallery": "dark",
  "galleries": [
    { "slug": "dark",        "badge": "stock template",  "blurb": "The default simpleGals look: near-black, quiet, lets the photos glow." },
    { "slug": "bright",      "badge": "custom CSS",       "blurb": "The same layout inverted to dark-on-light. Airy, clean, gallery-wall bright." },
    { "slug": "retro-fruit", "badge": "custom template",  "blurb": "A 2010 Apple-style web gallery, rebuilt 1:1 from its original sliced-image chrome." }
  ],
  "links": [
    { "label": "View source on GitHub", "href": "https://github.com/simplegals/simplegals.github.io" },
    { "label": "simpleGals on PyPI",    "href": "https://pypi.org/project/simplegals/" },
    { "label": "Fork a template",       "href": "https://github.com/simplegals/simplegals.github.io/tree/main/templates/retro-fruit" }
  ]
}
```

The `galleries` array is the render order. Card `title`, cover image, and
`image_count` come from each gallery's `gallery.json`; `badge` and `blurb` come
from `site.json`.

## `templates/index.html.j2` (the landing)

Direction A, dark. Sections top to bottom:
1. Hero: dimmed hero photo background, `title` as a large light wordmark,
   `tagline`, `pitch`, and the `chip`. Hero image URL = the `hero_gallery`
   manifest's `cover_og` (1200px), served at `<hero_gallery>/<cover_og>`.
2. 3-up gallery cards: for each entry in `site.galleries`, a card with the cover
   image (`<slug>/<cover>` from the manifest), gallery `title`, the `badge`, the
   `blurb`, `image_count` photos, and a "View gallery ->" link to
   `<slug>/index.html`.
3. Fold: a hairline divider and a downward chevron.
4. Below the fold: "How the showcase is built" / "One folder in, three sites out"
   plus three numbered steps and the `links` row.
5. Footer: "Built with simpleGals <version> | source on GitHub". Version is read
   from the installed simplegals (`simplegals.__version__`).

Standard head: `<meta name="viewport">`, `<title>{{ title }}</title>`, OG/Twitter
tags using the hero image and `site_url` root, and an emoji favicon via an inline
`data:` SVG URI (no binary asset to commit).

## `build_index.py`

A single script, standard library plus Jinja2 (already available via simpleGals).
Responsibilities:
1. Read `site.json`.
2. For each gallery in `site.galleries`, read `galleries/<slug>/out/gallery.json`
   (fields used: `title`, `description`, `cover`, `cover_og`, `image_count`,
   `slug`). It never constructs simpleGals output filenames itself; it uses the
   manifest's `cover` / `cover_og` values.
3. Render `templates/index.html.j2` with the site config and the assembled card
   list, plus the resolved hero image path.
4. Assemble the deploy tree into `_site/`: write `_site/index.html`, and copy each
   `galleries/<slug>/out/` to `_site/<slug>/`.

Invocation: `python build_index.py` (assembles into `./_site`). A `--out` flag
may set the target dir. It fails loudly if a referenced gallery is missing its
`out/gallery.json` (a gallery was not built).

## CI: `.github/workflows/pages.yml`

- Triggers: `push` to `main`, `workflow_dispatch`, and
  `repository_dispatch: { types: [simplegals-release] }` (the cross-repo trigger;
  the sending half lives in the tool repo and is sub-project 3).
- Permissions: `pages: write`, `id-token: write`. Concurrency group `pages`.
- Steps: `actions/checkout@v4` -> `actions/setup-python@v5` (3.12) ->
  `pip install "simplegals>=0.4.0"` -> for each `galleries/*/`: `cd` in and
  `simpleGals build --force` -> `python build_index.py` -> `actions/configure-pages`
  -> `actions/upload-pages-artifact@v3` with `path: _site` -> deploy job with
  `actions/deploy-pages@v4`.

Note the CLI is `simpleGals build --force` (capital G, `build` subcommand;
`--force` is on `build`, not the top level). On the case-sensitive Linux runner
only `simpleGals` resolves.

## Local prototyping and verification

Before the org repo exists, the whole site builds and is verifiable locally:
1. Generate the 36 placeholder images into `shared/in/`.
2. Create the relative symlinks.
3. In each `galleries/<slug>/`, run `simpleGals build --force` against the local
   `simplegals>=0.4.0`.
4. `python build_index.py`, then open `_site/index.html` and each
   `_site/<slug>/index.html` to confirm the landing, the three galleries, retro
   pagination, retro item pages ("Page N of M (P%)"), and that `_site/<slug>/assets/`
   exists for retro.

Automated checks (pytest, in the site repo):
- `build_index.py`: given a fixtures tree of fake `site.json` + a couple of
  `out/gallery.json` files, it renders an `index.html` containing each card's
  title/badge/blurb/link and the hero path, and assembles `_site/<slug>/`.
- A smoke test that the retro template renders (via simpleGals `render_gallery`
  with `template` pointing at `templates/retro-fruit/`) and that `out/assets/`
  contains the slice PNGs and an item page contains "Page: 1 of".

## `.gitignore`, `README`

`.gitignore`: `out/`, `.meta/`, `.superpowers/`, `__pycache__/`, `_site/`.
`README.md`: what the site is, how to add real photos (drop into `shared/in/`,
optionally set each gallery's `cover`), how to build locally, and how CI deploys.

## Non-goals

- No meta-gallery tool. `build_index.py` is its seed, not the product.
- No new simpleGals features. Everything needed shipped in 0.4.0.
- No org transfer or cross-repo dispatch wiring here. The `repository_dispatch`
  listener is included in `pages.yml`, but the sending side (tool repo
  `notify-site` job + `SITE_DISPATCH_TOKEN`) is sub-project 3 (the runbook).

## Backlog (deferred, do not build now)

- A richer per-gallery description override so the retro-fruit presentation can
  explain that its disabled features (social previews, EXIF) can be turned back
  on. For now the showcase card uses the static `site.json` blurb; the mechanism
  is deferred by explicit request.
- Wiring the site to the org: rename/point the remote to
  `simplegals/simplegals.github.io`, enable Pages (Actions source), and connect
  the release dispatch (sub-project 3).

## Micro-defaults chosen (flag if you disagree)

- Hero image = the `dark` gallery's `cover_og` (1200px). "Choosing the hero" means
  setting `cover` in `dark/simpleGal.json`.
- Retro item pages show `image.display_path` (the web display image), not the
  full original.
- 36 placeholder images.
- Gallery titles `Dark` / `Bright` / `Retro-fruit`; card blurbs as shown in the
  approved landing mockup.

## See also

- [Demo initiative design](2026-07-09-simplegals-demo-initiative-design.md) (parent)
- [0.4.0 template extensibility](2026-07-09-simplegals-0.4.0-template-extensibility-design.md) (the dependency)
- [Org transfer runbook](2026-07-09-simplegals-org-transfer-runbook.md) (sub-project 3, the deploy wiring)
