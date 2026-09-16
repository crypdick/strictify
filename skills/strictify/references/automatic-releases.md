# Automatic releases for uv projects

Offer this only for a uv-managed Python distribution the user intends to publish
from GitHub. Applications, private packages, and repos with manual release approval
stay unchanged. Release automation is not a prek hook: prek verifies the source;
the workflow owns version mutation and publication.

## Contract

On every pull request, run the normal quality gate without publishing. On every
push to the release branch, usually `main`:

1. Run the same full quality gate used locally.
2. Serialize release jobs for that branch with `cancel-in-progress: false`.
3. Check out the current release branch with enough history to inspect its parent.
4. Stop successfully when a newer source commit has overtaken this run.
5. Preserve a valid, unpublished manual version increase. Otherwise choose the
   next patch after the latest published stable version.
6. Run `uv version --no-sync VERSION`. Do not edit `pyproject.toml` or `uv.lock`
   separately; uv owns their synchronization.
7. Run `uv sync --locked --all-groups` and the full quality gate against the
   release version.
8. Commit `pyproject.toml` and `uv.lock` as `Release VERSION`, with a
   `Source-Commit: SHA` body line. Push with the workflow token. GitHub does not
   start another workflow from that token's push.
9. Build from the release commit with `uv build`, publish through a protected
   GitHub environment and PyPI trusted publishing, then create `vVERSION` and a
   GitHub Release containing both distributions.

Manual workflow dispatch must recover the same source release instead of allocating
another version. PyPI upload may use `skip-existing`, but tag recovery must verify
that an existing tag already points to the intended release commit. Never move an
existing version tag.

## Version preparation

Keep version-selection and retry logic in a small tested repository script rather
than an inline workflow program. It should report `state` (`new`, `retry`, or
`stale`), `version`, and release commit SHA through `GITHUB_OUTPUT`.

Use the package's PyPI JSON metadata as publication state. Accept only stable
`major.minor.patch` versions unless the repository explicitly defines prerelease
semantics. If current project version is greater than every published version,
preserve it; otherwise increment latest published patch. A retry is the existing
`Release VERSION` commit whose parent and `Source-Commit` line match triggering
source SHA. Any other branch-head mismatch is stale.

## Required repository-specific choices

Before writing workflow, confirm package name, release branch, Python setup,
quality command, build command, PyPI environment name, and whether docs deploy in
same workflow. Use existing action pinning convention. Grant `contents: write` only
to version/tag jobs and `id-token: write` only to trusted-publishing job.

Strictify itself demonstrates concurrency, stale-run rejection, synchronized
version files, and retry metadata in `.github/workflows/checks.yml` and
`tools/prepare_plugin_release.py`. Its version lives in plugin JSON manifests, so
reuse transaction pattern—not plugin-specific version parsing—in Python projects.
