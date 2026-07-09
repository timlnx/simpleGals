# simpleGals Org Transfer and Publish Re-point: Ops Runbook

Date: 2026-07-09
Status: draft
Owner: timlnx
Sub-project: 3 of the [demo initiative](2026-07-09-simplegals-demo-initiative-design.md)

Moving `timlnx/simpleGals` into its own `simplegals` org is the boring, scary
part of the whole demo initiative. Boring because it is mostly clicking around in
GitHub and PyPI settings. Scary because ONE of those clicks (the PyPI trusted
publisher) will quietly break the next release if you do it in the wrong order.
This runbook exists so future-me does it in the right order and does not spend an
evening staring at a red publish job wondering what happened.

Everything below is manual. There is no script. "Cross your fingers" shows up as
an actual step in one or two places.

## Who This Is For

You, holding all three of: admin on `timlnx/simpleGals`, the ability to create a
free GitHub org, and owner rights on the `simplegals` project on PyPI. If you are
missing any one of the three, stop and get it first. Nothing here works halfway.

## The One Rule That Matters

Read this before you touch anything.

**PyPI trusted publishing does NOT follow GitHub's redirects.** After the
transfer, Actions in the moved repo hands PyPI an OIDC token that says
`simplegals/simpleGals`. PyPI compares that string EXACTLY against the trusted
publisher on file, which today says `timlnx/simpleGals`. It will not match. The
next release publish fails with "not a trusted publisher" and uploads nothing.

The good news: a failed trusted-publish uploads nothing, so PyPI is never left
half-broken. You fix the publisher and re-run the release. The bad news is you
find out mid-release if you skip it. So the order below front-loads the publisher
fix: add the new publisher BEFORE the transfer, while the old one is still valid,
and you never have a window where publishing is dead.

## Do It in This Order

The design doc lists six steps; this expands them and reorders two so there is no
rework and no dead publish window.

### 1. Create the `simplegals` org

Why first: everything else needs a place to land. Free plan is fine for a public
tool and a public Pages site.

- github.com, top-right + menu, "New organization", Free plan.
- Org name: `simplegals` (lowercase; it becomes the URL prefix and, critically,
  the required prefix of the Pages repo name later).

Verify: `https://github.com/simplegals` loads and you are an owner.

### 2. Pre-add the new PyPI trusted publisher (BEFORE the transfer)

Why now instead of after: PyPI happily stores a trusted-publisher config for a
repo you do not own yet. Adding it while the old one still works means the moment
the transfer lands, publishing already succeeds. No window, no panic.

On PyPI: your account, the `simplegals` project, Manage, Publishing, "Add a new
publisher" (GitHub Actions):

- Owner: `simplegals`
- Repository: `simpleGals`
- Workflow name: `publish.yml`
- Environment: match whatever the current `timlnx/simpleGals` publisher uses. If
  the current one names an environment (for example `pypi`), use the SAME name.
  If it is blank, leave it blank. A mismatch here is its own silent failure.

Leave the OLD `timlnx/simpleGals` publisher in place for now. Having both is fine
and is the whole point.

Verify: the project's Publishing page lists two publishers, old and new.

### 3. Transfer `timlnx/simpleGals` into the org

Why: this is the actual move. GitHub sets up permanent redirects for web, API,
and git remotes, so existing clones and links keep working. Issues, PRs, stars,
watchers, tags, and releases come along.

- `timlnx/simpleGals`, Settings, Danger Zone, "Transfer ownership".
- New owner: `simplegals`. Type the repo name to confirm.

Verify: `https://github.com/simplegals/simpleGals` loads, and
`https://github.com/timlnx/simpleGals` redirects to it.

PROTIP: the redirect is a courtesy, not a crutch. Update your own clone so you are
not silently depending on it:

    git remote set-url origin git@github.com:simplegals/simpleGals.git
    git remote -v

### 4. Prove publishing still works, then remove the old publisher

Why: do NOT delete the `timlnx` publisher on faith. Confirm the new one actually
fires first.

The cheapest real test is the next patch release, but if you do not have one
ready, you can trigger `publish.yml` by cutting a throwaway pre-release tag and
release, or just wait for the next genuine `0.3.x`. When a release publishes:

- Watch the run: `gh run watch <run-id>` (or the Actions tab).
- The "Verify tag matches VERSION" step must pass (it already does; tag equals
  `VERSION`).
- The publish step must upload without a "not a trusted publisher" error.
- Confirm the new version appears at `https://pypi.org/project/simplegals/`.

ONLY after a green publish under `simplegals/simpleGals`: go back to PyPI and
delete the old `timlnx/simpleGals` trusted publisher. Now there is exactly one,
and it is correct.

### 5. Turn Actions and code scanning back on for the org

Why: brand-new orgs frequently default Actions to disabled or "require approval",
and repo-level security features can come across muted. A repo that built fine
under `timlnx` can sit there doing nothing under `simplegals` until you flip these.

