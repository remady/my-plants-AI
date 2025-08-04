"""This file contains the definition for the plant search tool."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class QuerySchema(BaseModel):
    query: str = Field(..., description="Query to ask LLM to lookup for plant e.g. 'plant with short black leaves'") 

@tool
def search_plant_tool(query: QuerySchema) -> str:
    """Searches for a plant with the given query."""
    return "Tomato"
