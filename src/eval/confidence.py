"""
置信度计算模块 (Confidence Calculation)
基于证据的置信度评估和推理链置信度传播
"""

from dataclasses import dataclass, field
from typing import Any, Optional

# D-S 证据理论中的不确定性标记
Unknown = "__Unknown__"


@dataclass
class Evidence:
    """证据"""
    source: str           # 证据来源
    reliability: float    # 来源可靠性 [0, 1]
    content: Any          # 证据内容
    timestamp: Optional[str] = None
    
    
@dataclass
class ConfidenceResult:
    """置信度结果"""
    value: float                    # 置信度值 [0, 1]
    method: str                     # 计算方法
    evidence_count: int = 0         # 证据数量
    evidence: list[Evidence] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


class ConfidenceCalculator:
    """
    置信度计算器
    
    支持多种置信度计算方法:
    - 基于证据数量的计算
    - 基于来源可靠性的加权
    - 贝叶斯推断
    - 推理链传播
    
    示例:
        calc = ConfidenceCalculator()
        result = calc.calculate(
            evidence=[Evidence(source="dbpedia", reliability=0.9, content="...")],
            method="bayesian"
        )
        print(f"置信度: {result.value:.2f}")
    """
    
    def __init__(self, default_reliability: float = 0.5, default_source_weight: float = 1.0):
        """
        初始化
        
        Args:
            default_reliability: 默认证据可靠性
            default_source_weight: 默认来源权重 (1.0 = 完全信任)
        """
        self.default_reliability = default_reliability
        self.default_source_weight = default_source_weight
        self.source_weights: dict[str, float] = {}
        
    def calculate(
        self,
        evidence: list[Evidence],
        method: str = "weighted",
        prior: float = 0.5,
        **kwargs
    ) -> ConfidenceResult:
        """
        计算置信度
        
        Args:
            evidence: 证据列表
            method: 计算方法 (weighted, bayesian, multiplicative, Dempster-Shafer)
            prior: 先验概率 (用于贝叶斯方法)
            **kwargs: 其他参数
        
        Returns:
            ConfidenceResult: 置信度结果
        """
        if not evidence:
            return ConfidenceResult(
                value=0.0,
                method=method,
                evidence_count=0
            )
        
        if method == "weighted":
            return self._calculate_weighted(evidence)
        elif method == "bayesian":
            return self._calculate_bayesian(evidence, prior)
        elif method == "multiplicative":
            return self._calculate_multiplicative(evidence)
        elif method == "dempster_shafer":
            return self._calculate_dempster_shafer(evidence)
        else:
            raise ValueError(f"未知方法: {method}")
    
    def _calculate_weighted(self, evidence: list[Evidence]) -> ConfidenceResult:
        """加权平均法"""
        # 使用source_weights进行加权，权重影响最终置信度
        weights = [self.get_source_weight(e.source) for e in evidence]
        total_weight = sum(weights)
        if total_weight == 0:
            return ConfidenceResult(value=0.0, method="weighted")
        
        # 加权平均：(权重1*可靠性1 + 权重2*可靠性2 + ...) / 证据数量
        weighted_sum = sum(w * e.reliability for w, e in zip(weights, evidence))
        confidence = weighted_sum / len(evidence)
        
        return ConfidenceResult(
            value=confidence,
            method="weighted",
            evidence_count=len(evidence),
            evidence=evidence,
            details={'total_weight': total_weight}
        )
    
    def _calculate_bayesian(self, evidence: list[Evidence], prior: float) -> ConfidenceResult:
        """
        贝叶斯推断法
        
        使用贝叶斯更新规则:
        P(H|E) = P(E|H) * P(H) / P(E)
        
        简化实现: 使用似然比
        """
        # 计算似然比
        likelihood_ratio = 1.0
        for e in evidence:
            # 将可靠性转换为似然
            p_e_given_h = e.reliability  # P(E|真)
            p_e_given_not_h = 1 - e.reliability  # P(E|假)
            if p_e_given_not_h > 0:
                likelihood_ratio *= p_e_given_h / p_e_given_not_h
        
        # 贝叶斯更新
        posterior = (likelihood_ratio * prior) / (likelihood_ratio * prior + (1 - prior))
        
        # 限制在 [0, 1]
        posterior = max(0.0, min(1.0, posterior))
        
        return ConfidenceResult(
            value=posterior,
            method="bayesian",
            evidence_count=len(evidence),
            evidence=evidence,
            details={'prior': prior, 'likelihood_ratio': likelihood_ratio}
        )
    
    def _calculate_multiplicative(self, evidence: list[Evidence]) -> ConfidenceResult:
        """
        乘法合成法
        
        综合多个证据的置信度:
        C = 1 - Π(1 - w_i * c_i)
        """
        product = 1.0
        for e in evidence:
            product *= (1 - e.reliability)
        
        confidence = 1 - product
        
        return ConfidenceResult(
            value=confidence,
            method="multiplicative",
            evidence_count=len(evidence),
            evidence=evidence
        )
    
    def _calculate_dempster_shafer(self, evidence: list[Evidence]) -> ConfidenceResult:
        """
        Dempster-Shafer 证据理论
        
        计算信度函数和似真度
        """
        # 组合所有证据
        combined_m = {True: 0.0, False: 0.0, Unknown: 1.0}
        
        for e in evidence:
            # 信念分配
            belief = e.reliability
            new_combined = {}
            
            for h1, m1 in combined_m.items():
                for h2 in [True, False, Unknown]:
                    m2 = 0.0
                    if h2 is True:
                        m2 = belief
                    elif h2 is False:
                        m2 = 0.0
                    else:
                        m2 = 1 - belief
                    
                    # D-S 组合规则
                    if h1 == Unknown or h2 == Unknown:
                        new_h = Unknown
                    elif h1 == h2:
                        new_h = h1
                    else:
                        new_h = Unknown
                    
                    new_combined[new_h] = new_combined.get(new_h, 0) + m1 * m2
        
        # 归一化
        total = sum(new_combined.values())
        if total > 0:
            for k in new_combined:
                new_combined[k] /= total
        
        confidence = new_combined.get(True, 0.0)
        
        return ConfidenceResult(
            value=confidence,
            method="dempster_shafer",
            evidence_count=len(evidence),
            evidence=evidence,
            details={'mass': new_combined}
        )
    
    def propagate_confidence(
        self,
        chain_confidences: list[float],
        method: str = "min"
    ) -> float:
        """
        推理链置信度传播
        
        Args:
            chain_confidences: 推理链各步骤的置信度
            method: 传播方法 (min, arithmetic, geometric, multiplicative)
        
        Returns:
            传播后的置信度
        """
        if not chain_confidences:
            return 0.0
        
        if method == "min":
            # 取最小值 (保守估计)
            return min(chain_confidences)
        elif method == "arithmetic":
            # 算术平均
            return sum(chain_confidences) / len(chain_confidences)
        elif method == "geometric":
            # 几何平均
            product = 1.0
            for c in chain_confidences:
                product *= c
            return product ** (1 / len(chain_confidences))
        elif method == "multiplicative":
            # 乘法
            product = 1.0
            for c in chain_confidences:
                product *= c
            return product
        else:
            raise ValueError(f"未知传播方法: {method}")
    
    def compute_reasoning_confidence(
        self,
        reasoning_steps: list[dict]
    ) -> ConfidenceResult:
        """
        计算推理链的整体置信度
        
        Args:
            reasoning_steps: 推理步骤列表, 每步包含:
                - premise_confidence: 前提置信度
                - rule_confidence: 规则置信度
                - conclusion_confidence: 结论置信度
        
        Returns:
            整体置信度
        """
        if not reasoning_steps:
            return ConfidenceResult(value=0.0, method="reasoning_chain")
        
        chain_values = []
        for step in reasoning_steps:
            # 每步的置信度由前提和规则共同决定
            premise = step.get('premise_confidence', 0.5)
            rule = step.get('rule_confidence', 0.5)
            
            # 使用最小值作为该步置信度
            step_confidence = min(premise, rule)
            chain_values.append(step_confidence)
        
        overall = self.propagate_confidence(chain_values, method="min")
        
        return ConfidenceResult(
            value=overall,
            method="reasoning_chain",
            evidence_count=len(reasoning_steps),
            details={'chain_confidences': chain_values}
        )
    
    def get_source_weight(self, source: str) -> float:
        """获取来源权重"""
        return self.source_weights.get(source, self.default_source_weight)
    
    def set_source_weight(self, source: str, weight: float):
        """设置来源权重"""
        self.source_weights[source] = max(0.0, min(1.0, weight))
    
    def calibrate(self, predictions: list[tuple[float, float]], method: str = "platt"):
        """
        置信度校准
        
        Args:
            predictions: (预测置信度, 真实标签) 列表
            method: 校准方法 (platt, isotonic)
        """
        # 简化的校准实现
        # 实际项目可使用 sklearn.calibration
        
        if method == "platt":
            # Platt 校准: sigmoid 拟合
            self._platt_calibrate(predictions)
        elif method == "isotonic":
            # 保序回归
            self._isotonic_calibrate(predictions)
    
    def _platt_calibrate(self, predictions: list[tuple[float, float]]):
        """Platt 校准"""
        # 简化实现
        pass
    
    def _isotonic_calibrate(self, predictions: list[tuple[float, float]]):
        """保序回归校准"""
        # 简化实现
        pass


