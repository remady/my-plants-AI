"""Module containing LLM chat callbacks."""

import time
from typing import Any, Dict, Optional
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler, CallbackManagerForToolRun, UsageMetadataCallbackHandler

from app.core.logging import logger
from app.core.metrics import (
    llm_input_tokens_used,
    llm_output_tokens_used,
    llm_response_duration,
    llm_tool_call_duration_seconds,
    llm_tool_calls,
    llm_total_cost,
    llm_total_tokens_used,
)


class TokensUsageCallback(UsageMetadataCallbackHandler):
    """Callback handler for tracking and logging LLM token usage, cost, and response metrics."""

    def __init__(self, session_id: str = None, model: str = None):
        """Initialize the TokensUsageCallback.

        Args:
            session_id (Optional[str]): The session identifier for tracking metrics.
            model (Optional[str]): LLM model name
        """
        super().__init__()
        self.session_id = session_id
        self.model = model
        self.start_time = None

    def on_llm_start(self, serialized: Dict[str, Any], prompts: list, **kwargs) -> None:
        """Called when the LLM process starts; records the start time for response duration metrics.

        Args:
            serialized (Dict[str, Any]): Serialized LLM configuration.
            prompts (list): List of prompts sent to the LLM.
            **kwargs: Additional keyword arguments.
        """
        super().on_llm_start(serialized, prompts, **kwargs)
        self.start_time = time.perf_counter()

    def on_llm_end(self, response, **kwargs) -> None:
        """Called when the LLM process ends; extracts usage metadata, logs metrics, and updates cost and token gauges.

        Args:
            response: The response object returned by the LLM.
            **kwargs: Additional keyword arguments.

        Raises:
            Exception: Logs any exception that occurs during metric extraction or logging.
        """
        super().on_llm_end(response, **kwargs)
        try:
            if self.usage_metadata:
                logger.info("usage_metadata", usage_metadata=self.usage_metadata)
                session_label = self.session_id or "unknown"
                usage_metadata = self.usage_metadata[self.model]
                input_tokens = usage_metadata.get("input_tokens", 0)
                output_tokens = usage_metadata.get("output_tokens", 0)
                total_tokens = usage_metadata.get("total_tokens", input_tokens + output_tokens)
                llm_input_tokens_used.labels(session_id=session_label, model=self.model).inc(input_tokens)
                llm_output_tokens_used.labels(session_id=session_label, model=self.model).inc(output_tokens)
                llm_total_tokens_used.labels(session_id=session_label, model=self.model).inc(total_tokens)

                cost = self._calculate_cost(self.model, input_tokens, output_tokens)
                if cost > 0:
                    llm_total_cost.labels(session_id=session_label, model=self.model).inc(cost)

        except Exception as e:
            logger.error("error_get_usage_metadata", session_id=self.session_id, error=str(e))

    def _calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        # TODO move it to utils, update with real data in the future versions
        pricing = {
            "gemini-2.5-flash": {"input": 0.00015, "output": 0.00060},
            "gemini-2.5-pro": {"input": 0.00125, "output": 0.01500},
            "gpt-4.1": {"input": 0.002, "output": 0.008},
            "gpt-4.5": {"input": 0.075, "output": 0.150},
            "gpt-o3": {"input": 0.00110, "output": 0.00440},
            "claude-4-sonnet": {"input": 0.00300, "output": 0.01500},
            "claude-4-opus": {"input": 0.01500, "output": 0.07500},
        }

        model_pricing = None
        for model_key in pricing:
            if model_key in model_name.lower():
                model_pricing = pricing[model_key]
                break

        if not model_pricing:
            return 0.0

        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]

        return input_cost + output_cost


class ToolRunCallback(AsyncCallbackHandler):
    """Asynchronous callback handler for tracking tool run events such as start, end, and errors."""

    def __init__(self, session_id: str = None, model: str = None):
        """Initialize the callback handler.

        Args:
            session_id: The session ID for the conversation.
            model: The model used for the conversation.
        """
        super().__init__()
        self.tool_start_time: int = None
        self.session_id: str = session_id
        self.tool_name: str = None
        self.model: str = None

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Run when a tool starts.

        Args:
            serialized (dict[str, Any]): Serialized tool configuration.
            input_str (str): The input string to the tool.
            **kwargs: Additional keyword arguments.
        """
        self.tool_start_time = time.perf_counter()
        await super().on_tool_start(serialized=serialized, input_str=input_str, **kwargs)

        self.tool_name = serialized.get("name", "unknown")
        logger.info("tool_call_start", session_id=self.session_id, input_str=input_str, tool_name=self.tool_name)
        llm_tool_calls.labels(tool_name=self.tool_name, session_id=self.session_id, model=self.model).inc()

    async def on_tool_end(
        self,
        output: Any,
        **kwargs: Any,
    ) -> None:
        """Run when a tool ends.

        Args:
            output (Any): The output returned by the tool.
            **kwargs (Any): Additional keyword arguments.
        """
        await super().on_tool_end(output=output, **kwargs)
        logger.info("tool_call_end", output=output[:50] + "...", tool_name=self.tool_name, session_id=self.session_id)
        llm_tool_call_duration_seconds.labels(tool_name=self.tool_name, session_id=self.session_id, model=self.model).observe(
            time.perf_counter() - self.tool_start_time
        )

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when tool errors.

        Args:
            error (BaseException): The error that occurred.
            run_id (UUID): The run ID. This is the ID of the current run.
            parent_run_id (UUID): The parent run ID. This is the ID of the parent run.
            tags (Optional[list[str]]): The tags.
            kwargs (Any): Additional keyword arguments.
        """
        await super().on_tool_error(error=error, run_id=run_id, parent_run_id=parent_run_id, tags=tags, kwargs=kwargs)
        logger.error("tool_call_error", error=str(error), exc_info=True)
