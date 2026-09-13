# Ability Python SDK

[English](README.md) | [简体中文](README.zh-CN.md)

🧩 为 AbilityFramework 托管的 Python 能力提供服务接口、任务、生命周期通信、心跳与日志。分发包名为 `ability-py`，导入名为 `ability_py`。

## 工程结构

- `src/ability_py/`：SDK 实现。
- `examples/`：能力入口示例。
- `pyproject.toml`：包元数据与构建配置。

## 🛠 构建与安装

需要 Python **3.8+** 和 uv；准备当前 Semantic Robot Bundle 时使用 Python **3.13**。

```bash
uv build --wheel
uv venv --python 3.13
uv pip install dist/ability_py-*.whl
.venv/bin/python -c "import ability_py"
```

产物为 `dist/ability_py-*.whl`，版本应与 ability-scaffold、能力包和 Bundle 清单保持一致。

## 使用方式

从[示例](examples/)开始，或使用 ability-scaffold 生成工程。实现生成的接口后，由 AbilityFramework 带实例配置启动入口。安装 SDK 不会安装或启动 C++ 宿主。

quick-start 在组装 Robot Bundle 前，将构建的 Wheel 复制到 ability-runtime 根目录与选定 base bundle 的 Wheel 缓存。

## 常见问题

Ability 无法导入 SDK 时，应检查宿主实际使用的解释器 / 环境，而不仅是当前 shell 的 Python。LFS 指针文本不是可安装的 Wheel；连接和生命周期问题还需要检查运行中的 AbilityFramework 是否兼容。

[原始使用笔记](README.reference.md)

[CI 与 Tag 制品发布](docs/ci-release.md)

## 许可证

Copyright 2026 InsightOS。自有代码采用 [Apache-2.0](LICENSE)；第三方组件与资产请查看 [NOTICE](NOTICE) 和[许可范围](LICENSE_SCOPE.md)。

## 三个平台的构建复现

参见 [glibc、musl 与 macOS 构建说明](README.build.md)：包含已锁定的源码版本、实际脚本入口、工具要求、本地与 CI 指令、产物位置和平台验证范围。
