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

from service import ImplAbility, task_manager
import ability_py
from task import AddTask, ArraySumTask, SleepTask


# 注册task
tasks = {
    0: AddTask(),
    1: ArraySumTask(),
    3: SleepTask(),
}


task_manager.register_tasks(tasks)

if __name__ == "__main__":
    # 创建能力实例
    ability = ImplAbility()
    # 创建能力服务
    service = ability_py.AbilityService()
    # 运行能力服务
    service.run(ability)
