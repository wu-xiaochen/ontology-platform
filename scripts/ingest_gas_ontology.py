import sys
import os
import asyncio

# 增加 src 路径
sys.path.insert(0, os.path.abspath('.'))

from src.core.reasoner import Reasoner
from src.memory.base import SemanticMemory, EpisodicMemory
from src.agents.orchestrator import CognitiveOrchestrator
from src.perception.extractor import KnowledgeExtractor

KNOWLEDGE_TEXT = """
[此处粘贴用户提供的完整文本...]
"""

async def ingest():
    print("🚀 开始高精度本体知识灌输...")
    
    # 初始化组件
    reasoner = Reasoner()
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "clawra2026")
    
    semantic_mem = SemanticMemory(uri=neo4j_uri, user=neo4j_user, password=neo4j_pass)
    # 尝试连接，连接失败则仅打印警告
    try:
        semantic_mem.connect()
        print("🟢 Neo4j 连接成功")
    except Exception as e:
        print(f"🟡 Neo4j 连接失败 (仅影响落库): {e}")
    
    extractor = KnowledgeExtractor(use_mock_llm=False)
    
    # 1. 提取事实
    print("🧠 正在调用 LLM 进行知识抽取 (分块处理中)...")
    facts = extractor.extract_from_text(KNOWLEDGE_TEXT)
    print(f"✨ 提取完成! 共获取 {len(facts)} 条独立三元组。")
    
    # 2. 存储事实
    print("💾 正在持久化至本体推理引擎与语义网...")
    stored_count = 0
    for fact in facts:
        try:
            reasoner.add_fact(fact)
            if semantic_mem.is_connected:
                semantic_mem.store_fact(fact)
            stored_count += 1
            if stored_count % 10 == 0:
                print(f"  - 已存储 {stored_count} 条...")
        except Exception as e:
            print(f"  - 跳过错误三元组: {fact}, 错误: {e}")
            
    # 3. 最终同步状态
    print(f"\n✅ 灌输任务完成!")
    print(f"总计存入: {stored_count} 条事实")
    print(f"当前推理引擎事实总数: {len(reasoner.facts)}")

if __name__ == "__main__":
    # 注意：这里需要替换为用户提供的真实文本
    import sys
    # 从命令行参数或临时文件中读取文本以避免代码过长
    with open("gas_knowledge.txt", "r", encoding="utf-8") as f:
        KNOWLEDGE_TEXT = f.read()
    
    asyncio.run(ingest())
