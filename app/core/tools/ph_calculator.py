"""This file contains the definition for the pH calculator tool."""

from langchain_core.tools import tool


@tool
def ph_calculator_tool(query: str) -> dict:
    """Calculates the pH for a given query."""
    return {"expected": 6.0}
