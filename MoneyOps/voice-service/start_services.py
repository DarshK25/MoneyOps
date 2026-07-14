#!/usr/bin/env python
"""
Voice Service - Entry point
Runs the LiveKit agent worker with integrated health check server.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    from app.agent.entrypoint import main
    main()