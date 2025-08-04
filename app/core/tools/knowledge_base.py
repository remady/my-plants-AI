"""Documents Retriever tool."""
from typing import Type

from asgiref.sync import async_to_sync
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.core.rag.rag_interface import RagInterface, RAGResponse


class KnowledgeSearchInput(BaseModel):
    """Input model for searching the plant knowledge database."""
    query: str = Field(description="Detailed search query to the plants knowledge database")

class KnowledgeBaseTool(BaseTool):
    """Tool for searching information in the plant knowledge base.
    
    Including plant care,
    fertilization schedules, common diseases and pests, soil and watering requirements,
    and seasonal tips from expert sources.
    """
    name: str = "search_knowledge_base"
    description: str = (
        "Use this tool to search information about plant care, fertilization schedules " \
        "common diseases and pests, soil and watering requirements, as well as seasonal " \
        "tips from gardening guides, agricultural manuals, and expert sources."
    )
    args_schema: Type[BaseModel] = KnowledgeSearchInput
    rag_system: RagInterface

    def _run(self, query: str):
        return async_to_sync(self._arun)(query)

    async def _arun(self, query: str) -> str:
        logger.debug("search_knowledge_base_tool", message="Knowledge base invoked", query=query)
        response: RAGResponse = await self.rag_system.search(query)
        
        if not response.sources:
            return f"Answer: {response.answer}\nSources: Not found in the knowledge base"
        
        sources_str = ", ".join(response.sources)
        return f"Answer: {response.answer}\nSources: {sources_str}"