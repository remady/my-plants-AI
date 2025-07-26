"""Deepeval module level fixtures and hooks."""
import pytest

from tests.evaluation_llm import DEGoogleGeminiAI


@pytest.fixture(scope="module")
def evaluation_model(judge_llm):
    """Fixture that returns an instance of DEGoogleGeminiAI initialized with the provided judge_llm.
    
    Parameters
    ----------
    judge_llm : object
        The LLM instance to be used for evaluation.

    Returns:
    -------
    DEGoogleGeminiAI
        An instance of DEGoogleGeminiAI.
    """
    return DEGoogleGeminiAI(judge_llm)