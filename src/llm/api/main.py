import logging
import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from datetime import datetime

from ...core.reasoner import Reasoner, Fact, Rule, RuleType
from ...memory.base import SemanticMemory, EpisodicMemory
from ...agents.orchestrator import CognitiveOrchestrator
from ...core.ontology.rule_engine import RuleEngine, OntologyRule

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional API key verification"""
    if credentials is None:
        return None
    api_key = os.getenv("API_KEY")
    if api_key and credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials

# Global instances
reasoner = Reasoner()
semantic_mem = SemanticMemory()
episodic_mem = EpisodicMemory(db_path="data/api_episodic.db")
orchestrator = CognitiveOrchestrator(reasoner, semantic_mem, episodic_mem)
rule_engine = RuleEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for FastAPI"""
    logger.info("Initializing Clawra Cognitive API...")
    semantic_mem.connect()
    yield
    logger.info("Clawra API shutdown")

app = FastAPI(
    title="Clawra Cognitive Engine API",
    version="2.0.0",
    description="""
    Enterprise REST API for Clawra Neuro-Symbolic Cognitive Framework.
    
    **Features:**
    - Knowledge ingestion and retrieval
    - Ontology-based reasoning
    - Rule engine with conflict detection
    - Metacognitive capabilities
    - Knowledge boundary detection
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Request/Response Models ====================

class UserInput(BaseModel):
    text: str = Field(..., description="User input text")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

class FactInput(BaseModel):
    subject: str
    predicate: str
    object: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = Field(default="api_input")

class RuleInput(BaseModel):
    id: str
    target_object_class: str
    expression: str
    description: str
    version: str = "1.0.0"
    
class QueryInput(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, ge=1, le=20)
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

class ReasoningInput(BaseModel):
    max_depth: int = Field(default=10, ge=1, le=20)
    direction: str = Field(default="forward", pattern="^(forward|backward|bidirectional)$")

class ClawraResponse(BaseModel):
    intent: str
    status: str
    message: str
    facts: List[Dict[str, Any]] = []
    confidence: float = 0.0
    trace: List[Dict[str, Any]] = []

class KnowledgeStatus(BaseModel):
    total_facts: int
    total_rules: int
    graph_connected: bool
    vector_store_status: str
    uptime: str

class RuleEvaluationInput(BaseModel):
    rule_id: str
    context: Dict[str, float]
    
class RuleEvaluationResponse(BaseModel):
    rule_id: str
    status: str
    passed: bool
    expression: str
    context_used: Dict[str, float]
    message: str

# ==================== Health & Status Endpoints ====================

@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint with API information"""
    return {
        "name": "Clawra Cognitive Engine API",
        "version": "2.0.0",
        "description": "Neuro-Symbolic Cognitive Framework for Enterprise AI",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "reasoner": "active",
            "memory": "connected" if semantic_mem.is_connected else "local",
            "vector_store": "active"
        }
    }

@app.get("/status", response_model=KnowledgeStatus, tags=["Status"])
async def get_system_status(api_key: str = Depends(verify_api_key)):
    """Get comprehensive system status"""
    start_time = datetime.now()  # In production, track actual start time
    
    return KnowledgeStatus(
        total_facts=len(reasoner.facts),
        total_rules=len(rule_engine.rules),
        graph_connected=semantic_mem.is_connected,
        vector_store_status="active",
        uptime="N/A"  # Calculate from actual start time in production
    )

# ==================== Knowledge Management Endpoints ====================

