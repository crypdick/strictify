# Automatic releases for uv projects

Offer only for uv-managed distributions intended for publication from GitHub.
Skip applications, private packages, and manual-approval release policies.
Publication belongs in CI, not a prek hook.

## Contract

Pull requests run the normal quality gate without publishing. On release-branch
pushes, usually `main`:

1. Pass the same full gate used locally. Serialize releases with
   `cancel-in-progress: false` and check out the branch with parent history.
2. Reject stale runs and select the version using the rules below.
3. Run `uv version --no-sync VERSION` to synchronize `pyproject.toml` and `uv.lock`;
   do not edit them separately. Run `uv sync --locked --all-groups` and the full gate.
4. Commit both as `Release VERSION` with `Source-Commit: SHA` in the body.
   Push with the workflow token to avoid triggering another workflow.
5. Build the release commit with `uv build`. Publish through a protected GitHub
   environment and PyPI trusted publishing; create `vVERSION` and a GitHub Release
   containing both distributions.

Manual dispatch must recover the same release. PyPI upload may use `skip-existing`;
existing tags must already point to the intended commit. Never move a version tag.

## Version preparation

Use a small tested script. Report `state` (`new`, `retry`, `stale`), `version`,
and release commit SHA through `GITHUB_OUTPUT`.

Query PyPI JSON metadata. Accept stable `major.minor.patch` unless the repo defines
prerelease semantics. Preserve a project version above every published version;
otherwise bump the latest published patch.

A retry matches an existing `Release VERSION` commit whose parent and
`Source-Commit` both identify the triggering SHA. Any other branch-head mismatch
is stale and stops successfully.

## Required repository-specific choices

Establish package name, branch, Python setup, quality/build commands, PyPI
environment, and any coupled docs deployment. Follow existing action pinning.
Grant `contents: write` only to version/tag jobs and `id-token: write` only to publishing.

Strictify's `.github/workflows/checks.yml` and `tools/prepare_plugin_release.py`
demonstrate serialization, retries, and synchronized versions. Adapt the transaction
pattern; Python packages need different version parsing than plugin JSON manifests.
