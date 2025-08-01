"""This file contains the prompts for the agent."""

from pathlib import Path
from datetime import datetime

from app.core.config import settings


def load_system_prompt():
    """Load the system prompt from the file."""
    with open(Path(__file__).parent.absolute() / "system.md", "r") as f:
        return f.read().format(
            agent_name=settings.PROJECT_NAME + " Agent",
            current_date_and_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

SYSTEM_PROMPT = load_system_prompt()