- Org Settings, Actions, General: allow Actions (all, or selected + allow this
  repo). Confirm workflow permissions match what the release needs (the publish
  job needs `id-token: write` for OIDC; that is set in the workflow, but org
  policy can override it, so check "Workflow permissions").
- Code scanning: the repo runs a `CodeQL Security Scan`. If it is a committed
  workflow file it transferred with the repo and just needs Actions enabled. If
  it was GitHub "default setup", re-enable it under the repo's Security settings.

Verify: push a trivial commit (or re-run a workflow) and watch CI + CodeQL go
green under the new owner.

### 6. Create the `simplegals.github.io` site repo

Why: this is the home of sub-project 2 (the demo/portfolio site). The name is not
a suggestion.

- New repo in the `simplegals` org, named EXACTLY `simplegals.github.io`. Any
  other name will not serve at the org root URL.
- Public. No README/gitignore needed; the site sub-project scaffolds it.
- Settings, Pages, Source: GitHub Actions (NOT a `gh-pages` branch, NOT Jekyll).

Verify: the repo exists at `https://github.com/simplegals/simplegals.github.io`
and Pages is set to the Actions source.

### 7. Wire the cross-repo release trigger

Why: `GITHUB_TOKEN` cannot trigger workflows in a DIFFERENT repo. So when the
tool publishes a release, the tool repo has to poke the site repo itself, using a
token you provide. Without this, a new simpleGals release ships to PyPI but the
demo site never rebuilds against it.

Make the token:

- A fine-grained PAT. Resource owner: `simplegals`. Repository access: only
  `simplegals.github.io`. Permissions: Contents = Read and write (the
  repository-dispatch API needs Contents write; nothing else).
- A GitHub App installation token is the better long-term answer; a fine-grained
  PAT is the honest MVP. Note the expiry and put a reminder somewhere, because a
  silently-expired PAT is a great way to wonder why the site went stale.

Store it in the TOOL repo (`simplegals/simpleGals`), Settings, Secrets and
variables, Actions, as `SITE_DISPATCH_TOKEN`.

Then add a job to `publish.yml` that fires after the publish job:

    notify-site:
      needs: publish
      runs-on: ubuntu-latest
      steps:
        - name: Trigger the demo site rebuild
          run: |
            curl -sf -X POST \
              -H "Authorization: Bearer ${{ secrets.SITE_DISPATCH_TOKEN }}" \
              -H "Accept: application/vnd.github+json" \
              https://api.github.com/repos/simplegals/simplegals.github.io/dispatches \
              -d '{"event_type":"simplegals-release"}'

And the site's `pages.yml` listens for it:

    on:
      repository_dispatch:
        types: [simplegals-release]

(The site half of this belongs to sub-project 2; it is listed here so the two
ends use the SAME `event_type` string. If they drift, nothing errors, the site
just never rebuilds, which is the worst kind of bug.)

Verify: publish a release (or POST the dispatch by hand with the same curl) and
confirm a run starts in the site repo.

## Loose Ends to Sweep After the Move

None of these break the build, but leaving them makes the repo lie about where it
lives.

- `pyproject.toml`: `[project.urls] Repository` still points at
  `https://github.com/timlnx/simpleGals`. Change it to `.../simplegals/simpleGals`.
  (The in-app branding constant `PROJECT_URL` was already set to the org URL back
  in 0.3.1, on purpose, so the generated pages are already correct. It is only the
  package metadata that lags.)
- README badges and any hardcoded `timlnx/simpleGals` links.
- If you have local clones on other machines, `git remote set-url` each one.

## Rollback

If the transfer itself goes sideways (it rarely does), you can transfer the repo
right back to `timlnx`. The PyPI publisher is fully reversible too: re-add the
`timlnx` publisher, remove the `simplegals` one. Because a failed publish uploads
nothing, there is no poisoned PyPI version to clean up. The only thing you cannot
undo is a version you actually published, so the usual rule holds: never reuse a
version number.

## What to Watch Next

Once this is done, sub-project 2 (the site) is unblocked: it can `pip install
simplegals` from PyPI under the new org and rebuild on every release via the
dispatch you just wired. If a release ever ships but the site does not refresh,
check three things in order: the `SITE_DISPATCH_TOKEN` expiry, the `event_type`
strings matching on both ends, and org Actions still being enabled.

Good luck, buddies.

## See Also

- [Demo initiative design](2026-07-09-simplegals-demo-initiative-design.md) (the parent)
- [0.3.1 cover/manifest spec](2026-07-09-simplegals-0.3.1-cover-manifest-design.md) (the `gallery.json` contract the site consumes)
- PyPI trusted publishing: https://docs.pypi.org/trusted-publishers/
- GitHub repo transfer: https://docs.github.com/repositories/creating-and-managing-repositories/transferring-a-repository