@app.post("/knowledge/ingest", response_model=ClawraResponse, tags=["Knowledge"])
async def ingest_knowledge(user_input: UserInput, api_key: str = Depends(verify_api_key)):
    """
    Ingest knowledge from text
    
    Extracts facts from text and stores them in the knowledge base
    """
    try:
        result = await orchestrator.execute_task(
            [{"role": "user", "content": user_input.text}]
        )
        return ClawraResponse(**result)
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/facts", tags=["Knowledge"])
async def add_fact(fact_input: FactInput, api_key: str = Depends(verify_api_key)):
    """Add a single fact to the knowledge base"""
    try:
        fact = Fact(
            subject=fact_input.subject,
            predicate=fact_input.predicate,
            object=fact_input.object,
            confidence=fact_input.confidence,
            source=fact_input.source
        )
        reasoner.add_fact(fact)
        semantic_mem.store_fact(fact)
        
        return {
            "status": "success",
            "message": f"Fact added: {fact.subject} {fact.predicate} {fact.object}",
            "fact": fact_input.dict()
        }
    except Exception as e:
        logger.error(f"Fact addition error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/facts", tags=["Knowledge"])
async def list_facts(
    subject: Optional[str] = None,
    predicate: Optional[str] = None,
    object: Optional[str] = None,
    min_confidence: float = 0.0,
    limit: int = 100
):
    """List facts with optional filters"""
    facts = reasoner.query(
        subject=subject,
        predicate=predicate,
        obj=object,
        min_confidence=min_confidence
    )
    
    return {
        "count": len(facts[:limit]),
        "facts": [
            {
                "subject": f.subject,
                "predicate": f.predicate,
                "object": f.object,
                "confidence": f.confidence,
                "source": f.source
            }
            for f in facts[:limit]
        ]
    }

@app.delete("/knowledge/facts/clear", tags=["Knowledge"])
async def clear_facts(api_key: str = Depends(verify_api_key)):
    """Clear all facts from memory (use with caution)"""
    count = len(reasoner.facts)
    reasoner.clear_facts()
    return {"status": "success", "message": f"Cleared {count} facts"}

# ==================== Query & Reasoning Endpoints ====================

@app.post("/query", tags=["Query"])
async def query_knowledge(query_input: QueryInput, api_key: str = Depends(verify_api_key)):
    """
    Query knowledge base with semantic search
    
    Combines vector similarity search with graph traversal
    """
    try:
        # Vector search
        vector_results = semantic_mem.semantic_search(
            query_input.query, 
            top_k=query_input.top_k
        )
        
        # Fact query
        fact_results = reasoner.query(
            min_confidence=query_input.min_confidence
        )
        
        return {
            "query": query_input.query,
            "vector_results": [
                {"content": doc.content, "metadata": doc.metadata}
                for doc in vector_results
            ],
            "fact_count": len(fact_results),
            "total_results": len(vector_results)
        }
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reasoning/forward", tags=["Reasoning"])
async def forward_chain_reasoning(
    reasoning_input: ReasoningInput,
    api_key: str = Depends(verify_api_key)
):
    """Execute forward chain reasoning"""
    try:
        result = reasoner.forward_chain(
            max_depth=reasoning_input.max_depth
        )
        
        return {
            "conclusions_count": len(result.conclusions),
            "facts_used_count": len(result.facts_used),
            "depth": result.depth,
            "total_confidence": result.total_confidence.value,
            "conclusions": [
                {
                    "rule": step.rule.name,
                    "conclusion": f"{step.conclusion.subject} {step.conclusion.predicate} {step.conclusion.object}",
                    "confidence": step.confidence.value
                }
                for step in result.conclusions
            ]
        }
    except Exception as e:
        logger.error(f"Reasoning error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reasoning/backward", tags=["Reasoning"])
async def backward_chain_reasoning(
    goal: FactInput,
    max_depth: int = 10,
    api_key: str = Depends(verify_api_key)
):
    """Execute backward chain reasoning from a goal"""
    try:
        goal_fact = Fact(
            subject=goal.subject,
            predicate=goal.predicate,
            object=goal.object
        )
        
        result = reasoner.backward_chain(
            goal=goal_fact,
            max_depth=max_depth
        )
        
        return {
            "goal": f"{goal.subject} {goal.predicate} {goal.object}",
            "conclusions_count": len(result.conclusions),
            "total_confidence": result.total_confidence.value,
            "conclusions": [
                {
                    "conclusion": f"{step.conclusion.subject} {step.conclusion.predicate} {step.conclusion.object}",
                    "confidence": step.confidence.value
                }
                for step in result.conclusions
            ]
        }
    except Exception as e:
        logger.error(f"Backward reasoning error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reasoning/explain", tags=["Reasoning"])
