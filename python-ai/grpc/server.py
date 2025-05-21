import grpc
from concurrent import futures
import time
from typing import Any, Dict, List
import json

from utils.logger import logger
from utils.config import settings
from utils.metrics import track_api_metrics

# Import generated protobuf files
# Note: These imports will be available after running the protobuf compiler
try:
    # Try relative import first
    from .protos import lucie_pb2, lucie_pb2_grpc
except ImportError:
    try:
        # Try absolute import as fallback
        from grpc.protos import lucie_pb2, lucie_pb2_grpc
    except ImportError:
        logger.warning(
            "Protobuf files not found. Please run the protobuf compiler first."
        )
        logger.info(
            "Run 'cd /app && ./scripts/generate_protos.sh' to generate protobuf files"
        )
        raise


class LucieService(lucie_pb2_grpc.LucieServiceServicer):
    """Implementation of the Lucie gRPC service."""

    def __init__(self):
        """Initialize the service."""
        self.active_conversations: Dict[str, Any] = {}

    async def ProcessMessage(
        self, request: lucie_pb2.Message, context: grpc.aio.ServicerContext
    ) -> lucie_pb2.Response:
        """
        Process an incoming message and generate a response.

        Args:
            request: The incoming message
            context: The gRPC context

        Returns:
            A response message
        """
        try:
            logger.info(f"Processing message: {request.content}")

            # TODO: Implement actual message processing logic
            # This is a placeholder implementation
            response = lucie_pb2.Response(
                content="Message received and processed",
                status=lucie_pb2.Status.SUCCESS,
            )

            return response

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return lucie_pb2.Response(content="", status=lucie_pb2.Status.ERROR)

    async def GetKnowledge(
        self, request: lucie_pb2.KnowledgeRequest, context: grpc.aio.ServicerContext
    ) -> lucie_pb2.KnowledgeResponse:
        """
        Retrieve knowledge from the knowledge base.

        Args:
            request: The knowledge request
            context: The gRPC context

        Returns:
            A knowledge response
        """
        try:
            logger.info(f"Retrieving knowledge for query: {request.query}")

            # TODO: Implement actual knowledge retrieval logic
            # This is a placeholder implementation
            response = lucie_pb2.KnowledgeResponse(
                content="Knowledge retrieved",
                confidence=0.95,
                sources=["source1", "source2"],
            )

            return response

        except Exception as e:
            logger.error(f"Error retrieving knowledge: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return lucie_pb2.KnowledgeResponse(content="", confidence=0.0, sources=[])


async def serve():
    """
    Start the gRPC server.
    """
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_send_message_length", 100 * 1024 * 1024),  # 100MB
            ("grpc.max_receive_message_length", 100 * 1024 * 1024),  # 100MB
        ],
    )

    # Add the service to the server
    lucie_pb2_grpc.add_LucieServiceServicer_to_server(LucieService(), server)

    # Add the port to the server
    server.add_insecure_port(settings.get_grpc_address())

    # Start the server
    await server.start()
    logger.info(f"gRPC server started on {settings.get_grpc_address()}")

    try:
        # Keep the server running
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        await server.stop(0)


if __name__ == "__main__":
    import asyncio

    asyncio.run(serve())
