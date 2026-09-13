# Ability-SDK-Python: reproducible platform builds

## Versions, tools and build layout

The glibc installer pins component tag **v0.4.0-insightos.2026.2** at `3a90b6d94ea6babb890ffcd285ba55e5fef6fc8c`.
This guide pins the current build-script snapshot at `2a15050fee885d6980528adc6f91439cbf4bd7a3`.
To reconstruct another published release, read its `release.json` and select
both `source_commit` and `build_recipe_commit`; a source tag alone may predate
the CI scripts. This recipe reproduces the build steps, not historical archive bytes.

Prerequisites: uv 0.12.12, Git and Python 3; component scripts select Python 3.13. Use a fresh virtual environment for each platform.

The release scripts expect **two sibling checkouts**, `automation/` for build
scripts and `source/` for the component. Run these commands from a fresh working
directory (the scripts themselves are not standalone copies):

```bash
REPRO_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/Ability-SDK-Python-repro.XXXXXXXX")"
git clone --no-checkout https://github.com/insightos-community/Ability-SDK-Python.git "$REPRO_ROOT/automation"
GIT_LFS_SKIP_SMUDGE=1 git -C "$REPRO_ROOT/automation" checkout --detach 2a15050fee885d6980528adc6f91439cbf4bd7a3
git clone --no-checkout https://github.com/insightos-community/Ability-SDK-Python.git "$REPRO_ROOT/source"
GIT_LFS_SKIP_SMUDGE=1 git -C "$REPRO_ROOT/source" checkout --detach v0.4.0-insightos.2026.2
cd "$REPRO_ROOT/source"
test "$(git rev-parse HEAD)" = 3a90b6d94ea6babb890ffcd285ba55e5fef6fc8c
export TARGET_TAG=v0.4.0-insightos.2026.2
export COMPONENT=ability-py
export GITHUB_SHA=2a15050fee885d6980528adc6f91439cbf4bd7a3
```

## Linux glibc / standard component Release

The executable build entry is [`.github/scripts/build.sh`](.github/scripts/build.sh);
archive validation is [`.github/scripts/package.py`](.github/scripts/package.py).
From `source/` in the layout above:

```bash
bash ../automation/.github/scripts/build.sh
python3 ../automation/.github/scripts/package.py ability-py
(cd .output/release && sha256sum -c SHA256SUMS)
```

Artifacts: `source/.output/release/` (archives/wheels, `release.json`, checksum
inventory and license notices). `release.json` records source and recipe revisions.
The local commands do not publish or overwrite a GitHub Release.

## Linux musl

This component produces pure Python wheels, scripts, static Web/docs or assets
that are reused by the musl installer. Reproduce the component on the standard
build host above; a second musl compilation of those same files is unnecessary.
Native transitive dependencies must still be obtained from the musl lock.

For the complete musl build and offline checks, use the [quick-start musl commands](https://github.com/insightos-community/quick-start/blob/main/README.build.md#linux-musl-x86_64).

## macOS / macosx

The component wheel is `py3-none-any` and is reused in the macOS installer.
On an Apple Silicon build host with uv 0.12.12, build the pure package from a
fresh checkout at the source revision above:

```bash
uv build
uv venv --managed-python --python 3.13.15 .venv-macos
uv pip install --python .venv-macos/bin/python dist/*.whl
uv pip check --python .venv-macos/bin/python
```

The complete macOS installer targets Apple Silicon/macOS 15.5+; see the [locked assembly instructions](https://github.com/insightos-community/quick-start/blob/main/README.build.md#macos-apple-silicon).

## GitHub workflow reproduction

The repository’s [CI workflow](.github/workflows/ci.yml) implements the two-checkout
layout. To build a source tag without publishing, create a reproduction branch at the
pinned automation commit. GitHub dispatch expects a branch/tag ref; both tag refs
and default-branch dispatches can enter this workflow’s publishing job. The following
commands require repository write access and use a non-default branch:

```bash
gh auth setup-git
REPRO_BRANCH=reproduce/platform-builds
git -C "$REPRO_ROOT/automation" push origin 2a15050fee885d6980528adc6f91439cbf4bd7a3:refs/heads/$REPRO_BRANCH
gh workflow run ci.yml --repo insightos-community/Ability-SDK-Python --ref "$REPRO_BRANCH" -f tag=v0.4.0-insightos.2026.2
gh run list --repo insightos-community/Ability-SDK-Python --workflow ci.yml --limit 5
# Set REPRO_RUN_ID to the selected run ID.
gh run watch "$REPRO_RUN_ID" --repo insightos-community/Ability-SDK-Python --exit-status
gh run download "$REPRO_RUN_ID" --repo insightos-community/Ability-SDK-Python --name release-assets --dir downloaded-release
```

## Reproduction evidence

Build in a fresh checkout and a separate output directory for each ABI. Preserve
source commits, compiler/tool versions, dependency locks, package inventories and
test logs. Fixed source revisions and a container digest reproduce the recipe;
unlocked OS packages, runner images, timestamps and build tools can still change
archive bytes. Compare a downloaded release against its published `SHA256SUMS`;
do not expect a local rebuild to have the same digest.

See the [complete installer and repository index](https://github.com/insightos-community/quick-start/blob/main/README.build.md) for assembly order,
platform locks and end-to-end validation. Local build commands do not publish a
Release. Publishing requires repository write access and a new version tag;
existing release tags/assets should not be replaced.
