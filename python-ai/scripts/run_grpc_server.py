#!/usr/bin/env python3
"""
Script to run the Lucie gRPC server standalone.
This can be used for development or for running the gRPC server separately from the API.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path to allow importing from other modules
sys.path.append(str(Path(__file__).parent.parent))

from grpc.server import serve
from utils.logger import logger

if __name__ == "__main__":
    try:
        logger.info("Starting Lucie gRPC server...")
        asyncio.run(serve())
        logger.info("gRPC server stopped.")
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server due to keyboard interrupt...")
    except Exception as e:
        logger.error(f"Error running gRPC server: {str(e)}")
        sys.exit(1)
