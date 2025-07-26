"""Factory for creating embedding model instances.

This module provides the EmbeddingFactory class for registering and instantiating
embedding models from various providers such as Google, OpenAI, and Anthropic.
"""

from typing import Any


class EmbeddingFactory:
    """Factory class for registering and creating embedding model instances.

    This class allows registration of embedding model classes under a specific name
    and provides a method to instantiate them with given parameters.
    """
    _registry = {}

    @classmethod
    def register(cls, name: str):
        """Register an embedding model class under a specific name.

        Args:
            name (str): The name to register the embedding model class under.

        Returns:
            Callable: A decorator that registers the embedding model class.
        """
        def inner(embedding_class):
            cls._registry[name] = embedding_class
            return embedding_class
        return inner

    @classmethod
    def create(cls, model_provider: str, **kwargs) -> Any:
        """Create an instance of a registered embedding model.

        Args:
            model_provider (str): The name of the registered embedding model to instantiate.
            **kwargs: Additional keyword arguments to pass to the embedding model constructor.

        Returns:
            Any: An instance of the requested embedding model.

        Raises:
            ValueError: If the specified model_provider is not registered.
        """
        if model_provider not in cls._registry:
            raise ValueError(f"Embedding model '{model_provider}' is not registered.")
        embedding_class = cls._registry[model_provider]
        return embedding_class(**kwargs)