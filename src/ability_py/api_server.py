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

from flask import Flask, current_app
import socket
from ability_py.heartbeat import LifecycleState

app = Flask(__name__)
ability = None


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.post("/api/lifecycle/start")
def start_lifecycle():
    app.ability.on_start()
    app.heartbeat_mgr.update_lifecycle_state(LifecycleState.Standby)
    return "OK", 200


@app.post("/api/lifecycle/connect")
def connect_lifecycle():
    app.ability.on_connect()
    ability_port = app.ability.get_ability_port()
    if ability_port is None or ability_port <= 0:
        print("Ability port is not set or invalid.")
    else:
        # 更新心跳中的ability端口
        app.heartbeat_mgr.heartbeat_data["abilityPort"] = ability_port
    app.heartbeat_mgr.update_lifecycle_state(LifecycleState.Running)
    return "OK", 200


@app.post("/api/lifecycle/disconnect")
def disconnect_lifecycle():
    app.ability.on_disconnect()
    app.heartbeat_mgr.heartbeat_data["abilityPort"] = 0  # 断开连接时重置端口为0
    app.heartbeat_mgr.update_lifecycle_state(LifecycleState.Suspend)
    return "OK", 200


@app.post("/api/lifecycle/terminate")
def terminate_lifecycle():
    app.ability.on_terminate()
    app.heartbeat_mgr.update_lifecycle_state(LifecycleState.Terminated)
    return "OK", 200


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # 0 表示让 OS 分配
        return s.getsockname()[1]
