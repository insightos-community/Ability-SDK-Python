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

from typing import Optional


class AbilityInterface:
    """
    能力接口基类，定义了能力生命周期的回调方法
    
    所有自定义能力必须继承此接口并实现所有抽象方法
    """
    
    def on_start(self) -> None:
        """
        能力启动时的回调
        
        在能力服务启动时被调用，用于初始化资源
        """
        raise NotImplementedError

    def on_connect(self) -> None:
        """
        能力连接时的回调
        
        当外部系统与能力建立连接时被调用
        """
        raise NotImplementedError

    def on_disconnect(self) -> None:
        """
        能力断开连接时的回调
        
        当外部系统与能力断开连接时被调用，用于清理连接相关资源
        """
        raise NotImplementedError

    def on_terminate(self) -> None:
        """
        能力终止时的回调
        
        在能力服务终止前被调用，用于清理所有资源
        """
        raise NotImplementedError

    def get_ability_port(self) -> Optional[int]:
        """
        获取能力服务的端口号
        
        Returns:
            能力服务监听的端口号，如果未设置则返回 None
        """
        raise NotImplementedError
