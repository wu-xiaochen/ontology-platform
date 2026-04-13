import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.clawra import Clawra
from src.perception.extractor import KnowledgeExtractor
from src.utils.config import get_config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_gas_regulator_domain():
    print("\n" + "="*60)
    print("🚀 Clawra 燃气调压箱全链路 backend 验证测试")
    print("="*60 + "\n")

    # 1. 初始化系统
    # 启用记忆系统以测试持久化与进化
    clawra = Clawra(enable_memory=True, neo4j_enabled=False, chroma_enabled=True)
    extractor = KnowledgeExtractor(use_mock_llm=False) # 使用真实 LLM 以验证抽取质量
    
    # 2. 读取知识库文档
    kb_path = "data/gas_regulator_knowledge.md"
    if not os.path.exists(kb_path):
        logger.error(f"知识文件 {kb_path} 不存在！")
        return
    
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb_text = f.read()
    
    print(f"📦 [Step 1] 正在处理知识库文档 (长度: {len(kb_text)})...")
    
    # 3. 知识抽取与注入
    # 使用 MetaLearner 流程，它会自动分块、抽取并存入图谱/向量库
    result = clawra.learn(kb_text, domain_hint="gas_equipment")
    
    print(f"✅ 知识注入完成:")
    print(f"   - 识别领域: {result.get('domain')}")
    print(f"   - 学习模式: {len(result.get('learned_patterns', []))} 个")
    print(f"   - 提取事实: {result.get('facts_added', 0)} 条")
    
    # 4. 模拟场景推理
    scenario = "我们计划为一个拥有 200 户居民的新社区进行燃气供应。管道进口压力为 0.4MPa。请推荐合适的设备配置，并说明安装过程中必须检查的关键质量红线。"
    
    print(f"\n🔍 [Step 2] 模拟业务场景推理:")
    print(f"   输入: {scenario}")
    
    # 使用编排器执行推理，它会结合 Graph-RAG 和情节记忆
    reasoning_result = clawra.orchestrate(scenario)
    
    print(f"\n🧠 [Mental Trace]:")
    for step in reasoning_result.get("trace", []):
        print(f"   → {step}")
    
    print(f"\n📝 [Final Conclusion]:")
    print(f"   {reasoning_result.get('answer')}")
    
    # 5. 触发自主进化
    print(f"\n🌀 [Step 3] 触发自主进化闭环 (Skill Distillation)...")
    
    evolve_result = await clawra.evolve()
    
    print(f"✅ 进化任务执行成功:")
    print(f"   - 评估事实: {evolve_result['results']['evaluated_facts']}")
    print(f"   - 冲突修复: {evolve_result['results']['conflicts_resolved']}")
    print(f"   - 蒸馏技能: {evolve_result['results']['skills_distilled']} 个")
    
    # 6. 验证技能库
    skill_dir = "data/skills"
    if os.path.exists(skill_dir):
        skills = os.listdir(skill_dir)
        print(f"\n💾 [Skill Library]: 发现 {len(skills)} 个持久化技能文件")
        for s in skills:
            if s.endswith(".py"):
                print(f"   - {s}")
    
    print("\n" + "="*60)
    print("🎉 燃气调压箱全链路 backend 验证完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_gas_regulator_domain())
