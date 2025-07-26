"""Custom metrics for evaluating LLM responses using DeepEval.

Defines a partial GEval metrics with specific evaluation steps and rubric.
"""

from functools import partial

from deepeval.metrics import GEval
from deepeval.metrics.g_eval import Rubric
from deepeval.test_case import LLMTestCaseParams

professionalism_metric = partial(
    GEval,
    name="Professionalism",
    evaluation_steps=[
        "Evaluate whether responses maintain a respectful, courteous tone.",
        "Look for absence of casual slang, inappropriate humor, or overly familiar language",
        "Review grammar, spelling, and punctuation accuracy",
        "Assess vocabulary appropriateness for professional settings",
        "Evaluate sentence structure and coherence",
        "Verify the model maintains appropriate professional boundaries",
        "Assess cultural sensitivity in communication",
        "Assess ability to redirect inappropriate conversations professionally"
    ],
    rubric=[
        Rubric(score_range=(0,2), expected_outcome="Unprofessional tone, inappropriate language, poor grammar."),
        Rubric(score_range=(3,6), expected_outcome="Generally professional but with some lapses in tone or minor errors."),
        Rubric(score_range=(7,9), expected_outcome="Professional and appropriate with minor room for improvement."),
        Rubric(score_range=(10,10), expected_outcome="Perfectly professional, respectful, and well-structured."),
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
)

