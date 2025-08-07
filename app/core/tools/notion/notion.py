"""Tool for the Notion API."""

import json
import warnings
from typing import Any, List, Literal, Optional, Type, Union

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from langchain_core.utils import get_from_dict_or_env, get_from_env
from notion_client import AsyncClient
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.logging import logger


class NotionApiWrapper(BaseModel):
    """A wrapper for the Notion API."""
    client: AsyncClient
    api_key: str = Field(..., description="Notion API key")
    
    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: dict) -> Any:
        """Validate that the environment is set up correctly."""
        api_key = get_from_dict_or_env(
            values, "notion_api_key", "NOTION_API_KEY"
        )
        values["api_key"] = api_key
        try:
            from notion_client import AsyncClient
        except ImportError:
            raise ImportError(
                "notion-client is not installed. "
                "Please install it with `pip install notion-client`"
            )
        client = AsyncClient(auth=api_key, logger=logger)
        values["client"] = client
        return values
    
    
    def get_or_create_database(self):
        """Get or create the Notion database."""
        self.client.databases.create()
        
    def create_new_page(self):
        """Create a new page in the Notion database."""
        self.get_or_create_database()
        self.client.pages.create()
        
    def run(self, mode: str, **kw: Any) -> str:
        """Run the tool.

        Args:
            mode: The mode to run the tool in.
            kw: Additional keyword arguments.

        Returns:
            The result of the tool run.
        """
        match mode:
            case "create_page":
                return 1
            case _:
                raise ValueError(f"Invalid {mode=} for Notion API Wrapper")
            

class NotionDocumentSchema(BaseModel):
    """The schema for a Notion document."""
    a: int = Field(description="first number")
    b: int = Field(description="second number")
    title: str = Field(..., description="Database title")
    


class NotionTool(BaseTool):
    """A tool for interacting with Notion."""
    
    name: str = "Notion App"
    description: str = "create / update your pages and databases on notion.so"
    args_schema: Optional[ArgsSchema] = NotionDocumentSchema
    api_wrapper: "NotionApiWrapper" = Field(default_factory=NotionApiWrapper)

    def _run(
        self, a: int, b: int, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> int:
        """Use the tool."""
        return a * b

    async def _arun(
        self,
        a: int,
        b: int,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> int:
        """Use the tool asynchronously."""
        # If the calculation is cheap, you can just delegate to the sync implementation
        # as shown below.
        # If the sync calculation is expensive, you should delete the entire _arun method.
        # LangChain will automatically provide a better implementation that will
        # kick off the task in a thread to make sure it doesn't block other async code.
        return self._run(a, b, run_manager=run_manager.get_sync())