async def explain_reasoning():
    """Get explanation of last reasoning process"""
    result = reasoner.forward_chain(max_depth=5)
    explanation = reasoner.explain(result)
    
    return {
        "explanation": explanation,
        "conclusions": len(result.conclusions),
        "confidence": result.total_confidence.value
    }

# ==================== Rule Management Endpoints ====================

@app.get("/rules", tags=["Rules"])
async def list_rules():
    """List all registered rules"""
    return {
        "count": len(rule_engine.rules),
        "rules": [rule.to_dict() for rule in rule_engine.rules.values()]
    }

@app.post("/rules", tags=["Rules"])
async def add_rule(rule_input: RuleInput, api_key: str = Depends(verify_api_key)):
    """Add a new rule to the rule engine"""
    try:
        rule = OntologyRule(
            id=rule_input.id,
            target_object_class=rule_input.target_object_class,
            expression=rule_input.expression,
            description=rule_input.description,
            version=rule_input.version
        )
        
        result = rule_engine.register_rule(rule, check_conflict=True)
        
        return {
            "status": result["status"],
            "rule_id": rule.id,
            "warnings": result.get("warnings", [])
        }
    except Exception as e:
        logger.error(f"Rule addition error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rules/evaluate", response_model=RuleEvaluationResponse, tags=["Rules"])
async def evaluate_rule(
    eval_input: RuleEvaluationInput,
    api_key: str = Depends(verify_api_key)
):
    """Evaluate a rule with given context"""
    try:
        result = rule_engine.evaluate_rule(eval_input.rule_id, eval_input.context)
        
        return RuleEvaluationResponse(
            rule_id=eval_input.rule_id,
            status=result.get("status", "ERROR"),
            passed=result.get("status") == "PASS",
            expression=result.get("expression", ""),
            context_used=result.get("context_used", {}),
            message=result.get("rule_name", result.get("msg", ""))
        )
    except Exception as e:
        logger.error(f"Rule evaluation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rules/object/{object_class}", tags=["Rules"])
async def get_rules_for_object(object_class: str):
    """Get all rules for a specific object class"""
    rules = rule_engine.get_rules_for_object(object_class)
    return {
        "object_class": object_class,
        "count": len(rules),
        "rules": [rule.to_dict() for rule in rules]
    }

# ==================== Interactive Endpoint ====================

@app.post("/interact", response_model=ClawraResponse, tags=["Interactive"])
async def interact_with_clawra(user_input: UserInput, api_key: str = Depends(verify_api_key)):
    """
    Unified interaction endpoint
    
    Automatically routes text to knowledge extraction or metacognitive agent
    """
    try:
        result = await orchestrator.execute_task(
            [{"role": "user", "content": user_input.text}],
            custom_prompt=user_input.context.get("prompt") if user_input.context else None
        )
        return ClawraResponse(**result)
    except Exception as e:
        logger.error(f"Interaction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Episode & Learning Endpoints ====================

@app.get("/episodes", tags=["Learning"])
async def list_episodes(limit: int = 10):
    """List recent episodes from episodic memory"""
    episodes = episodic_mem.retrieve_episodes(limit=limit)
    return {
        "count": len(episodes),
        "episodes": episodes
    }

@app.post("/episodes/feedback", tags=["Learning"])
async def add_feedback(
    task_id: str,
    reward: float,
    correction: str = "",
    api_key: str = Depends(verify_api_key)
):
    """Add RLHF feedback for an episode"""
    try:
        episodic_mem.add_human_feedback(task_id, reward, correction)
        return {
            "status": "success",
            "message": f"Feedback recorded for task {task_id}"
        }
    except Exception as e:
        logger.error(f"Feedback error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
