"""This file contains the definition for the NPK calculator tool."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class QueryModel(BaseModel):
    """Model representing a query for the NPK calculator tool."""
    n: str = Field(..., description="amount of nitrogen in the solution")
    p: str = Field(..., description="amount of phosphorus in the solution")
    k: str = Field(..., description="amount of potassium in the solution")

@tool
def npk_calculator_tool(query: QueryModel) -> str:
    """Calculate and return the expected N-P-K ratio and EC value.

    Parameters
    ----------
    query : QueryModel
        The input query containing relevant information for the calculation.

    Returns:
    -------
    str
        A string describing the expected N-P-K ratio and EC value.
    """
    calculated = {"npk": "5-10-10", "ec": "1500"}
    print('-----', query)
    return f"N-P-K ratio is {query.n, query.p, query.k} with EC {calculated['ec']} ppm"
