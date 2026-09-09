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

import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional
from .interface import TaskInterface

TIMEFORMAT = "%Y-%m-%d %H:%M:%S.%f"

def get_current_time_str() -> str:
    return datetime.now().strftime(TIMEFORMAT)[:-3]

class TaskStatus:
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskManager:
    """任务管理器，负责任务的注册、创建、执行和状态管理"""

    def __init__(self):
        self.tasks: Dict[str, dict] = {}  # 任务信息字典，key为task_id
        self.task_registry: Dict[int, TaskInterface] = {}  # 任务类型注册表，key为index
        self.task_threads: Dict[str, threading.Thread] = {}  # 任务线程字典
        self.task_cancellation: Dict[str, threading.Event] = {}  # 任务取消标志
        self.lock = threading.Lock()

    def register_tasks(self, tasks: Dict[int, TaskInterface]):
        """
        批量注册任务类型

        Args:
            tasks: 任务字典，key为任务索引(int)，value为任务处理器(TaskInterface)
        """
        with self.lock:
            self.task_registry.update(tasks)

    def start_task(self, index: int, input_data: dict) -> dict:
        """
        创建并启动新任务

        Args:
            index: 任务索引，对应注册时的key
            input_data: 任务输入数据

        Returns:
            包含task_id、index和status的字典

        Raises:
            ValueError: 当任务索引未注册时
        """
        if index not in self.task_registry:
            raise ValueError(f"Unknown task index: {index}")

        task_id = f"task-{uuid.uuid4().hex[:8]}"
        now = get_current_time_str()

        # 创建取消事件
        cancel_event = threading.Event()

        task_info = {
            "task_id": task_id,
            "index": index,
            "status": TaskStatus.RUNNING,
            "created_at": now,
            "updated_at": now,
        }

        with self.lock:
            self.tasks[task_id] = task_info
            self.task_cancellation[task_id] = cancel_event

        # 在后台线程中执行任务
        thread = threading.Thread(
            target=self._execute_task, args=(task_id, index, input_data, cancel_event)
        )
        thread.daemon = True
        thread.start()

        with self.lock:
            self.task_threads[task_id] = thread

        return {"task_id": task_id}

    def _execute_task(
        self, task_id: str, index: int, input_data: dict, cancel_event: threading.Event
    ):
        """
        在后台执行任务

        Args:
            task_id: 任务ID
            index: 任务索引
            input_data: 任务输入数据
            cancel_event: 取消事件标志
        """
        try:
            # 检查任务是否已被取消
            if cancel_event.is_set():
                with self.lock:
                    self.tasks[task_id].update(
                        {
                            "status": TaskStatus.CANCELLED,
                            "updated_at": get_current_time_str(),
                        }
                    )
                return

            task_handler = self.task_registry[index]
            result = task_handler.execute(input_data)
            # 再次检查是否被取消
            if cancel_event.is_set():
                with self.lock:
                    self.tasks[task_id].update(
                        {
                            "status": TaskStatus.CANCELLED,
                            "updated_at": get_current_time_str(),
                        }
                    )
                return

            with self.lock:
                self.tasks[task_id].update(
                    {
                        "status": TaskStatus.COMPLETED,
                        "updated_at": get_current_time_str(),
                        "payload": result,
                    }
                )
        except Exception as e:
            with self.lock:
                self.tasks[task_id].update(
                    {
                        "status": TaskStatus.FAILED,
                        "updated_at": get_current_time_str(),
                        "message": str(e),
                    }
                )
        finally:
            # 清理线程和取消事件
            with self.lock:
                self.task_threads.pop(task_id, None)
                self.task_cancellation.pop(task_id, None)

    def get_task_info(self, task_id: str) -> Optional[dict]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，如果任务不存在则返回None
        """
        with self.lock:
            return self.tasks.get(task_id)

    def list_tasks(self) -> List[dict]:
        """
        列出所有任务

        Returns:
            所有任务信息的列表
        """
        with self.lock:
            return list(self.tasks.values())

    def list_task_registry(self) -> List[dict]:
        """
        列出已注册的任务类型

        Returns:
            已注册任务类型的信息列表
        """
        with self.lock:
            return [
                {"index": index, "task_name": type(handler).__name__}
                for index, handler in self.task_registry.items()
            ]

    def cancel_task(self, task_id: str) -> bool:
        """
        取消正在运行的任务

        Args:
            task_id: 任务ID

        Returns:
            True表示成功取消或标记取消，False表示任务不存在
        """
        with self.lock:
            task_info = self.tasks.get(task_id)
            if not task_info:
                return False

            # 如果任务已经完成、失败或已取消，不需要再取消
            if task_info["status"] in [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ]:
                return True

            # 设置取消标志
            cancel_event = self.task_cancellation.get(task_id)
            if cancel_event:
                cancel_event.set()

            # 更新任务状态
            now = get_current_time_str()
            task_info.update(
                {
                    "status": TaskStatus.CANCELLED,
                    "updated_at": now,
                }
            )

            return True


# 全局任务管理器实例
task_manager = TaskManager()
