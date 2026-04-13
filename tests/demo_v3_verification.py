import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.core.reasoner import Reasoner
from memory.base import SemanticMemory, EpisodicMemory
from agents.orchestrator import CognitiveOrchestrator

async def demo_ingest_and_query():
    reasoner = Reasoner()
    # Neo4j 连接（模拟环境使用 mock 或本地）
    semantic_mem = SemanticMemory(use_mock=True) 
    episodic_mem = EpisodicMemory()
    orch = CognitiveOrchestrator(reasoner, semantic_mem, episodic_mem)
    
    # 1. 灌输知识
    ingest_msg = [
        {"role": "user", "content": "居民小区燃气调压柜选型及痛点：核心痛点包括占地空间有限、噪音扰民。选型要求必须具备切断保护功能，且建议安装防噪声罩。"}
    ]
    print("--- Ingesting Knowledge ---")
    await orch.execute_task(ingest_msg)
    
    # 2. 查询并验证 Trace
    query_msg = [
        {"role": "user", "content": "居民小区场景的核心痛点和选型要求是什么？"}
    ]
    print("\n--- Querying with High Fidelity Trace ---")
    response = await orch.execute_task(query_msg)
    
    print("\n[Final Message]:")
    print(response.get("message"))
    
    print("\n[Reasoning Trace Snapshot]:")
    for t in response.get("trace", []):
        print(f"Tool: {t.get('tool')}")
        print(f"Result Summary: {t.get('result', {}).get('summary')}")
        if "metacognition" in t.get("result", {}):
            print(f"Metacognition: {t['result']['metacognition'].get('result')[:100]}...")

if __name__ == "__main__":
    asyncio.run(demo_ingest_and_query())
