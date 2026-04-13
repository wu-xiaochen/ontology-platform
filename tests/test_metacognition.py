"""Tests for Metacognitive Agent"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from src.agents.metacognition import MetacognitiveAgent
from src.core.reasoner import Reasoner, Fact


class TestMetacognitiveAgent:
    """Test metacognitive agent capabilities"""
    
    @pytest.fixture
    def agent(self):
        """Create metacognitive agent for testing"""
        reasoner = Reasoner()
        agent = MetacognitiveAgent(name="TestAgent", reasoner=reasoner)
        return agent
    
    @pytest.mark.asyncio
    async def test_reflection_basic(self, agent):
        """Test basic reflection functionality"""
        thought = "This is a test thought for reflection"
        result = await agent.reflect(thought)
        
        assert "valid" in result
        assert "confidence" in result
        assert "issues" in result
        assert "suggestions" in result
    
    @pytest.mark.asyncio
    async def test_reflection_with_reasoning_steps(self, agent):
        """Test reflection with reasoning steps"""
        thought = "Concluding X based on evidence"
        reasoning_steps = [
            {"confidence": 0.9, "conclusion": "Step 1"},
            {"confidence": 0.7, "conclusion": "Step 2"},
            {"confidence": 0.5, "conclusion": "Step 3"}  # Low confidence
        ]
        
        result = await agent.reflect(thought, reasoning_steps)
        
        assert result["valid"] == True
        assert len(result["issues"]) > 0  # Should detect low confidence step
    
    @pytest.mark.asyncio
    async def test_contradiction_detection(self, agent):
        """Test contradiction detection"""
        # Text with potential contradiction
        contradictory = "This is false but also true"
        has_contradiction = agent._detect_contradictions(contradictory)
        
        # Simple pattern detection
        assert has_contradiction == True
    
    @pytest.mark.asyncio
    async def test_run_basic_task(self, agent):
        """Test running basic task"""
        # Add some facts to reasoner
        agent.reasoner.add_fact(Fact("A", "relates_to", "B", confidence=0.9))
        
        result = await agent.run("Test task")
        
        assert result["status"] == "success"
        assert "inference_steps" in result
        assert "total_confidence" in result
        assert "reflection" in result
        assert "knowledge_boundary" in result
    
    def test_knowledge_boundary_high_confidence(self, agent):
        """Test knowledge boundary with high confidence"""
        result = agent.check_knowledge_boundary("test query", confidence=0.90)
        
        assert result["within_boundary"] == True
        assert result["confidence_level"] == "high"
    
    def test_knowledge_boundary_medium_confidence(self, agent):
        """Test knowledge boundary with medium confidence"""
        result = agent.check_knowledge_boundary("test query", confidence=0.65)
        
        assert result["within_boundary"] == True
        assert result["confidence_level"] == "medium"
    
    def test_knowledge_boundary_low_confidence(self, agent):
        """Test knowledge boundary with low confidence"""
        result = agent.check_knowledge_boundary("test query", confidence=0.45)
        
        # Low confidence (0.45) is still within boundary but with warning
        assert result["confidence_level"] == "low"
        assert result["recommendation"] is not None
    
    def test_knowledge_boundary_very_low_confidence(self, agent):
        """Test knowledge boundary with very low confidence"""
        result = agent.check_knowledge_boundary("test query", confidence=0.15)
        
        assert result["within_boundary"] == False
        assert result["confidence_level"] == "unknown"
        assert "expert" in result["recommendation"].lower()
    
    def test_confidence_calibration_no_evidence(self, agent):
        """Test confidence calibration with no evidence"""
        confidence = agent.calibrate_confidence(evidence_count=0)
        assert confidence == 0.0
    
    def test_confidence_calibration_with_evidence(self, agent):
        """Test confidence calibration with evidence"""
        # Single evidence piece
        confidence1 = agent.calibrate_confidence(evidence_count=1, evidence_quality=0.8)
        
        # Multiple evidence pieces
        confidence5 = agent.calibrate_confidence(evidence_count=5, evidence_quality=0.8)
        
        # More evidence should yield higher confidence
        assert confidence5 > confidence1
        
        # But should be capped at 0.99
        confidence_max = agent.calibrate_confidence(evidence_count=100, evidence_quality=1.0)
        assert confidence_max <= 0.99
    
    def test_confidence_calibration_quality_impact(self, agent):
        """Test that evidence quality affects confidence"""
        confidence_high_quality = agent.calibrate_confidence(evidence_count=5, evidence_quality=0.9)
        confidence_low_quality = agent.calibrate_confidence(evidence_count=5, evidence_quality=0.3)
        
        assert confidence_high_quality > confidence_low_quality
    
    @pytest.mark.asyncio
    async def test_reflection_without_issues(self, agent):
        """Test reflection with high-quality reasoning"""
        thought = "High confidence conclusion"
        reasoning_steps = [
            {"confidence": 0.95, "conclusion": "Step 1"},
            {"confidence": 0.92, "conclusion": "Step 2"}
        ]
        
        result = await agent.reflect(thought, reasoning_steps)
        
        # Should have no issues with high confidence
        assert len(result["issues"]) == 0
        assert result["confidence"] > 0.8
