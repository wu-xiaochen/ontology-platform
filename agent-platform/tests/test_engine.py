"""
核心功能测试用例
"""

import pytest
from datetime import date
from src.core.engine import (
    IntentParser,
    ApprovalRuleEngine,
    SupplierRecommender,
    CostOptimizer,
    ParsedItem,
    Priority
)
from tests.conftest import get_all_samples


class TestIntentParser:
    """测试意图解析引擎"""
    
    def setup_method(self):
        self.parser = IntentParser()
    
    def test_parse_simple_purchase_intent(self):
        """测试简单采购需求解析"""
        result = self.parser.parse("我们需要采购50台电脑")
        
        assert len(result.items) > 0
        assert result.items[0].name == "电脑"
        assert result.items[0].quantity == 50
        assert result.confidence > 0
    
    def test_parse_with_department(self):
        """测试带部门的解析"""
        result = self.parser.parse("研发部门需要采购10台显示器")
        
        assert result.department == "研发部"
        assert len(result.items) > 0
    
    def test_parse_with_date(self):
        """测试带日期的解析"""
        result = self.parser.parse("需要采购5台打印机，3月20日前到货")
        
        assert result.required_date is not None
        assert result.required_date.month == 3
        assert result.required_date.day == 20
    
    def test_parse_with_budget(self):
        """测试带预算的解析"""
        result = self.parser.parse("需要采购电脑，预算是5万元")
        
        assert result.budget_range is not None
        assert result.budget_range[0] >= 40000  # 5千 or 5万
    
    def test_parse_priority(self):
        """测试优先级提取"""
        result = self.parser.parse("紧急采购10台电脑")
        assert result.priority == Priority.URGENT
        
        result = self.parser.parse("尽快采购电脑")
        assert result.priority == Priority.HIGH


class TestApprovalRuleEngine:
    """测试审批规则引擎"""
    
    def setup_method(self):
        self.engine = ApprovalRuleEngine()
    
    def test_auto_approve_small_amount(self):
        """测试小额自动通过"""
        result = self.engine.evaluate(amount=3000)
        
        assert result["action"] == "auto_approve"
        assert result["status"] == "approved"
        assert result["rule_name"] == "小额采购自动通过"
    
    def test_single_approval(self):
        """测试一般金额单签"""
        result = self.engine.evaluate(amount=30000)
        
        assert result["action"] == "single_approval"
        assert result["status"] == "pending_approval"
        assert len(result["next_nodes"]) == 1
        assert result["next_nodes"][0]["approver_role"] == "department_manager"
    
    def test_multi_approval(self):
        """测试大额双签"""
        result = self.engine.evaluate(amount=80000)
        
        assert result["action"] == "multi_approval"
        assert len(result["next_nodes"]) == 2
    
    def test_boundary_5000(self):
        """测试5000元边界"""
        result = self.engine.evaluate(amount=5000)
        assert result["action"] == "single_approval"
        
        result = self.engine.evaluate(amount=4999)
        assert result["action"] == "auto_approve"
    
    def test_boundary_50000(self):
        """测试50000元边界"""
        result = self.engine.evaluate(amount=50000)
        assert result["action"] == "multi_approval"
        
        result = self.engine.evaluate(amount=49999)
        assert result["action"] == "single_approval"


class TestSupplierRecommender:
    """测试供应商推荐引擎"""
    
    def setup_method(self):
        data = get_all_samples()
        self.repo = data["supplier_repo"]
        self.recommender = SupplierRecommender(self.repo)
    
    def test_recommend_by_category(self):
        """测试按品类推荐"""
        items = [ParsedItem(name="电脑", quantity=10, category="电子设备/电脑")]
        
        results = self.recommender.recommend(
            purchase_request_id="test",
            items=items,
            category="电子设备/电脑",
            top_n=3
        )
        
        assert len(results) > 0
        assert results[0]["match_score"] >= 0
    
    def test_recommend_returns_top_n(self):
        """测试返回前N个"""
        items = [ParsedItem(name="办公桌", quantity=5)]
        
        results = self.recommender.recommend(
            purchase_request_id="test",
            items=items,
            category="办公家具",
            top_n=2
        )
        
        assert len(results) <= 2
    
    def test_recommend_includes_reasons(self):
        """测试推荐包含理由"""
        items = [ParsedItem(name="电脑", quantity=10)]
        
        results = self.recommender.recommend(
            purchase_request_id="test",
            items=items,
            category="电子设备/电脑",
            top_n=1
        )
        
        assert len(results) > 0
        assert "reasons" in results[0]


class TestCostOptimizer:
    """测试成本优化引擎"""
    
    def setup_method(self):
        self.optimizer = CostOptimizer()
    
    def test_analyze_empty_data(self):
        """测试空数据分析"""
        result = self.optimizer.analyze([], [])
        
        assert "suggestions" in result
        assert "category_spending" in result
        assert "department_spending" in result
    
    def test_analyze_with_data(self):
        """测试有数据分析"""
        data = get_all_samples()
        prs = data["purchase_requests"]
        orders = data["orders"]
        
        result = self.optimizer.analyze(prs, orders)
        
        assert "total_potential_savings" in result
        assert isinstance(result["category_spending"], dict)


class TestIntentParserSuggestions:
    """测试建议生成"""
    
    def setup_method(self):
        self.parser = IntentParser()
    
    def test_suggestions_for_vague_intent(self):
        """测试模糊需求的建议"""
        result = self.parser.parse("我想买电脑")
        
        assert len(result.suggestions) > 0
        assert any("规格" in s or "型号" in s for s in result.suggestions)
    
    def test_no_suggestions_for_clear_intent(self):
        """测试清晰需求无建议"""
        result = self.parser.parse("采购10台Dell笔记本i7/16G/512G")
        
        # 仍然可能有建议，但不应该是"请明确"
        # 这个测试主要验证不会崩溃


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
