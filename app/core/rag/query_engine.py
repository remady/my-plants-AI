from llama_index.core import get_response_synthesizer
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.schema import (
    QueryBundle,
)
from llama_index.llms.google_genai import GoogleGenAI

from app.core.config import settings
from app.core.logging import logger
from app.core.rag import MultiIndexManager

LOG_EVENT_NAME = "rag_query_engine"


class RAGQueryEngine:
    """Query engine for retrieving, reranking, and synthesizing responses from multiple RAG retrievers.

    This class manages the retrieval of relevant nodes using vector, keyword, and knowledge graph retrievers,
    reranks the results, synthesizes a response using an LLM, and attaches source metadata.
    """

    def __init__(self, index_manager: MultiIndexManager):
        """Initialize the RAGQueryEngine with retrievers, reranker, and response synthesizer.

        Parameters
        ----------
        index_manager : MultiIndexManager
            The manager providing access to all retrievers.
        """
        (
            self.vector_retriever, 
            self.keyword_retriever, 
            self.kg_retriever
        ) = index_manager.get_all_retrievers()
        
        self.reranker = SentenceTransformerRerank(
            top_n=settings.RERANK_TOP_N,
            model=settings.RAG_RERANK_MODEL
        )
        
        self.response_synthesizer = get_response_synthesizer(
            llm=GoogleGenAI(model_name="gemini-1.5-flash", api_key=settings.LLM_EVALUATION_API_KEY),
            response_mode="compact"
        )
        logger.debug("init_rag_query_engine_success")

    async def aquery(self, query_str: str):
        """Asynchronously queries all retrievers, reranks results, synthesizes a response, and adds source metadata.

        Parameters
        ----------
        query_str : str
            The input query string.

        Returns:
        -------
        Response
            The synthesized response object containing the answer and sources.
        """
        logger.debug("rag_query_received", query=query_str)
        query_bundle = QueryBundle(query_str=query_str)
        
        vector_nodes = await self.vector_retriever.aretrieve(query_bundle)
        keyword_nodes = await self.keyword_retriever.aretrieve(query_bundle)
        kg_nodes = await self.kg_retriever.aretrieve(query_bundle)
        
        all_nodes = vector_nodes + keyword_nodes + kg_nodes
        
        unique_nodes = {node.id_: node for node in all_nodes}
        combined_nodes = list(unique_nodes.values())
        
        logger.debug("rag_query_found_unique_nodes", num_nodes=len(combined_nodes))

        if not combined_nodes:
            logger.debug("raq_query_receive_failed", message="No any relevant nodes were found")
            
            from llama_index.core import Response
            return Response(response="Could not retrieve any information.")

        reranked_nodes = self.reranker.postprocess_nodes(
            combined_nodes,
            query_bundle=query_bundle
        )
        logger.debug("rag_query_nodes_after_rerank", num_nodes=len(reranked_nodes), nodes_scores=" ".join(node.score for node in reranked_nodes))
        response = await self.response_synthesizer.asynthesize(
            query=query_bundle,
            nodes=reranked_nodes
        )
        
        # Add sources
        if response.source_nodes:
            source_files = list(set([
                node.metadata.get('file_name', 'N/A') for node in response.source_nodes
            ]))
            response.metadata['sources'] = source_files
        logger.debug("rag_query_success")
        return response
