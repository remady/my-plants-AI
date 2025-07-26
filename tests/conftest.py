"""Pytest configuration and fixtures for testing the RAG agent application.

This module sets up test fixtures for HTTP clients, LangSmith integration, and user/session management.
"""
import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.core.logging import logger
from app.models.user import User
from app.services.database import database_service
from tests.http_client_wrapper import HttpClientWrapper


def pytest_addoption(parser):
    """Added custom commandline parameters."""
    parser.addoption(
        "--use-shared-datasets",
        action="store_true",
        help="Use goldens saved on Confident AI"
    )
    parser.addoption(
        "--upload-datasets",
        action="store_true",
        help="Upload goldens dataset to Confident AI"
    )

@pytest.fixture(scope="session")
def event_loop():  # noqa D103
    return asyncio.get_event_loop()


@pytest.fixture(scope="session")
def anyio_backend():  # noqa D103
    return "asyncio"


@pytest.fixture(scope="module")
def judge_llm():
    """Fixture to provide an AI chat model for judging/evaluation."""
    # I recommend to use smarter models like gemini pro, openai o3 or claude opus for the actual testing
    return ChatGoogleGenerativeAI(
        model=settings.LLM_EVALUATION_MODEL, 
        google_api_key=settings.EVALUATION_API_KEY,
        temperature=0
    )


@pytest.fixture(scope="session")
async def user() -> dict[str, str]:
    """Fixture to provide a test user from the database, creating one if necessary."""
    email = settings.TEST_USER_EMAIL
    password = settings.TEST_USER_PASSWORD
    user = await database_service.get_user_by_email(email=email)
    if not user:
        await database_service.create_user(email=email, password=User.hash_password(password))
    return {"email": email, "password": password}


@pytest.fixture(scope="session")
async def chat_session(user) -> AsyncGenerator[HttpClientWrapper, None]:
    """Fixture to provide an asynchronous HTTP client for testing."""
    client = HttpClientWrapper(session=AsyncClient(timeout=30), base_url=f"{settings.TEST_APP_HOST}{settings.API_V1_STR}")
    await client.create_chat_session(username=user["email"], password=user["password"])
    yield client
    await client.close()


@pytest.fixture()
async def clear_chat_history(chat_session: HttpClientWrapper):
    """Fixture to clear chat session history after the test."""
    yield
    await chat_session.delete_chat_messages()
