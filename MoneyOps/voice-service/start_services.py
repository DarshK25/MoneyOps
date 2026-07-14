#!/usr/bin/env python
"""
Voice Service - Unified startup script
Runs both FastAPI health API and LiveKit Agent worker
"""
import asyncio
import multiprocessing
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def run_health_api():
    """Run FastAPI health check server on port 8003"""
    import uvicorn
    from app.api.health import app
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")


def run_agent_worker():
    """Run LiveKit agent worker"""
    from app.agent.entrypoint import main as agent_main
    # The agent entrypoint uses cli.run_app which handles the worker
    import asyncio
    asyncio.run(agent_main())


if __name__ == "__main__":
    # Run health API in a separate process
    health_process = multiprocessing.Process(target=run_health_api, daemon=True)
    health_process.start()
    
    # Run agent worker in main process
    try:
        run_agent_worker()
    except KeyboardInterrupt:
        pass
    finally:
        health_process.terminate()
        health_process.join(timeout=5)