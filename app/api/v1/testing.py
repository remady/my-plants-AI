"""Chatbot API endpoints for handling chat interactions.

This module provides endpoints for chat interactions, including regular chat,
streaming chat, message history management, and chat history clearing.
"""
import asyncio
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from agentevals.graph_trajectory.utils import aextract_langgraph_trajectory_from_thread

from app.api.v1.auth import get_current_session
from app.core.config import settings
from app.core.langgraph.graph import LangGraphAgent
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.session import Session
from app.schemas.chat import (
    ChatResponseDebug,
)


router = APIRouter()
agent = LangGraphAgent()
graph_lock = asyncio.Lock()

@router.get("/messages", response_model=ChatResponseDebug)
async def get_session_messages(
    request: Request,
    session: Session = Depends(get_current_session)
):
    """Get all messages for a session.

    Args:
        request: The FastAPI request object for rate limiting.
        session: The current session from the auth token.

    Returns:
        ChatResponseDebug: Messages in the session without filtering.

    Raises:
        HTTPException: If there's an error retrieving the messages.
    """
    logger.info(
            "chat_history_request_received",
            session_id=session.id,
        )
    try:
        messages = await agent.get_chat_history(session.id, debug=True)
        logger.info("chat_history_request_processed", session_id=session.id)
        return ChatResponseDebug(messages=messages)
    except Exception as e:
        logger.error("get_messages_failed", session_id=session.id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph-trajectory")
async def get_graph_trajectory(
    request: Request,
    session: Session = Depends(get_current_session)
):
    """Retrieve the graph trajectory for the current session.

    Args:
        request: The FastAPI request object.
        session: The current session from the auth token.

    Returns:
        The trajectory extracted from the LangGraph agent.

    Raises:
        HTTPException: If there's an error retrieving the trajectory.
    """
    logger.info(
        "graph_trajectory_request_received",
        session_id=session.id,
    )
    try:
        async with graph_lock:
            if request.app.state.graph is None:
                request.app.state.graph = await agent.create_graph()
                
        trajectory = await aextract_langgraph_trajectory_from_thread(
            request.app.state.graph, {"configurable": {"thread_id": session.id}}
        )
        logger.info("graph_trajectory_request_processed", session_id=session.id)
        return trajectory
    except Exception as e:
        logger.error("get_graph_trajectory_failed", session_id=session.id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))