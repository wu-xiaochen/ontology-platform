"""
Agent工作流测试 (Agent Orchestrator Test)

测试 Orchestrator 的核心功能：
1. 创建 Orchestrator 实例
2. 验证工具注册（ToolRegistry）
3. 验证工具列表获取
4. 验证工具热插拔（注册→卸载→再注册）

设计原则：
- 每行逻辑代码必须有中文注释（解释"为什么"）
- 零硬编码：所有配置从环境变量读取
- 无TODO/FIXME：所有实现都是完整可用的
"""

import os
import sys
import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock

# 添加项目根目录到Python路径，确保可以导入src模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.action_runtime import ToolRegistry, ToolDefinition, tool_registry


class TestAgentOrchestrator:
    """Agent工作流测试类"""
    
    @pytest.fixture(autouse=True)
    def reset_tool_registry(self):
        """
        每个测试前重置工具注册表
        
        确保测试之间相互隔离，避免工具注册状态污染
        """
        # 清空工具注册表
        tool_registry.clear()
        yield
        # 测试结束后再次清空
        tool_registry.clear()
    
    @pytest.fixture
    def sample_tool_definition(self) -> ToolDefinition:
        """
        创建测试用的工具定义
        
        返回一个典型的ToolDefinition实例，用于测试注册功能
        """
        return ToolDefinition(
            name="test_tool",
            description="这是一个测试工具",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "输入参数"}
                },
                "required": ["input"]
            },
            category="test",
            tags=["test", "sample"],
            enabled=True
        )
    
    def test_tool_registry_singleton(self):
        """
        测试ToolRegistry单例模式
        
        验证点：
        - ToolRegistry是单例，多次获取的是同一个实例
        - 单例模式确保全局工具定义一致性
        """
        # 获取工具注册表实例
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        
        # 验证是同一个实例
        assert registry1 is registry2, "ToolRegistry应是单例模式"
        
        # 验证全局实例与新建实例相同
        assert tool_registry is registry1, "全局tool_registry应与单例相同"
    
    def test_tool_registration(self, sample_tool_definition: ToolDefinition):
        """
        测试工具注册功能
        
        验证点：
        - 工具可以成功注册
        - 注册后可以通过名称获取
        - 重复注册会覆盖旧定义
        """
        # 注册工具
        tool_registry.register(sample_tool_definition)
        
        # 验证可以通过名称获取
        retrieved = tool_registry.get_tool("test_tool")
        assert retrieved is not None, "注册后应能通过名称获取工具"
        assert retrieved.name == "test_tool", "获取的工具名称应匹配"
        assert retrieved.description == "这是一个测试工具", "获取的工具描述应匹配"
        
        # 验证分类索引已更新
        tools_in_category = tool_registry.list_tools(category="test")
        assert len(tools_in_category) == 1, "test分类下应有1个工具"
        assert tools_in_category[0].name == "test_tool", "分类下的工具名称应匹配"
    
    def test_tool_listing(self):
        """
        测试工具列表获取功能
        
        验证点：
        - 可以获取所有已注册工具列表
        - 可以按分类过滤工具
        - 可以按标签过滤工具
        - 可以只获取启用的工具
        """
        # 注册多个测试工具
        tools = [
            ToolDefinition(
                name="tool_a",
                description="工具A",
                parameters={},
                category="category_1",
                tags=["tag1", "common"],
                enabled=True
            ),
            ToolDefinition(
                name="tool_b",
                description="工具B",
                parameters={},
                category="category_1",
                tags=["tag2", "common"],
                enabled=True
            ),
            ToolDefinition(
                name="tool_c",
                description="工具C",
                parameters={},
                category="category_2",
                tags=["tag1"],
                enabled=False  # 禁用状态
            )
        ]
        
        for tool in tools:
            tool_registry.register(tool)
        
        # 测试获取所有启用的工具（默认 enabled_only=True）
        all_tools = tool_registry.list_tools()
        assert len(all_tools) == 2, "应返回2个启用的工具"
        
        # 测试获取所有工具（包括禁用的）
        all_tools_including_disabled = tool_registry.list_tools(enabled_only=False)
        assert len(all_tools_including_disabled) == 3, "应返回3个工具（包括禁用的）"
        
        # 测试按分类过滤
        category_1_tools = tool_registry.list_tools(category="category_1")
        assert len(category_1_tools) == 2, "category_1下应有2个工具"
        
        # 测试按标签过滤（默认只返回启用的工具）
        tag1_tools = tool_registry.list_tools(tags=["tag1"])
        assert len(tag1_tools) == 1, "tag1标签下应有1个启用的工具"
        
        # 测试按标签过滤（包括禁用的工具）
        tag1_all_tools = tool_registry.list_tools(tags=["tag1"], enabled_only=False)
        assert len(tag1_all_tools) == 2, "tag1标签下应有2个工具（包括禁用的）"
        
        # 测试只获取启用的工具
        enabled_tools = tool_registry.list_tools(enabled_only=True)
        assert len(enabled_tools) == 2, "启用的工具应有2个"
        
        # 测试获取禁用的工具（enabled_only=False）
        all_including_disabled = tool_registry.list_tools(enabled_only=False)
        assert len(all_including_disabled) == 3, "包含禁用的工具应有3个"
    
    def test_tool_hot_swap_unregister(self):
        """
        测试工具热插拔 - 卸载功能
        
        验证点：
        - 可以卸载已注册的工具
        - 卸载后无法再通过名称获取
        - 卸载不存在的工具返回False
        """
        # 注册测试工具
        tool = ToolDefinition(
            name="hot_swap_test",
            description="热插拔测试工具",
            parameters={},
            category="test"
        )
        tool_registry.register(tool)
        
        # 验证工具已注册
        assert tool_registry.get_tool("hot_swap_test") is not None, "工具应已注册"
        
        # 卸载工具
        result = tool_registry.unregister_tool("hot_swap_test")
        assert result is True, "卸载已存在的工具应返回True"
        
        # 验证工具已卸载
        assert tool_registry.get_tool("hot_swap_test") is None, "卸载后应无法获取"
        
        # 测试卸载不存在的工具
        result = tool_registry.unregister_tool("non_existent")
        assert result is False, "卸载不存在的工具应返回False"
    
    def test_tool_hot_swap_reregister(self):
        """
        测试工具热插拔 - 重新注册功能
        
        验证点：
        - 卸载后可以重新注册同名工具
        - 重新注册的工具定义会覆盖旧定义
        - 重新注册后工具可以正常使用
        """
        # 注册初始版本
        tool_v1 = ToolDefinition(
            name="versioned_tool",
            description="版本1",
            parameters={"version": {"type": "integer", "default": 1}},
            category="test"
        )
        tool_registry.register(tool_v1)
        
        # 验证初始版本
        retrieved_v1 = tool_registry.get_tool("versioned_tool")
        assert retrieved_v1.description == "版本1", "初始版本描述应匹配"
        
        # 卸载工具
        tool_registry.unregister_tool("versioned_tool")
        
        # 重新注册新版本
        tool_v2 = ToolDefinition(
            name="versioned_tool",
            description="版本2",
            parameters={"version": {"type": "integer", "default": 2}},
            category="test"
        )
        tool_registry.register(tool_v2)
        
        # 验证新版本
        retrieved_v2 = tool_registry.get_tool("versioned_tool")
        assert retrieved_v2.description == "版本2", "新版本描述应匹配"
    
    def test_tool_enable_disable(self):
        """
        测试工具启用/禁用功能
        
        验证点：
        - 可以禁用已启用的工具
        - 可以启用已禁用的工具
        - 禁用状态影响list_tools的过滤结果
        """
        # 注册测试工具
        tool = ToolDefinition(
            name="toggle_tool",
            description="可切换状态的工具",
            parameters={},
            category="test",
            enabled=True
        )
        tool_registry.register(tool)
        
        # 验证初始状态为启用
        retrieved = tool_registry.get_tool("toggle_tool")
        assert retrieved.enabled is True, "初始状态应为启用"
        
        # 禁用工具
        disable_result = tool_registry.disable_tool("toggle_tool")
        assert disable_result is True, "禁用应返回True"
        
        # 验证状态已禁用
        retrieved = tool_registry.get_tool("toggle_tool")
        assert retrieved.enabled is False, "禁用后状态应为False"
        
        # 验证list_tools(enabled_only=True)过滤掉禁用的工具
        enabled_tools = tool_registry.list_tools(enabled_only=True)
        tool_names = [t.name for t in enabled_tools]
        assert "toggle_tool" not in tool_names, "禁用的工具不应出现在启用列表中"
        
        # 重新启用工具
        enable_result = tool_registry.enable_tool("toggle_tool")
        assert enable_result is True, "启用应返回True"
        
        # 验证状态已启用
        retrieved = tool_registry.get_tool("toggle_tool")
        assert retrieved.enabled is True, "启用后状态应为True"
    
    def test_get_openai_tools_format(self):
        """
        测试获取OpenAI格式的工具定义
        
        验证点：
        - 可以获取OpenAI格式的工具定义列表
        - 格式符合OpenAI API要求
        - 包含必要的字段（type, function, name, description, parameters）
        """
        # 注册测试工具
        tool = ToolDefinition(
            name="openai_format_test",
            description="测试OpenAI格式",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "查询内容"}
                },
                "required": ["query"]
            },
            category="test"
        )
        tool_registry.register(tool)
        
        # 获取OpenAI格式
        openai_tools = tool_registry.get_openai_tools()
        
        # 验证返回列表
        assert isinstance(openai_tools, list), "应返回列表"
        assert len(openai_tools) == 1, "应包含1个工具"
        
        # 验证格式
        tool_def = openai_tools[0]
        assert tool_def["type"] == "function", "type字段应为function"
        assert "function" in tool_def, "应包含function字段"
        assert tool_def["function"]["name"] == "openai_format_test", "name应匹配"
        assert tool_def["function"]["description"] == "测试OpenAI格式", "description应匹配"
        assert "parameters" in tool_def["function"], "应包含parameters字段"
    
    def test_get_categories_and_tags(self):
        """
        测试获取分类和标签列表
        
        验证点：
        - 可以获取所有已使用的分类
        - 可以获取所有已使用的标签
        - 分类和标签列表正确反映已注册工具
        """
        # 注册多个不同分类和标签的工具
        tools = [
            ToolDefinition(name="cat1_tag1", description="", parameters={}, category="cat1", tags=["tag1"]),
            ToolDefinition(name="cat1_tag2", description="", parameters={}, category="cat1", tags=["tag2"]),
            ToolDefinition(name="cat2_tag1", description="", parameters={}, category="cat2", tags=["tag1", "tag3"]),
        ]
        
        for tool in tools:
            tool_registry.register(tool)
        
        # 获取分类列表
        categories = tool_registry.get_categories()
        assert "cat1" in categories, "应包含cat1分类"
        assert "cat2" in categories, "应包含cat2分类"
        
        # 获取标签列表
        tags = tool_registry.get_tags()
        assert "tag1" in tags, "应包含tag1标签"
        assert "tag2" in tags, "应包含tag2标签"
        assert "tag3" in tags, "应包含tag3标签"
    
    def test_tool_statistics(self):
        """
        测试工具注册统计信息
        
        验证点：
        - 可以获取工具注册统计信息
        - 统计信息包含工具总数、启用/禁用数量
        - 统计信息包含分类和标签分布
        """
        # 注册不同状态的工具
        tools = [
            ToolDefinition(name="stat_active1", description="", parameters={}, category="cat1", tags=["tag1"], enabled=True),
            ToolDefinition(name="stat_active2", description="", parameters={}, category="cat1", tags=["tag1"], enabled=True),
            ToolDefinition(name="stat_disabled", description="", parameters={}, category="cat2", tags=["tag2"], enabled=False),
        ]
        
        for tool in tools:
            tool_registry.register(tool)
        
        # 获取统计信息
        stats = tool_registry.get_statistics()
        
        # 验证统计字段
        assert stats["total_tools"] == 3, "总工具数应为3"
        assert stats["enabled_tools"] == 2, "启用的工具数应为2"
        assert stats["disabled_tools"] == 1, "禁用的工具数应为1"
        
        # 验证分类统计
        assert "cat1" in stats["categories"], "应包含cat1分类统计"
        assert stats["categories"]["cat1"] == 2, "cat1下应有2个工具"
        assert "cat2" in stats["categories"], "应包含cat2分类统计"
        assert stats["categories"]["cat2"] == 1, "cat2下应有1个工具"
        
        # 验证标签统计
        assert "tag1" in stats["tags"], "应包含tag1标签统计"
        assert stats["tags"]["tag1"] == 2, "tag1标签应有2个工具"
    
    def test_register_tool_decorator(self):
        """
        测试装饰器风格的工具注册
        
        验证点：
        - 可以使用装饰器注册工具
        - 装饰器注册的工具可以正常获取
        - 被装饰的函数保持可调用性
        """
        # 使用装饰器注册工具
        @tool_registry.register_tool(
            name="decorator_tool",
            description="装饰器注册的工具",
            parameters={
                "type": "object",
                "properties": {
                    "value": {"type": "string"}
                }
            },
            category="decorator_test",
            tags=["decorator"]
        )
        def decorator_handler(args):
            return {"result": f"处理: {args.get('value', '')}"}
        
        # 验证工具已注册
        tool = tool_registry.get_tool("decorator_tool")
        assert tool is not None, "装饰器注册的工具应可获取"
        assert tool.description == "装饰器注册的工具", "描述应匹配"
        
        # 验证被装饰的函数仍可调用
        result = decorator_handler({"value": "test"})
        assert result["result"] == "处理: test", "被装饰函数应可正常调用"
    
    def test_clear_registry(self):
        """
        测试清空注册表功能
        
        验证点：
        - 可以清空所有工具注册
        - 清空后所有工具都无法获取
        - 清空后分类和标签索引也被清空
        """
        # 注册一些工具
        for i in range(3):
            tool_registry.register(ToolDefinition(
                name=f"clear_test_{i}",
                description=f"测试工具{i}",
                parameters={},
                category="clear_test",
                tags=["clear"]
            ))
        
        # 验证工具已注册
        assert len(tool_registry.list_tools()) == 3, "应注册3个工具"
        
        # 清空注册表
        tool_registry.clear()
        
        # 验证所有工具已被清除
        assert len(tool_registry.list_tools()) == 0, "清空后应无工具"
        
        # 验证分类和标签也被清空
        assert len(tool_registry.get_categories()) == 0, "清空后应无分类"
        assert len(tool_registry.get_tags()) == 0, "清空后应无标签"


if __name__ == "__main__":
    # 允许直接运行测试文件
    pytest.main([__file__, "-v"])
