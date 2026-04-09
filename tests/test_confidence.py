#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for confidence module"""

import sys
sys.path.insert(0, 'src')

from src.eval.confidence import Evidence, ConfidenceResult, ConfidenceCalculator


def test_evidence_creation():
    """Test evidence creation"""
    e = Evidence(source="test", reliability=0.9, content="test content")
    assert e.source == "test"
    assert e.reliability == 0.9
    assert e.content == "test content"


def test_confidence_result():
    """Test confidence result structure"""
    r = ConfidenceResult(value=0.85, method="test", evidence_count=1)
    assert r.value == 0.85
    assert r.method == "test"
    assert r.evidence_count == 1


def test_calculator_weighted():
    """Test weighted confidence calculation"""
    calc = ConfidenceCalculator(default_reliability=0.7)
    evidence = [
        Evidence(source="src1", reliability=0.9, content="A"),
        Evidence(source="src2", reliability=0.8, content="B"),
    ]
    result = calc._calculate_weighted(evidence)
    assert 0 <= result.value <= 1
    assert result.evidence_count == 2


def test_calculator_multiplicative():
    """Test multiplicative confidence calculation"""
    calc = ConfidenceCalculator(default_reliability=0.7)
    evidence = [
        Evidence(source="src1", reliability=0.9, content="A"),
        Evidence(source="src2", reliability=0.8, content="B"),
    ]
    result = calc._calculate_multiplicative(evidence)
    assert 0 <= result.value <= 1
    assert result.evidence_count == 2


def test_source_weights():
    """Test source weight management"""
    calc = ConfidenceCalculator()
    calc.set_source_weight("trusted", 0.95)
    weight = calc.get_source_weight("trusted")
    assert weight == 0.95

    # Default source should return default_reliability
    default_weight = calc.get_source_weight("unknown")
    assert default_weight == 1.0


if __name__ == "__main__":
    test_evidence_creation()
    test_confidence_result()
    test_calculator_weighted()
    test_calculator_multiplicative()
    test_source_weights()
    print("All tests passed.")
