"""Deepeval evaluations LLMs module."""
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from deepeval.models.base_model import DeepEvalBaseLLM

from app.core.logging import logger


class DEGoogleGeminiAI(DeepEvalBaseLLM):
    """Class to implement Google AI for DeepEval."""
    def __init__(self, model: ChatGoogleGenerativeAI):
        """Initialize the GoogleGeminiAI instance with a ChatGoogleGenerativeAI model.

        Args:
            model (ChatGoogleGenerativeAI): The Google Generative AI model to use.
        """
        self.model = model
        self.model_name = model.model

    def load_model(self):
        """Loads a model, that will be responsible for scoring.

        Returns:
            A model object
        """
        logger.info("loading_model", model_name=self.model_name)
        return self.model

    def generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        """Runs the model to output LLM response.

        Returns:
            <BaseModel>.
        """
        logger.info("generating_evaluation_response", prompt=prompt)
        client = self.load_model()
        
        response = client.with_structured_output(schema=schema).invoke(input=[
            ("user", prompt)
        ])
        
        return response

    async def a_generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        """Runs the model to output LLM response.

        Returns:
            <BaseModel>.
        """
        logger.info("generating_a_evaluation_response", prompt=prompt)
        client = self.load_model()
        
        response = await client.with_structured_output(schema=schema).ainvoke(input=[
            ("user", prompt)
        ])
        
        return response

    def get_model_name(self) -> str:
        """Return current model's name."""
        return self.model_name
