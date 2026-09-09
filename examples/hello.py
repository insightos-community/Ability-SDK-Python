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

import ability_py
from flask import Flask, request
import threading
import requests

app = Flask(__name__)


@app.post("/ping")
def ping():
    return "PONG", 200


@app.post("/shutdown")
def shutdown():
    # 关闭 Flask 服务
    func = request.environ.get("werkzeug.server.shutdown")
    if func:
        func()
        return "Server shutting down...", 200
    return "Shutdown not available", 200


class ImplAbility(ability_py.AbilityInterface):
    def __init__(self):
        self.ability_port = 0
        self.t = None

    def on_start(self):
        print("Ability started")

    def on_connect(self):
        print("Ability connected")
        # 如果已有服务在运行，先关闭
        if self.ability_port:
            try:
                requests.post(
                    f"http://localhost:{self.ability_port}/shutdown", timeout=1
                )
            except:
                pass

        self.ability_port = ability_py.get_free_port()
        self.t = threading.Thread(
            target=app.run,
            kwargs={"host": "localhost", "port": self.ability_port},
            daemon=True,
        )
        self.t.start()

    def on_disconnect(self):
        print("Ability disconnected")
        # 优雅关闭 Flask 服务
        if self.ability_port != 0:
            try:
                requests.post(
                    f"http://localhost:{self.ability_port}/shutdown", timeout=1
                )
            except:
                pass
            self.ability_port = 0

    def on_terminate(self):
        print("Ability terminated")

    def get_ability_port(self) -> int:
        return self.ability_port


ability = ImplAbility()
service = ability_py.AbilityService()
service.run(ability)
