import pytest
import asyncio
import os
from src.agents.orchestrator import CognitiveOrchestrator
from src.core.reasoner import Reasoner
from src.memory.base import SemanticMemory, EpisodicMemory

@pytest.mark.asyncio
async def test_glossary_enriches_extraction():
    """验证业务词典是否能纠正提取偏差"""
    reasoner = Reasoner()
    semantic = SemanticMemory()
    episodic = EpisodicMemory()
    orch = CognitiveOrchestrator(reasoner, semantic, episodic)
    
    # 模拟包含 DDL 的文本
    ddl_text = "CREATE TABLE T_REG_PARM (P1_MAX float, P2_MIN float); -- P1_MAX 是出口压力最大值"
    
    # 调用 ingest 逻辑 (通过调用内部 _execute 函数模拟)
    # 这里我们直接验证 GlossaryEngine 发现能力
    mapping = orch.glossary_engine.discover_glossary(ddl_text)
    assert "P1_MAX" in mapping
    assert "出口压力最大值" in mapping["P1_MAX"]

@pytest.mark.asyncio
async def test_auditor_blocks_fan_trap():
    """验证审计智能体是否能拦截扇形陷阱 (V2 Graph-Backed)"""
    reasoner = Reasoner()
    semantic = SemanticMemory()
    episodic = EpisodicMemory()
    # 模拟连接状态以启用图查询
    semantic.is_connected = True
    orch = CognitiveOrchestrator(reasoner, semantic, episodic)
    
    # 构造一个带有聚合意图且涉及 N 端实体的查询
    risky_query = "计算所有 Supplier 旗下的 Order 总额"
    args = {"query": risky_query}
    
    audit_result = await orch.auditor.audit_plan("query_graph", args)
    assert audit_result["status"] == "BLOCKED"
    assert any("扇形陷阱" in r for r in audit_result["risks"])

@pytest.mark.asyncio
async def test_self_healing_action():
    """验证本体自修复 Action 是否生效"""
    reasoner = Reasoner()
    semantic = SemanticMemory()
    episodic = EpisodicMemory()
    orch = CognitiveOrchestrator(reasoner, semantic, episodic)
    
    params = {"physical_key": "P1_MAX", "business_term": "出口压力上限", "confidence": 0.95}
    result = await orch._execute_update_mapping(params)
    
    assert result["status"] == "SUCCESS"
    # 验证 Reasoner 中是否存入事实
    facts = reasoner.query("P1_MAX", "maps_to", None)
    assert len(facts) > 0
    assert facts[0].object == "出口压力上限"

if __name__ == "__main__":
    asyncio.run(test_glossary_enriches_extraction())
    asyncio.run(test_auditor_blocks_fan_trap())
    asyncio.run(test_self_healing_action())
    print("Deep Integration Tests: Passed")
