#!/usr/bin/env bash
# Copyright 2026 InsightOS
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail
uv build
uv venv .output/smoke --python 3.13
uv pip install --python .output/smoke/bin/python dist/*.whl
uv pip check --python .output/smoke/bin/python
.output/smoke/bin/python - <<'PYTHON'
from importlib.metadata import version
from ability_py import AbilityInterface, AbilityService, TaskInterface, TaskManager, get_free_port
assert version("ability-py")
assert callable(AbilityInterface.on_start)
assert 0 < get_free_port() < 65536
print("Installed wheel import and port allocation smoke checks passed")
PYTHON
