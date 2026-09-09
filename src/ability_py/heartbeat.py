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

import os
import signal
import threading
import time

import requests


class LifecycleState:
    Unknown = "Unknown"
    Inactive = "Inactive"
    Init = "Init"
    Standby = "Standby"
    Running = "Running"
    Suspend = "Suspend"
    Terminated = "Terminated"
    Error = "Error"


# 连续收到 HTTP 410 Gone 这么多次就视为 "framework 已经忘了我", 自毁退出。
# 410 的语义由框架定义: instance_id 不在 AbilityInstance 表里 (典型原因:
# 上一代 framework 死掉后 PR_SET_PDEATHSIG 没 reparent 发信号, 留下的
# python 僵尸在对新框架打心跳)。自毁让僵尸进程无声退场。
ORPHAN_GONE_THRESHOLD = 3


class HeartbeatMgr:
    def __init__(self, host: str, port: int, heartbeat_interval: int = 10):
        self.host = host
        self.port = port
        self.heartbeat_interval = heartbeat_interval
        self.running = False
        self.heartbeat_data = None
        self._url = f"http://{host}:{port}/api/ability-heartbeat"
        self._consecutive_gone = 0

    def start(self):
        self.running = True
        t = threading.Thread(target=self._heartbeat_loop, daemon=True)
        t.start()

    def stop(self):
        self.running = False

    def update_lifecycle_state(self, state: LifecycleState):
        """更新状态并立即通知框架（不等定时心跳）"""
        self.heartbeat_data["state"] = str(state)
        self._send()

    def set_heartbeat(self, data: dict):
        self.heartbeat_data = data

    def _heartbeat_loop(self):
        """定时心跳 — 保持存活检测"""
        while self.running:
            self._send()
            time.sleep(self.heartbeat_interval)

    def _send(self):
        try:
            resp = requests.post(self._url, json=self.heartbeat_data, timeout=3)
        except Exception:
            # 框架不可达 (还没起 / 重启中) — 静默重试, 不计入 orphan 判定
            return
        if resp.status_code == 410:
            self._consecutive_gone += 1
            print(
                f"[heartbeat] framework returned 410 Gone "
                f"({self._consecutive_gone}/{ORPHAN_GONE_THRESHOLD}) — "
                f"instance_id={self.heartbeat_data.get('id')}",
                flush=True,
            )
            if self._consecutive_gone >= ORPHAN_GONE_THRESHOLD:
                print(
                    "[heartbeat] orphaned from framework, self-terminating",
                    flush=True,
                )
                self.running = False
                # 让 process 主循环 (flask serve_forever) 收到 SIGTERM 干净退出
                os.kill(os.getpid(), signal.SIGTERM)
            return
        # 非 410 的响应视为 "心跳被接受" — 清零计数器
        self._consecutive_gone = 0
