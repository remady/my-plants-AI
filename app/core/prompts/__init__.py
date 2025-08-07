"""This file contains the prompts for the agent."""

from datetime import datetime
from pathlib import Path

from app.core.config import settings

_current = Path(__file__).parent.absolute()


def load_prompt_by_name(name: str, format_schema: dict = None):
    """Load a prompt file by name and format its contents with the provided schema.

    Parameters
    ----------
    name : str
        The name of the prompt file
    format_schema : dict, optional
        Dictionary to format the prompt content.

    Returns:
    -------
    str
        The formatted prompt content as a string.
    """
    if not name.endswith(".md"):
        name += ".md"
    with open(_current / name, "r") as f:
        contents = f.read()
        if format_schema is not None:
            return contents.format(**format_schema)
        return contents
        

SYSTEM_PROMPT = load_prompt_by_name(
    "system", 
    format_schema=dict(
        agent_name=settings.PROJECT_NAME + " Agent",
        current_date_and_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))
SUPERVISOR_PROMPT = load_prompt_by_name("supervisor")
PLANT_CARE_AGENT_PROMPT = load_prompt_by_name("plant_care_agent")

