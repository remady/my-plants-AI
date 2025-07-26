"""Initialize retriver embeddings."""

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings
from app.factories.embedding_factory import EmbeddingFactory


@EmbeddingFactory.register("google_genai")
class GoogleEmbeddings(GoogleGenerativeAIEmbeddings): #noqa D101
    def __init__(self, **kwargs):                     #noqa D107
        super().__init__(model=kwargs.get("model", "models/embedding-001"))

@EmbeddingFactory.register("openai")
class OpenAIEmbed(OpenAIEmbeddings):    #noqa D101
    def __init__(self, **kwargs):       #noqa D107
        super().__init__(model=kwargs.get("model", "text-embedding-3-small"))
        
        
embeddings = EmbeddingFactory.create(
    model_provider=settings.MODEL_PROVIDER,
    model=settings.EMBEDDINGS,
)