"""API v1 router configuration.

This module sets up the main API router and includes all sub-routers for different
endpoints like authentication and chatbot functionality.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chatbot import router as chatbot_router
from app.api.v1.documents import router as document_router
from app.api.v1.testing import router as testing_router
from app.core.logging import logger
from app.core.config import (
    Environment,
    settings,
)

api_router = APIRouter()

# Include routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chatbot_router, prefix="/chatbot", tags=["chatbot"])
api_router.include_router(document_router, prefix="/documents", tags=["documents"])

if settings.ENVIRONMENT in (Environment.DEVELOPMENT, Environment.TEST):
    api_router.include_router(testing_router, prefix="/testing", tags=["testing"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        dict: Health status information.
    """
    logger.info("health_check_called")
    return {"status": "healthy", "version": settings.VERSION}
