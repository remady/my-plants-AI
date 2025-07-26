"""Documents Retriever tool."""
from langchain.tools.retriever import create_retriever_tool

from app.core.vectorstore import vector_store

retriever_tool = create_retriever_tool(
    vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4}),
    "retrieve_plants_documents",
    "Search for information about plant care, fertilization schedules " \
    "common diseases and pests, soil and watering requirements, as well as seasonal " \
    "tips from gardening guides, agricultural manuals, and expert sources."
)