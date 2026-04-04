#!/usr/bin/env python3
"""
Ontology Platform - Main Entry Point
本体推理与查询平台 - 主入口
"""

import uvicorn
from src.api import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
