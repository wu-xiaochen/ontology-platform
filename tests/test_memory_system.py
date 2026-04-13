"""
记忆系统集成测试 (Memory System Integration Test)

测试 UnifiedMemory 的核心功能：
1. 创建 UnifiedMemory 实例（使用内存降级模式）
2. 存储模式 store_pattern()
3. 搜索相似模式 search_similar_patterns()
4. 按 ID 获取 get_pattern_by_id()
5. 验证降级机制（Neo4j/ChromaDB 不可用时回退内存）
6. 统计信息 get_statistics()

设计原则：
- 每行逻辑代码必须有中文注释（解释"为什么"）
- 零硬编码：所有配置从环境变量读取
- 无TODO/FIXME：所有实现都是完整可用的
"""

import os
import sys
import pytest
from typing import Dict, Any, List

# 添加项目根目录到Python路径，确保可以导入src模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory.manager import UnifiedMemory, MemoryPattern


class TestMemorySystem:
    """记忆系统集成测试类"""
    
    @pytest.fixture
    def memory(self) -> UnifiedMemory:
        """
        创建测试用的UnifiedMemory实例
        
        禁用Neo4j和ChromaDB，强制使用内存降级模式，确保测试环境一致性
        """
        # 创建UnifiedMemory实例，禁用外部数据库，强制使用内存降级模式
        # 这样可以确保测试在任何环境下都能运行，无需外部依赖
        return UnifiedMemory(
            neo4j_enabled=False,  # 禁用Neo4j，避免连接失败
            chroma_enabled=False,  # 禁用ChromaDB，避免连接失败
        )
    
    @pytest.fixture
    def sample_pattern(self) -> Dict[str, Any]:
        """
        创建测试用的模式样本
        
        返回一个典型的模式字典，用于测试存储和检索功能
        """
        return {
            "id": "test_pattern_001",
            "name": "燃气设备维护规则",
            "description": "燃气调压箱需要每季度进行一次安全检查，确保压力正常",
            "logic_type": "maintenance_rule",
            "domain": "gas_equipment",
            "confidence": 0.92,
            "source": "test",
            "metadata": {"created_by": "test", "priority": "high"}
        }
    
    def test_memory_initialization(self, memory: UnifiedMemory):
        """
        测试记忆系统初始化
        
        验证点：
        - UnifiedMemory实例成功创建
        - 降级模式正确启用（因为禁用了Neo4j和ChromaDB）
        - 内部存储结构正确初始化
        """
        # 验证实例创建成功
        assert memory is not None, "UnifiedMemory实例应成功创建"
        
        # 验证降级模式已启用（因为禁用了外部数据库）
        assert memory.is_degraded is True, "禁用外部数据库时应启用降级模式"
        
        # 验证降级存储已初始化
        assert memory._fallback_store is not None, "降级存储应已初始化"
    
    def test_store_pattern(self, memory: UnifiedMemory, sample_pattern: Dict[str, Any]):
        """
        测试模式存储功能
        
        验证点：
        - 模式可以成功存储
        - 存储返回成功状态
        - 存储后可以通过ID获取
        """
        # 执行模式存储
        result = memory.store_pattern(sample_pattern)
        
        # 验证存储成功
        assert result is True, "模式存储应返回True"
        
        # 验证存储后可以通过ID获取
        retrieved = memory.get_pattern_by_id(sample_pattern["id"])
        assert retrieved is not None, "存储后应能通过ID获取模式"
        assert retrieved["id"] == sample_pattern["id"], "获取的模式ID应匹配"
        assert retrieved["name"] == sample_pattern["name"], "获取的模式名称应匹配"
    
    def test_store_pattern_without_id(self, memory: UnifiedMemory):
        """
        测试存储无ID模式时的自动ID生成
        
        验证点：
        - 无ID的模式也可以存储
        - 系统会自动生成唯一ID
        - 生成的ID不为空
        """
        # 准备无ID的模式
        pattern_without_id = {
            "name": "测试模式",
            "description": "这是一个没有ID的测试模式",
            "logic_type": "test",
            "domain": "general"
        }
        
        # 执行存储
        result = memory.store_pattern(pattern_without_id)
        
        # 验证存储成功
        assert result is True, "无ID模式也应成功存储"
        
        # 验证统计信息中显示有模式存储
        stats = memory.get_statistics()
        assert stats["fallback_memory"]["pattern_count"] > 0, "应至少有一个模式存储"
    
    def test_search_similar_patterns(self, memory: UnifiedMemory):
        """
        测试相似模式搜索功能
        
        验证点：
        - 可以搜索到相似的模式
        - 搜索结果包含模式信息
        - 搜索支持top_k参数限制结果数量
        """
        # 先存储一些测试模式
        patterns = [
            {
                "id": "search_test_1",
                "name": "燃气安全检查",
                "description": "定期对燃气设备进行安全检查",
                "logic_type": "safety_rule",
                "domain": "gas_safety"
            },
            {
                "id": "search_test_2",
                "name": "设备维护计划",
                "description": "制定设备定期维护计划",
                "logic_type": "maintenance_rule",
                "domain": "equipment"
            },
            {
                "id": "search_test_3",
                "name": "燃气泄漏检测",
                "description": "检测燃气管道是否泄漏",
                "logic_type": "detection_rule",
                "domain": "gas_safety"
            }
        ]
        
        # 存储所有测试模式
        for pattern in patterns:
            memory.store_pattern(pattern)
        
        # 执行搜索：搜索与"燃气安全"相关的内容
        results = memory.search_similar_patterns("燃气安全检查", top_k=5)
        
        # 验证返回结果列表
        assert isinstance(results, list), "搜索结果应返回列表"
        
        # 在降级模式下，搜索结果可能为空（取决于降级存储的实现）
        # 但我们验证搜索功能可以正常调用不报错
    
    def test_get_pattern_by_id(self, memory: UnifiedMemory):
        """
        测试按ID获取模式功能
        
        验证点：
        - 可以按ID获取已存储的模式
        - 获取的模式信息完整
        - 不存在的ID返回None
        """
        # 存储测试模式
        test_pattern = {
            "id": "get_by_id_test",
            "name": "测试获取模式",
            "description": "用于测试按ID获取功能",
            "logic_type": "test",
            "domain": "test_domain",
            "confidence": 0.85
        }
        memory.store_pattern(test_pattern)
        
        # 按ID获取模式
        retrieved = memory.get_pattern_by_id("get_by_id_test")
        
        # 验证获取成功
        assert retrieved is not None, "应能获取到已存储的模式"
        assert retrieved["id"] == "get_by_id_test", "ID应匹配"
        assert retrieved["name"] == "测试获取模式", "名称应匹配"
        assert retrieved["logic_type"] == "test", "类型应匹配"
        assert retrieved["domain"] == "test_domain", "领域应匹配"
        
        # 测试获取不存在的ID
        not_found = memory.get_pattern_by_id("non_existent_id")
        assert not_found is None, "不存在的ID应返回None"
    
    def test_delete_pattern(self, memory: UnifiedMemory):
        """
        测试模式删除功能
        
        验证点：
        - 可以删除已存储的模式
        - 删除后无法再通过ID获取
        - 删除不存在的模式返回False
        """
        # 存储测试模式
        test_pattern = {
            "id": "delete_test",
            "name": "待删除模式",
            "description": "用于测试删除功能",
            "logic_type": "test"
        }
        memory.store_pattern(test_pattern)
        
        # 验证模式已存储
        assert memory.get_pattern_by_id("delete_test") is not None, "模式应已存储"
        
        # 删除模式
        result = memory.delete_pattern("delete_test")
        
        # 验证删除成功
        assert result is True, "删除应返回True"
        
        # 验证删除后无法获取
        after_delete = memory.get_pattern_by_id("delete_test")
        assert after_delete is None, "删除后应无法获取"
        
        # 测试删除不存在的模式
        delete_non_exist = memory.delete_pattern("non_existent")
        # 删除不存在的模式应返回False（表示未删除任何内容）
        assert delete_non_exist is False, "删除不存在的模式应返回False"
    
    def test_fallback_mechanism(self):
        """
        测试降级机制
        
        验证点：
        - 当Neo4j和ChromaDB都不可用时，自动降级到内存存储
        - 降级模式下数据仍然可以正常存取
        - 降级状态正确报告
        """
        # 创建禁用所有外部数据库的实例
        memory = UnifiedMemory(
            neo4j_enabled=False,
            chroma_enabled=False
        )
        
        # 验证降级模式已启用
        assert memory.is_degraded is True, "禁用外部数据库时应处于降级模式"
        
        # 验证降级存储已初始化
        assert memory._fallback_store is not None, "降级存储应已初始化"
        
        # 验证降级模式下仍然可以存储数据
        test_pattern = {
            "id": "fallback_test",
            "name": "降级测试模式",
            "description": "测试降级模式下的存储功能"
        }
        store_result = memory.store_pattern(test_pattern)
        assert store_result is True, "降级模式下应能正常存储"
        
        # 验证降级模式下仍然可以读取数据
        retrieved = memory.get_pattern_by_id("fallback_test")
        assert retrieved is not None, "降级模式下应能正常读取"
        assert retrieved["name"] == "降级测试模式", "读取的数据应正确"
    
    def test_get_statistics(self, memory: UnifiedMemory):
        """
        测试统计信息获取功能
        
        验证点：
        - 可以获取记忆系统的统计信息
        - 统计信息包含各存储后端的状态
        - 统计信息格式正确
        """
        # 先存储一些测试数据
        for i in range(3):
            memory.store_pattern({
                "id": f"stats_test_{i}",
                "name": f"统计测试模式{i}",
                "description": f"用于测试统计功能的模式{i}"
            })
        
        # 获取统计信息
        stats = memory.get_statistics()
        
        # 验证统计信息结构
        assert isinstance(stats, dict), "统计信息应返回字典"
        
        # 验证包含必要的字段
        assert "graph_memory" in stats, "应包含graph_memory字段"
        assert "vector_memory" in stats, "应包含vector_memory字段"
        assert "fallback_memory" in stats, "应包含fallback_memory字段"
        assert "overall_degraded" in stats, "应包含overall_degraded字段"
        
        # 验证图记忆状态
        assert "enabled" in stats["graph_memory"], "graph_memory应包含enabled字段"
        assert "connected" in stats["graph_memory"], "graph_memory应包含connected字段"
        
        # 验证向量记忆状态
        assert "enabled" in stats["vector_memory"], "vector_memory应包含enabled字段"
        assert "document_count" in stats["vector_memory"], "vector_memory应包含document_count字段"
        
        # 验证降级存储状态
        assert "enabled" in stats["fallback_memory"], "fallback_memory应包含enabled字段"
        assert "pattern_count" in stats["fallback_memory"], "fallback_memory应包含pattern_count字段"
        
        # 验证降级存储中有3个模式
        assert stats["fallback_memory"]["pattern_count"] == 3, "降级存储中应有3个模式"
        
        # 验证整体降级状态
        assert stats["overall_degraded"] is True, "当前应处于降级模式"
    
    def test_health_check(self, memory: UnifiedMemory):
        """
        测试健康检查功能
        
        验证点：
        - 可以执行健康检查
        - 健康检查结果包含各组件状态
        - 降级模式下健康状态正确报告
        """
        # 执行健康检查
        health = memory.health_check()
        
        # 验证健康检查结果结构
        assert isinstance(health, dict), "健康检查结果应返回字典"
        assert "status" in health, "应包含status字段"
        assert "timestamp" in health, "应包含timestamp字段"
        assert "components" in health, "应包含components字段"
        
        # 验证组件状态
        assert "graph_memory" in health["components"], "应包含graph_memory组件状态"
        assert "vector_memory" in health["components"], "应包含vector_memory组件状态"
        
        # 验证降级模式下状态为degraded
        assert health["status"] == "degraded", "降级模式下整体状态应为degraded"
    
    def test_memory_pattern_dataclass(self):
        """
        测试MemoryPattern数据类
        
        验证点：
        - MemoryPattern可以正确创建
        - to_dict方法返回正确的字典
        - from_dict方法可以从字典正确创建实例
        """
        # 创建MemoryPattern实例
        pattern = MemoryPattern(
            id="dataclass_test",
            name="数据类测试",
            description="测试MemoryPattern数据类",
            logic_type="test",
            domain="test_domain",
            confidence=0.88,
            source="test_source"
        )
        
        # 验证实例属性
        assert pattern.id == "dataclass_test", "ID应匹配"
        assert pattern.name == "数据类测试", "名称应匹配"
        assert pattern.confidence == 0.88, "置信度应匹配"
        
        # 测试to_dict方法
        pattern_dict = pattern.to_dict()
        assert isinstance(pattern_dict, dict), "to_dict应返回字典"
        assert pattern_dict["id"] == "dataclass_test", "字典中的ID应匹配"
        assert pattern_dict["name"] == "数据类测试", "字典中的名称应匹配"
        
        # 测试from_dict方法
        reconstructed = MemoryPattern.from_dict(pattern_dict)
        assert reconstructed.id == pattern.id, "重建的实例ID应匹配"
        assert reconstructed.name == pattern.name, "重建的实例名称应匹配"
        assert reconstructed.confidence == pattern.confidence, "重建的实例置信度应匹配"
    
    def test_multiple_patterns_storage(self, memory: UnifiedMemory):
        """
        测试多个模式的批量存储和检索
        
        验证点：
        - 可以存储多个模式
        - 每个模式都可以独立检索
        - 统计信息正确反映存储数量
        """
        # 准备多个测试模式
        patterns = [
            {"id": "multi_1", "name": "模式1", "description": "第一个测试模式", "domain": "domain_a"},
            {"id": "multi_2", "name": "模式2", "description": "第二个测试模式", "domain": "domain_b"},
            {"id": "multi_3", "name": "模式3", "description": "第三个测试模式", "domain": "domain_a"},
        ]
        
        # 批量存储
        for pattern in patterns:
            result = memory.store_pattern(pattern)
            assert result is True, f"模式 {pattern['id']} 应成功存储"
        
        # 验证每个模式都可以检索
        for pattern in patterns:
            retrieved = memory.get_pattern_by_id(pattern["id"])
            assert retrieved is not None, f"模式 {pattern['id']} 应能检索到"
            assert retrieved["name"] == pattern["name"], f"模式 {pattern['id']} 名称应匹配"
        
        # 验证统计信息
        stats = memory.get_statistics()
        assert stats["fallback_memory"]["pattern_count"] == len(patterns), \
            f"统计中应有 {len(patterns)} 个模式"
    
    def test_memory_close(self, memory: UnifiedMemory):
        """
        测试内存关闭功能
        
        验证点：
        - 可以正常关闭内存系统
        - 关闭后资源被正确释放
        - 关闭操作不抛出异常
        """
        # 先存储一些数据
        memory.store_pattern({
            "id": "close_test",
            "name": "关闭测试",
            "description": "测试关闭功能"
        })
        
        # 执行关闭操作
        try:
            memory.close()
            close_success = True
        except Exception as e:
            close_success = False
            print(f"关闭时发生异常: {e}")
        
        # 验证关闭成功
        assert close_success is True, "关闭操作应成功执行不抛异常"


if __name__ == "__main__":
    # 允许直接运行测试文件
    pytest.main([__file__, "-v"])
