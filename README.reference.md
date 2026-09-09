> Historical technical reference / 历史技术参考。For current build and usage instructions, see [English](README.md) / [中文](README.zh-CN.md). Version-specific examples below are not a current release manifest.

# Ability Python SDK

## Warning

- 暂时未处理 onSubabilityError
- 暂时 日志没有 写入 框架里面 logs/
- 暂不支持 zenoh 通信协议

## Run Example （极简 demo）

- 需要启动 Ability Framework
- 从 AbilityFramework 获取实际实例 uuid 和 config

```bash
uv run examples/demo/main.py {uuid} '{config}'
```

## Formatting Code

```bash
uv run ruff format
```

## Build

```bash
uv build --wheel
```
会在 dist/ 目录下生成 wheel 包
