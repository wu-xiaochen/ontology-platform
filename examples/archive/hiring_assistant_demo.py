#!/usr/bin/env python3
"""
AI Hiring Assistant Demo
=========================

Demonstrates clawra's confidence-aware reasoning for candidate assessment.

Features:
- Confidence-scored candidate evaluation
- Explicit reasoning traces
- Knowledge gap identification
- Actionable recommendations

Run:
    PYTHONPATH=src python examples/hiring_assistant_demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent ))

try:
    from ontology import Agent
    from src.ontology.confidence import ConfidenceLevel
except ImportError:
    print("❌ clawra not installed")
    print("\nInstall from source:")
    print("  pip install -e .")
    print("\nOr from PyPI:")
    print("  pip install clawra")
    sys.exit(1)


def create_hiring_agent() -> Agent:
    """Initialize hiring domain agent with ontology and rules."""
    
    agent = Agent(domain="hiring")
    
    # Load hiring ontology (or create inline)
    agent.learn_ontology({
        "types": {
            "Candidate": {
                "required": ["name", "skills", "years_experience"],
                "properties": {
                    "name": "string",
                    "skills": "list[string]",
                    "years_experience": "number",
                    "education_level": "string",  # bachelor, master, phd
                    "leadership_roles": "number",
                    "ml_experience": "boolean",
                    "career_gap_months": "number",
                    "github_portfolio": "boolean",
                    "references_count": "number"
                }
            },
            "JobRole": {
                "required": ["title", "required_skills", "experience_level"],
                "properties": {
                    "title": "string",
                    "required_skills": "list[string]",
                    "experience_level": "string",  # junior, mid, senior
                    "requires_ml": "boolean",
                    "requires_leadership": "boolean"
                }
            }
        }
    })
    
    # Add reasoning rules
    agent.add_rules([
        {
            "id": "experience_threshold",
            "name": "Minimum Experience Requirement",
            "condition": """
                Candidate.years_experience >= JobRole.min_experience
            """,
            "conclusion": "Meets minimum experience requirement",
            "confidence": 0.9,
            "description": "Checks if candidate has required years of experience"
        },
        {
            "id": "skill_match",
            "name": "Required Skills Match",
            "condition": """
                ALL(JobRole.required_skills) IN Candidate.skills
            """,
            "conclusion": "Has all required technical skills",
            "confidence": 0.85,
            "description": "Verifies candidate possesses all required skills"
        },
        {
            "id": "ml_requirement",
            "name": "ML Experience Check",
            "condition": """
                JobRole.requires_ml == True AND Candidate.ml_experience == False
            """,
            "conclusion": "Critical skill gap: missing ML experience",
            "confidence": 0.95,
            "description": "Flags missing ML experience for ML roles"
        },
        {
            "id": "leadership_check",
            "name": "Leadership Experience",
            "condition": """
                JobRole.requires_leadership == True AND Candidate.leadership_roles < 1
            """,
            "conclusion": "No leadership experience for role requiring it",
            "confidence": 0.9,
            "description": "Identifies lack of leadership for senior roles"
        },
        {
            "id": "career_gap_flag",
            "name": "Career Gap Analysis",
            "condition": """
                Candidate.career_gap_months > 6
            """,
            "conclusion": "Significant career gap identified - requires explanation",
            "confidence": 0.7,
            "description": "Flags extended career gaps for follow-up"
        },
        {
            "id": "portfolio_bonus",
            "name": "GitHub Portfolio Verification",
            "condition": """
                Candidate.github_portfolio == True AND Candidate.years_experience >= 2
            """,
            "conclusion": "Technical skills verified via public portfolio",
            "confidence": 0.8,
            "description": "Boosts confidence when code is publicly visible"
        },
        {
            "id": "reference_check",
            "name": "Reference Availability",
            "condition": """
                Candidate.references_count < 2
            """,
            "conclusion": "Insufficient references for verification",
            "confidence": 0.75,
            "description": "Flags candidates with limited references"
        },
        {
            "id": "overall_recommendation",
            "name": "Hiring Recommendation Logic",
            "condition": """
                (skill_match == True) AND 
                (experience_threshold == True) AND 
                (ml_requirement != triggered) AND
                (leadership_check != triggered) AND
                (career_gap_flag != triggered OR career_gap_explained == True)
            """,
            "conclusion": "RECOMMEND: Proceed to next interview round",
            "confidence": 0.85,
            "description": "Overall positive recommendation"
        }
    ])
    
    return agent


def assess_candidate(agent: Agent, candidate_data: dict, job_data: dict) -> dict:
    """
    Assess a candidate for a specific role.
    
    Returns structured assessment with confidence scores and reasoning.
    """
    
    # Learn candidate data
    agent.learn({
        "type": "Candidate",
        "id": candidate_data["id"],
        "properties": candidate_data["properties"]
    })
    
    # Learn job requirements
    agent.learn({
        "type": "JobRole",
        "id": job_data["id"],
        "properties": job_data["properties"]
    })
    
    # Get assessment
    query = f"Should we hire {candidate_data['properties']['name']} for {job_data['properties']['title']} role?"
    
    result = agent.ask(query)
    
    return {
        "candidate": candidate_data["properties"]["name"],
        "role": job_data["properties"]["title"],
        "recommendation": result.conclusion,
        "confidence": result.confidence,
        "confidence_level": result.confidence_level,  # CONFIRMED/ASSUMED/SPECULATIVE
        "reasoning_chain": result.reasoning_chain,
        "knowledge_gaps": result.knowledge_gaps,
        "next_steps": generate_next_steps(result)
    }


def generate_next_steps(assessment_result) -> list:
    """Generate actionable next steps based on assessment."""
    
    next_steps = []
    
    if assessment_result.confidence_level == ConfidenceLevel.SPECULATIVE:
        next_steps.append("⚠️ Low confidence - manual review required")
        next_steps.append("📞 Schedule phone screen to gather more information")
    
    if assessment_result.confidence_level == ConfidenceLevel.CONFIRMED:
        if "RECOMMEND" in assessment_result.conclusion:
            next_steps.append("✅ High confidence - proceed to technical interview")
            next_steps.append("📧 Send interview invitation")
        else:
            next_steps.append("❌ High confidence - do not proceed")
            next_steps.append("📧 Send polite rejection email")
    
    # Check for specific gaps
    for gap in assessment_result.knowledge_gaps:
        if "reference" in gap.lower():
            next_steps.append("📋 Request 2 professional references")
        if "career gap" in gap.lower():
            next_steps.append("❓ Ask about career gap during interview")
        if "technical" in gap.lower():
            next_steps.append("💻 Administer technical assessment")
    
    return next_steps


def render_assessment(assessment: dict) -> str:
    """Render assessment as human-readable report."""
    
    lines = []
    lines.append("=" * 70)
    lines.append(f"CANDIDATE ASSESSMENT: {assessment['candidate']}")
    lines.append(f"Role: {assessment['role']}")
    lines.append("=" * 70)
    lines.append("")
    
    # Overall recommendation
    rec = assessment["recommendation"]
    conf = assessment["confidence"]
    level = assessment["confidence_level"].name
    
    lines.append(f"📊 OVERALL RECOMMENDATION: {rec}")
    lines.append(f"   Confidence: {conf:.2f} ({level})")
    lines.append("")
    
    # Reasoning chain
    lines.append("🔍 REASONING CHAIN:")
    for i, step in enumerate(assessment["reasoning_chain"], 1):
        lines.append(f"   [{i}] {step}")
    lines.append("")
    
    # Knowledge gaps
    if assessment["knowledge_gaps"]:
        lines.append("⚠️  KNOWLEDGE GAPS:")
        for gap in assessment["knowledge_gaps"]:
            lines.append(f"   ? {gap}")
        lines.append("")
    
    # Next steps
    lines.append("📋 NEXT STEPS:")
    for step in assessment["next_steps"]:
        lines.append(f"   → {step}")
    lines.append("")
    
    lines.append("=" * 70)
    
    return "\n".join(lines)


def main():
    """Run hiring assistant demo with sample candidates."""
    
    print("\n" + "=" * 70)
    print("🤖 AI HIRING ASSISTANT DEMO")
    print("Powered by clawra")
    print("=" * 70 + "\n")
    
    # Initialize agent
    print("[1] Initializing hiring assistant...")
    agent = create_hiring_agent()
    print("    ✓ Agent loaded with hiring ontology and 8 reasoning rules\n")
    
    # Sample candidates
    candidates = [
        {
            "id": "candidate_001",
            "properties": {
                "name": "John Doe",
                "skills": ["Python", "Django", "PostgreSQL", "React"],
                "years_experience": 5,
                "education_level": "bachelor",
                "leadership_roles": 1,
                "ml_experience": False,
                "career_gap_months": 0,
                "github_portfolio": True,
                "references_count": 3
            }
        },
        {
            "id": "candidate_002",
            "properties": {
                "name": "Jane Smith",
                "skills": ["Python", "TensorFlow", "PyTorch", "SQL"],
                "years_experience": 3,
                "education_level": "master",
                "leadership_roles": 0,
                "ml_experience": True,
                "career_gap_months": 8,
                "github_portfolio": True,
                "references_count": 1
            }
        },
        {
            "id": "candidate_003",
            "properties": {
                "name": "Bob Johnson",
                "skills": ["Java", "Spring", "MySQL"],
                "years_experience": 2,
                "education_level": "bachelor",
                "leadership_roles": 0,
                "ml_experience": False,
                "career_gap_months": 0,
                "github_portfolio": False,
                "references_count": 2
            }
        }
    ]
    
    # Job roles
    roles = [
        {
            "id": "role_senior_ml",
            "properties": {
                "title": "Senior ML Engineer",
                "required_skills": ["Python", "TensorFlow", "PyTorch"],
                "experience_level": "senior",
                "min_experience": 4,
                "requires_ml": True,
                "requires_leadership": True
            }
        },
        {
            "id": "role_backend",
            "properties": {
                "title": "Backend Developer",
                "required_skills": ["Python", "Django", "PostgreSQL"],
                "experience_level": "mid",
                "min_experience": 3,
                "requires_ml": False,
                "requires_leadership": False
            }
        }
    ]
    
    # Run assessments
    print("[2] Running candidate assessments...\n")
    
    # Scenario 1: John Doe for Senior ML Engineer
    print("-" * 70)
    assessment = assess_candidate(agent, candidates[0], roles[0])
    print(render_assessment(assessment))
    
    # Scenario 2: Jane Smith for Senior ML Engineer
    print("-" * 70)
    assessment = assess_candidate(agent, candidates[1], roles[0])
    print(render_assessment(assessment))
    
    # Scenario 3: John Doe for Backend Developer
    print("-" * 70)
    assessment = assess_candidate(agent, candidates[0], roles[1])
    print(render_assessment(assessment))
    
    # Scenario 4: Bob Johnson for Backend Developer (mismatch example)
    print("-" * 70)
    assessment = assess_candidate(agent, candidates[2], roles[1])
    print(render_assessment(assessment))
    
    print("\n✅ Demo complete!")
    print("\nKey takeaways:")
    print("  • Every assessment includes confidence scores")
    print("  • Reasoning chains are fully transparent")
    print("  • Knowledge gaps are explicitly identified")
    print("  • Next steps are actionable and specific")
    print("\nThis is how you build agents that think before they speak. 🦞\n")


if __name__ == "__main__":
    main()
