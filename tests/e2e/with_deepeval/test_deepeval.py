"""Deepeval tests module."""

from itertools import chain
from pathlib import Path

import pytest
from deepeval import assert_test, log_hyperparameters
from deepeval.dataset import Golden
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    ConversationalGEval,
    ToxicityMetric,
)
from deepeval.test_case import ConversationalTestCase, LLMTestCase, TurnParams

import tests.data as test_data
from app.core.config import settings
from app.core.logging import logger
from app.schemas.chat import ChatRequest, Message
from tests.custom_metrics.deepeval_metrics import professionalism_metric
from tests.http_client_wrapper import HttpClientWrapper
from tests.utils import convert_chat_response_into_deepeval_turns, extract_rag_context

DATASET_SIMPLE_INTERACTIONS = "aqa-dataset-simple-interactions"
DATASET_RAG = "aqa-dataset-rag"


@log_hyperparameters
def hyperparameters():
    """Send LLM parameters to Conf. AI for better tracking."""
    return {
        "app version": settings.VERSION,
        "model": settings.LLM_MODEL,
        "temperature": settings.DEFAULT_LLM_TEMPERATURE,
        "embeddings": settings.EMBEDDINGS,
    }


@pytest.mark.anyio
@pytest.mark.smoke
@pytest.mark.parametrize("golden", test_data.load_deepeval_dataset(DATASET_SIMPLE_INTERACTIONS).goldens)
async def test_smoke(golden: Golden, evaluation_model, chat_session: HttpClientWrapper, clear_chat_history):
    """Checking simple interactions with the target LLM."""
    message = ChatRequest(messages=[Message(role="user", content=golden.input)])
    chat_response = await chat_session.chat(message)
    test_case = LLMTestCase(input=golden.input, actual_output=chat_response.messages[-1].content)
    assert_test(
        test_case=test_case,
        metrics=[
            ToxicityMetric(model=evaluation_model, threshold=0.2),
            AnswerRelevancyMetric(model=evaluation_model, threshold=0.9),
        ],
    )


@pytest.mark.anyio
@pytest.mark.smoke
@pytest.mark.parametrize("golden", test_data.load_deepeval_dataset(DATASET_RAG).goldens)
async def test_rag(golden: Golden, evaluation_model, chat_session: HttpClientWrapper, clear_chat_history):
    """Verify app retrieval capabilities."""
    retrieval_context_document = test_data.DOCUMENTS_DIR / "tomatoes_fert_plan.txt"
    await chat_session.upload_document(retrieval_context_document)
    message = ChatRequest(messages=[Message(role="user", content=golden.input)])
    await chat_session.chat(message)
    chat_response = await chat_session.list_chat_messages_debug()
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=chat_response.messages[-1].content,
        expected_output=golden.expected_output,
        retrieval_context=extract_rag_context(chat_response),
    )
    assert_test(
        test_case=test_case,
        metrics=[
            professionalism_metric(model=evaluation_model, threshold=0.9),
            ContextualPrecisionMetric(model=evaluation_model),
            ContextualRecallMetric(model=evaluation_model),
            ContextualRelevancyMetric(model=evaluation_model),
        ],
    )


@pytest.mark.anyio
@pytest.mark.parametrize("golden", test_data.load_deepeval_dataset(DATASET_RAG).goldens)
async def test_tool_calls_in_conversation(
    golden: Golden, evaluation_model, chat_session: HttpClientWrapper, clear_chat_history
):
    """Test that the assistant correctly calls specified tools during a conversation."""
    retrieval_context_document = test_data.DOCUMENTS_DIR / "tomatoes_fert_plan.txt"
    await chat_session.upload_document(retrieval_context_document)
    message = ChatRequest(messages=[Message(role="user", content=golden.input)])
    await chat_session.chat(message)
    chat_response = await chat_session.list_chat_messages_debug()
    test_case = ConversationalTestCase(
        scenario="User try to get an advice for his tomatoes plants.",
        expected_outcome="Specified tools being called",
        turns=convert_chat_response_into_deepeval_turns(chat_response),
    )
    # there is a deterministic (non LLM) similar deepeval metric ToolCorrectnessMetric
    metric = ConversationalGEval(
        name="Tools calls correctness",
        evaluation_params=[TurnParams.TOOLS_CALLED],
        evaluation_steps=[
            "Check that tool with name 'retrieve_plants_documents' was called during a conversation",
        ],
        model=evaluation_model,
        strict_mode=True,
    )
    assert_test(test_case, metrics=[metric])
