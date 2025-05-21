#!/usr/bin/env python3
"""
Main entry point for the Lucie Python AI service.
This script starts both the FastAPI and gRPC servers.
"""

import os
import asyncio
import uvicorn
import threading
import signal
import time
from pathlib import Path

# Add the current directory to the Python path
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger
from utils.config import settings

# Global flag to track when servers should shut down
should_shutdown = False


def start_fastapi_server():
    """Start the FastAPI server"""
    logger.info("Starting FastAPI server...")
    port = int(os.getenv("API_PORT", settings.API_PORT))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


async def start_grpc_server():
    """Start the gRPC server"""
    logger.info("Starting gRPC server...")
    try:
        from grpc.server import serve

        await serve()
    except Exception as e:
        logger.error(f"Failed to start gRPC server: {str(e)}")
        raise


def signal_handler(sig, frame):
    """Handle termination signals"""
    global should_shutdown
    logger.info(f"Received signal {sig}, initiating shutdown...")
    should_shutdown = True


def main():
    """Main entry point"""
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Lucie Python AI service...")
    logger.info(f"FastAPI will run on port {settings.API_PORT}")
    logger.info(f"gRPC will run on {settings.get_grpc_address()}")

    # Start FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=start_fastapi_server, daemon=True)
    fastapi_thread.start()

    # Start gRPC server in the main thread using asyncio
    try:
        asyncio.run(start_grpc_server())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        # Wait for FastAPI to shut down gracefully
        if fastapi_thread.is_alive():
            logger.info("Waiting for FastAPI server to shut down...")
            # Join the thread with a timeout instead of just sleeping
            fastapi_thread.join(timeout=5)

        logger.info("Lucie Python AI service stopped")


if __name__ == "__main__":
    main()
