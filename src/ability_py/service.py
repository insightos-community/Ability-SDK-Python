# Copyright 2026 InsightOS
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ability_py import logger
from ability_py.interface import AbilityInterface
import sys
import ctypes
import signal
from ability_py.api_server import app, get_free_port
from ability_py.heartbeat import HeartbeatMgr, LifecycleState
from werkzeug.serving import make_server
import json
import logging
import requests


def _set_parent_death_signal():
    """通过 prctl(PR_SET_PDEATHSIG, SIGTERM) 让内核在父进程（框架）退出时
    自动向本进程发送 SIGTERM。这样即使框架被 SIGKILL，子能力进程也不会成为
    孤儿继续向新框架实例发送心跳，从而破坏单例约束。"""
    try:
        PR_SET_PDEATHSIG = 1
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        ret = libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM, 0, 0, 0)
        if ret != 0:
            err = ctypes.get_errno()
            print(f"prctl(PR_SET_PDEATHSIG) failed: errno={err}")
    except Exception as e:
        # 非 Linux 平台或 libc 不可用时静默跳过
        print(f"PR_SET_PDEATHSIG unavailable: {e}")


class AbilityService:
    def __init__(self):
        # 父框架进程退出时自动结束本进程
        _set_parent_death_signal()
        if len(sys.argv) != 3:
            raise ValueError("Usage: python service.py <uuid> <config>")
        self.uuid = sys.argv[1]
        config = json.loads(sys.argv[2])
        self.af_port = config.get("port")
        if self.af_port is None:
            raise ValueError("Port not specified in config")

        # 生成随机不重复的端口
        self.ipc_port = get_free_port()
        print(f"Using IPC port: {self.ipc_port}")
        cr = self.get_cr()
        spec = cr.get("spec")
        meta = cr.get("metadata")
        if spec is None or meta is None:
            raise ValueError("Invalid CR format, missing 'spec' or 'meta'")
        ability_name = spec.get("abilityName")
        version = spec.get("version")
        cr_name = meta.get("name")
        if ability_name is None or version is None or cr_name is None:
            raise ValueError("Invalid CR format, missing required fields")
        # 实例名追加 instance id 前 8 位以区分多个历史/并发实例。
        # 与框架侧 AbilityInstance 表的命名规则保持一致。
        short = self.uuid.split("-")[0]
        instance_name = f"{cr_name}-{short}"

        heartbeat_data = {
            "IPCPort": self.ipc_port,
            "IPCProtocol": "http",
            "abilityName": ability_name,
            "abilityPort": 0,
            "id": self.uuid,
            "instanceName": instance_name,
            "state": str(LifecycleState.Unknown),
            "version": version,
        }
        # 初始化心跳管理器
        self.heartbeat_mgr = HeartbeatMgr(host="localhost", port=self.af_port)
        self.heartbeat_mgr.set_heartbeat(heartbeat_data)
        self.heartbeat_mgr.start()
        print("Heartbeat manager started.")

    def get_cr(self):
        # 获取能力注册信息
        response = requests.get(f"http://localhost:{self.af_port}/api/cr/" + self.uuid)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get CR info, status code: {response.status_code}"
            )
        return response.json()

    def run(self, ability: AbilityInterface):
        # 设置全局ability实例
        app.ability = ability
        app.heartbeat_mgr = self.heartbeat_mgr  # 挂载心跳管理器到app

        # 启动时发送生命周期事件
        ability.on_start()
        # 先绑定 IPC 端口再广播 Standby, 保证 "Standby 心跳" 到达框架时
        # IPC port 已经 listen, 框架随后的 connect 命令不会落到未绑定的端口上。
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        server = make_server("0.0.0.0", self.ipc_port, app)
        app.heartbeat_mgr.update_lifecycle_state(LifecycleState.Standby)
        server.serve_forever()
