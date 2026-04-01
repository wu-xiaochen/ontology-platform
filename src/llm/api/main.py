import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

from core.reasoner import Reasoner
from memory.base import SemanticMemory, EpisodicMemory
from agents.orchestrator import CognitiveOrchestrator

logger = logging.getLogger(__name__)

# Global instances for the API lifespan
reasoner = Reasoner()
semantic_mem = SemanticMemory()
episodic_mem = EpisodicMemory(db_path="data/api_episodic.db")
orchestrator = CognitiveOrchestrator(reasoner, semantic_mem, episodic_mem)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for FastAPI"""
    logger.info("Initializing Clawra Cognitive API...")
    semantic_mem.connect()
    yield
    logger.info("Clawra API shutdown")

app = FastAPI(
    title="Clawra API", 
    version="1.0.0", 
    description="Enterprise REST API for Clawra Cognitive Framework (Ingestion & Reasoning).",
    lifespan=lifespan
)

class UserInput(BaseModel):
    text: str

class ClawraResponse(BaseModel):
    intent: str
    status: str
    message: str
    facts: list = []

@app.get("/")
def read_root():
    return {"message": "Clawra API is running.", "version": "1.0.0"}

@app.post("/interact", response_model=ClawraResponse)
async def interact_with_clawra(user_input: UserInput):
    """
    统一入口点 (Unified Interactions API).
    自动分析是将文本路由至 Knowledge Extractor (知识录入) 还是 Metacognitive Agent (逻辑问答).
    """
    try:
        result = await orchestrator.execute_task(user_input.text)
        return ClawraResponse(**result)
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
