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

from service import TaskInterface


class AddTask(TaskInterface):
    def execute(self, input_data: dict) -> dict:
        a = input_data.get("input1", 0)
        b = input_data.get("input2", 0)
        result = a + b
        return {"result": result}


class ArraySumTask(TaskInterface):
    def execute(self, input_data: dict) -> dict:
        numbers = input_data.get("numbers", [])
        result = sum(numbers)
        return {"result": result}

class SleepTask(TaskInterface):
    def execute(self, input_data: dict) -> dict:
        import time
        duration = input_data.get("duration", 1)
        time.sleep(duration)
        return {"status": "slept for {} seconds".format(duration)}