# 便捷函数
def calculate_query_confidence(
    sources: list[tuple[str, float]],
    default_reliability: float = 0.5
) -> ConfidenceResult:
    """
    快速计算查询置信度
    
    Args:
        sources: [(来源名称, 可靠性), ...]
        default_reliability: 默认可靠性
    
    Returns:
        置信度结果
    """
    calc = ConfidenceCalculator(default_reliability)
    evidence = [
        Evidence(source=src, reliability=rel, content=None)
        for src, rel in sources
    ]
    return calc.calculate(evidence, method="weighted")


# 示例用法
if __name__ == '__main__':
    print("=== 置信度计算器测试 ===\n")
    
    # 创建证据
    evidence_list = [
        Evidence(source="Wikipedia", reliability=0.85, content="Paris is the capital of France"),
        Evidence(source="DBpedia", reliability=0.90, content="Paris is capital"),
        Evidence(source="WikiData", reliability=0.88, content="Paris capital"),
    ]
    
    calc = ConfidenceCalculator()
    
    # 测试不同方法
    print("--- 加权平均法 ---")
    result = calc.calculate(evidence_list, method="weighted")
    print(f"置信度: {result.value:.3f}")
    print(f"证据数量: {result.evidence_count}")
    
    print("\n--- 贝叶斯推断 ---")
    result = calc.calculate(evidence_list, method="bayesian", prior=0.5)
    print(f"置信度: {result.value:.3f}")
    print(f"详情: {result.details}")
    
    print("\n--- 乘法合成 ---")
    result = calc.calculate(evidence_list, method="multiplicative")
    print(f"置信度: {result.value:.3f}")
    
    print("\n--- 推理链传播 ---")
    chain = [0.9, 0.8, 0.7]  # 推理链各步的置信度
    propagated = calc.propagate_confidence(chain, method="min")
    print(f"推理链: {chain}")
    print(f"传播置信度 (min): {propagated:.3f}")
    
    print("\n--- 推理链整体置信度 ---")
    reasoning_steps = [
        {'premise_confidence': 0.9, 'rule_confidence': 0.8},
        {'premise_confidence': 0.85, 'rule_confidence': 0.9},
        {'premise_confidence': 0.95, 'rule_confidence': 0.85},
    ]
    result = calc.compute_reasoning_confidence(reasoning_steps)
    print(f"整体置信度: {result.value:.3f}")
    print(f"各步置信度: {result.details['chain_confidences']}")
    
    print("\n--- 快速计算 ---")
    sources = [("Wikipedia", 0.85), ("DBpedia", 0.90), ("个人博客", 0.3)]
    result = calculate_query_confidence(sources)
    print(f"查询置信度: {result.value:.3f}")
