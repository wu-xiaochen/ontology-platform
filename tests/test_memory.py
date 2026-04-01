"""
记忆治理器测试 (Memory Governance Tests)

测试记忆健康度监控和治理功能。
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from ontology_platform.memory import (
    MemoryGovernance,
    HealthReport,
    DriftAlert
)


class TestDriftAlert:
    """测试 DriftAlert 数据类"""
    
    def test_drift_alert_creation(self):
        """测试漂移警告创建"""
        alert = DriftAlert(
            type="class_drift",
            severity="high",
            description="检测到类层次结构变化",
            affected_entities=["Entity1", "Entity2"]
        )
        
        assert alert.type == "class_drift"
        assert alert.severity == "high"
        assert alert.description == "检测到类层次结构变化"
        assert alert.affected_entities == ["Entity1", "Entity2"]
        assert isinstance(alert.timestamp, datetime)
    
    def test_drift_alert_default_timestamp(self):
        """测试默认时间戳"""
        alert = DriftAlert(
            type="property_drift",
            severity="medium",
            description="属性定义变化"
        )
        
        # 时间戳应该接近当前时间
        time_diff = abs((datetime.now() - alert.timestamp).total_seconds())
        assert time_diff < 60  # 1 分钟内
    
    def test_drift_alert_severity_levels(self):
        """测试严重程度等级"""
        valid_severities = ["low", "medium", "high"]
        
        for severity in valid_severities:
            alert = DriftAlert(
                type="relationship_drift",
                severity=severity,
                description="测试"
            )
            assert alert.severity == severity


class TestHealthReport:
    """测试 HealthReport 数据类"""
    
    def test_health_report_creation(self):
        """测试健康度报告创建"""
        report = HealthReport(
            overall_score=85.5,
            class_coverage=90.0,
            property_consistency=95.0,
            logical_consistency=True,
            drift_alerts=[],
            recommendations=["建议 1", "建议 2"]
        )
        
        assert report.overall_score == 85.5
        assert report.class_coverage == 90.0
        assert report.property_consistency == 95.0
        assert report.logical_consistency is True
        assert len(report.drift_alerts) == 0
        assert len(report.recommendations) == 2
        assert isinstance(report.last_check, datetime)
    
    def test_health_report_score_range(self):
        """测试得分范围"""
        # 有效范围
        report = HealthReport(
            overall_score=75.0,
            class_coverage=80.0,
            property_consistency=85.0,
            logical_consistency=True
        )
        assert 0 <= report.overall_score <= 100
    
    def test_health_report_with_alerts(self):
        """测试带警告的报告"""
        alerts = [
            DriftAlert(
                type="class_drift",
                severity="high",
                description="严重漂移"
            ),
            DriftAlert(
                type="property_drift",
                severity="low",
                description="轻微漂移"
            )
        ]
        
        report = HealthReport(
            overall_score=65.0,
            class_coverage=70.0,
            property_consistency=75.0,
            logical_consistency=True,
            drift_alerts=alerts
        )
        
        assert len(report.drift_alerts) == 2
        assert report.drift_alerts[0].severity == "high"
        assert report.drift_alerts[1].severity == "low"


class TestMemoryGovernance:
    """测试 MemoryGovernance 类"""
    
    def test_initialization(self):
        """测试初始化"""
        gov = MemoryGovernance(ontology_graph=None)
        
        assert gov.graph is None
        assert gov.baseline is None
        assert isinstance(gov.history, list)
    
    def test_initialization_with_graph(self):
        """测试带图的初始化"""
        mock_graph = {"nodes": [], "edges": []}
        gov = MemoryGovernance(ontology_graph=mock_graph)
        
        assert gov.graph == mock_graph
    
    def test_thresholds(self):
        """测试阈值配置"""
        gov = MemoryGovernance()
        
        # 检查默认阈值
        assert gov.COVERAGE_THRESHOLD == 0.8
        assert gov.CONSISTENCY_THRESHOLD == 0.9
        assert gov.DRIFT_THRESHOLD == 0.15
    
    def test_check_health_returns_report(self):
        """测试健康检查返回报告"""
        gov = MemoryGovernance()
        
        # 即使没有图，也应该能执行检查
        report = gov.check_health()
        
        assert isinstance(report, HealthReport)
        assert hasattr(report, 'overall_score')
        assert hasattr(report, 'class_coverage')
        assert hasattr(report, 'property_consistency')
        assert hasattr(report, 'logical_consistency')
        assert hasattr(report, 'drift_alerts')
        assert hasattr(report, 'recommendations')
    
    def test_check_health_score_calculation(self):
        """测试健康度得分计算"""
        gov = MemoryGovernance()
        report = gov.check_health()
        
        # 得分应该在 0-100 范围内
        assert 0 <= report.overall_score <= 100
        
        # 各分量也应该在合理范围
        assert 0 <= report.class_coverage <= 100
        assert 0 <= report.property_consistency <= 100
    
    def test_check_health_logical_consistency_boolean(self):
        """测试逻辑一致性是布尔值"""
        gov = MemoryGovernance()
        report = gov.check_health()
        
        assert isinstance(report.logical_consistency, bool)


class TestHealthScenarios:
    """测试不同健康场景"""
    
    def test_healthy_memory(self):
        """测试健康记忆"""
        # 模拟健康报告
        report = HealthReport(
            overall_score=95.0,
            class_coverage=98.0,
            property_consistency=97.0,
            logical_consistency=True,
            drift_alerts=[]
        )
        
        # 健康度应该高
        assert report.overall_score >= 90
        assert len(report.drift_alerts) == 0
    
    def test_unhealthy_memory(self):
        """测试不健康记忆"""
        alerts = [
            DriftAlert(
                type="class_drift",
                severity="high",
                description="严重类漂移"
            ),
            DriftAlert(
                type="relationship_drift",
                severity="high",
                description="严重关系漂移"
            )
        ]
        
        report = HealthReport(
            overall_score=45.0,
            class_coverage=50.0,
            property_consistency=55.0,
            logical_consistency=False,
            drift_alerts=alerts
        )
        
        # 健康度应该低
        assert report.overall_score < 70
        assert len(report.drift_alerts) > 0
        assert report.logical_consistency is False
    
    def test_warning_threshold(self):
        """测试警告阈值"""
        report = HealthReport(
            overall_score=70.0,  # 刚好在警告线
            class_coverage=75.0,
            property_consistency=80.0,
            logical_consistency=True
        )
        
        # 应该触发警告
        assert report.overall_score >= 70


class TestIntegration:
    """集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建治理器
        gov = MemoryGovernance()
        
        # 2. 执行健康检查
        report = gov.check_health()
        
        # 3. 验证报告结构
        assert isinstance(report, HealthReport)
        assert 0 <= report.overall_score <= 100
        
        # 4. 检查历史记录
        assert isinstance(gov.history, list)
    
    def test_multiple_checks(self):
        """测试多次检查"""
        gov = MemoryGovernance()
        
        # 执行多次检查
        reports = []
        for _ in range(3):
            report = gov.check_health()
            reports.append(report)
        
        # 应该有 3 次检查
        assert len(reports) == 3
        
        # 每次检查都应该返回有效报告
        for report in reports:
            assert isinstance(report, HealthReport)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
