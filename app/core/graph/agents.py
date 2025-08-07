"""This file contains the definitions of agents for the multi-agent graph."""
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor.handoff import create_forward_message_tool

from app.core.config import settings
from app.core.prompts import PLANT_CARE_AGENT_PROMPT
from app.core.rag.rag_interface import RagInterface
from app.core.tools import (
    KnowledgeBaseTool,
    npk_calculator_tool,
    ph_calculator_tool,
)


def create_plant_expert_agent():
    """Create and return a plant expert agent with a toolkit."""
    rag = RagInterface()
    knowledge_base_tool = KnowledgeBaseTool(rag_system=rag)
    
    return create_react_agent(
        model=settings.AGENT_PLANT_LLM_MODEL,
        tools=[npk_calculator_tool, ph_calculator_tool, knowledge_base_tool],
        name="plant_expert_agent",
        prompt=PLANT_CARE_AGENT_PROMPT
    )

forwarding_tool = create_forward_message_tool("chat")