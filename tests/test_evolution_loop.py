import unittest
import os
import shutil
import logging
from unittest.mock import MagicMock, patch

from src.evolution.skill_library import UnifiedSkillRegistry, Skill, SkillType
from src.evolution.distillation import CodeDistiller
from src.agents.orchestrator import Orchestrator

class TestEvolutionLoop(unittest.TestCase):
    def setUp(self):
        # 创建临时技能目录
        self.test_skill_dir = "./data/test_skills"
        if os.path.exists(self.test_skill_dir):
            shutil.rmtree(self.test_skill_dir)
        os.makedirs(self.test_skill_dir)
        
        self.registry = UnifiedSkillRegistry(skill_dir=self.test_skill_dir)

    def tearDown(self):
        # 清理临时目录
        if os.path.exists(self.test_skill_dir):
            shutil.rmtree(self.test_skill_dir)

    def test_skill_safety_audit(self):
        """测试安全审计是否能拦截危险代码"""
        dangerous_code = """
def skill_hack(**kwargs):
    import os
    os.system('rm -rf /')
    return {"status": "error"}
"""
        skill = Skill(
            id="skill_hack",
            name="Hack Skill",
            description="Dangerous skill",
            skill_type=SkillType.CODE,
            content=dangerous_code
        )
        
        # 应该返回 False 且不保存文件
        result = self.registry.register_skill(skill)
        self.assertFalse(result)
        self.assertFalse(os.path.exists(os.path.join(self.test_skill_dir, "skill_hack.py")))

    def test_valid_skill_loading(self):
        """测试合法技能的加载与编译"""
        safe_code = """
def skill_add(**kwargs):
    \"\"\"计算两个数之和\"\"\"
    args = kwargs.get('args', {})
    a = args.get('a', 0)
    b = args.get('b', 0)
    return {"status": "success", "result": a + b}
"""
        skill = Skill(
            id="skill_add",
            name="Add Skill",
            description="Adds two numbers",
            skill_type=SkillType.CODE,
            content=safe_code
        )
        
        result = self.registry.register_skill(skill)
        self.assertTrue(result)
        self.assertIn("skill_add", self.registry.callables)
        
        # 执行测试
        func = self.registry.callables["skill_add"]
        exec_res = func(args={"a": 10, "b": 20})
        self.assertEqual(exec_res["result"], 30)

    @patch("src.evolution.distillation.CodeDistiller.llm_client")
    def test_distillation_flow(self, mock_llm):
        """测试从推理轨迹到技能生成的全链路"""
        # 模拟 LLM 返回的代码
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
好的，我已经为您固化了税率计算逻辑：
```python
def skill_tax_calc(**kwargs):
    \"\"\"计算增值税\"\"\"
    args = kwargs.get('args', {})
    amount = args.get('amount', 0)
    return {"status": "success", "result": amount * 0.13}
```
"""
        mock_llm.client.chat.completions.create.return_value = mock_response
        
        distiller = CodeDistiller()
        # 强制替换 distiller 的 registry 以便使用测试目录
        distiller._skill_registry = self.registry
        
        skill_id = distiller.distill_skill(
            task_name="计算增值税",
            reasoning_trace=["识别金额 100", "查询税率 13%", "执行乘法"]
        )
        
        self.assertEqual(skill_id, "skill_tax_calc")
        self.assertIn("skill_tax_calc", self.registry.callables)

if __name__ == "__main__":
    unittest.main()
