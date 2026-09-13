# Ability Python SDK

[English](README.md) | [简体中文](README.zh-CN.md)

🧩 The Python integration layer for abilities hosted by AbilityFramework: service interfaces, tasks, lifecycle communication, heartbeats, and logging. The distribution name is `ability-py`; the import name is `ability_py`.

## Structure

- `src/ability_py/` — SDK implementation.
- `examples/` — sample ability entry points.
- `pyproject.toml` — package metadata and build configuration.

## 🛠 Build and install

Requires Python **3.8+** and uv. Use Python **3.13** when preparing the current Semantic Robot Bundle.

```bash
uv build --wheel
uv venv --python 3.13
uv pip install dist/ability_py-*.whl
.venv/bin/python -c "import ability_py"
```

The output is `dist/ability_py-*.whl`. Keep the version aligned with ability-scaffold, the ability packages, and the bundle manifest.

## Use the SDK

Start with [examples](examples/) or generate an Ability project with ability-scaffold. Implement the generated interfaces and let AbilityFramework launch the entry point with its instance configuration. Installing this SDK does not install or start the C++ host.

Quick-start copies the built Wheel into ability-runtime and the selected base bundle's Wheel cache before assembling a Robot Bundle.

## Troubleshooting

If an Ability cannot import the SDK, inspect the interpreter/environment used by the host, not only your shell's Python. LFS pointer text is not an installable Wheel. Connection and lifecycle failures also require a compatible running AbilityFramework.

[Previous usage notes](README.reference.md)

[CI and Tag releases](docs/ci-release.md)

## License

Copyright 2026 InsightOS. First-party code: [Apache-2.0](LICENSE). See [NOTICE](NOTICE) and [license scope](LICENSE_SCOPE.md) for third-party components and assets.

## Reproducible platform builds

See [glibc, musl and macOS build instructions](README.build.md) for pinned source revisions, exact scripts, tool requirements, local commands, CI reproduction and platform support boundaries.
