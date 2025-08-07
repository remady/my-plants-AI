import os
import sys
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import chromadb
from llama_index.core import (
    KnowledgeGraphIndex,
    Settings,
    SimpleKeywordTableIndex,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import BaseNode
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

from app.core.config import settings
from app.core.logging import logger


class MultiIndexManager:
    """Manages the creation, loading, and interaction with multiple indices.
    
    - VectorStoreIndex for semantic search.
    - SimpleKeywordTableIndex for keyword-based search.
    - KnowledgeGraphIndex for entity and relationship-based search.
    """

    def __init__(self):
        """Initializes the MultiIndexManager.

        This involves setting up global LLM and embedding models, configuring
        the storage backend (ChromaDB), and loading or creating the indices.
        """
        print("Initializing MultiIndexManager...")
        logger.debug("initializing_multi_index_manager")

        # 1. Configure global LLM and Embedding settings
        Settings.llm = GoogleGenAI(
            model_name=settings.RAG_INDEX_MANAGER_LLM_MODEL, 
            api_key=settings.RAG_INDEX_MANAGER_LLM_API_KEY
        )
        Settings.embed_model = GoogleGenAIEmbedding(
            model_name=settings.RAG_INDEX_MANAGER_EMBEDDINGS, 
            api_key=settings.RAG_INDEX_MANAGER_EMBEDDINGS_API_KEY
        )
        Settings.chunk_size = settings.CHUNK_SIZE
        Settings.chunk_overlap = settings.CHUNK_OVERLAP

        # 2. Configure storage
        # Create a persistent ChromaDB client that stores data in the specified directory.
        db = chromadb.PersistentClient(path=settings.PERSIST_DIR)
        chroma_collection = db.get_or_create_collection("main_collection")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        # 3. Load or create indices
        # Different index types will be stored in dedicated subdirectories.
        self.storage_context = StorageContext.from_defaults(vector_store=vector_store)
        self.keyword_storage_path = os.path.join(
            settings.PERSIST_DIR, "keyword_index"
        )
        self.kg_storage_path = os.path.join(settings.PERSIST_DIR, "kg_index")

        self._load_or_create_indexes()
        logger.debug("initializing_multi_index_manager_success")

    def _load_or_create_indexes(self):
        """Loads indices from storage if they exist, otherwise creates new ones."""
        try:
            # The VectorStoreIndex is loaded automatically via the StorageContext and Chroma.
            self.vector_index = VectorStoreIndex.from_vector_store(
                self.storage_context.vector_store
            )
            self.keyword_index = SimpleKeywordTableIndex.from_storage(
                StorageContext.from_defaults(persist_dir=self.keyword_storage_path)
            )
            self.kg_index = KnowledgeGraphIndex.from_storage(
                StorageContext.from_defaults(persist_dir=self.kg_storage_path)
            )
        except Exception:
            print("Failed to load indices. Creating new ones...")
            # If loading fails (e.g., on the first run), create empty indices.
            self.vector_index = VectorStoreIndex.from_documents(
                [], storage_context=self.storage_context
            )
            self.keyword_index = SimpleKeywordTableIndex.from_documents(
                [], storage_context=StorageContext.from_defaults()
            )
            self.kg_index = KnowledgeGraphIndex.from_documents(
                [], storage_context=StorageContext.from_defaults()
            )

            # Persist the "empty" indices to create the folder structure.
            self.keyword_index.storage_context.persist(
                persist_dir=self.keyword_storage_path
            )
            self.kg_index.storage_context.persist(persist_dir=self.kg_storage_path)

    def add_document(self, nodes: List[BaseNode]):
        """Adds processed document nodes to all three indices.

        Args:
            nodes (List[BaseNode]): A list of nodes to be added to the indices.
        """
        print(f"Adding {len(nodes)} nodes to indices...")
        # Insert nodes into each index
        for node in nodes:
            self.vector_index.insert_nodes([node])
            self.keyword_index.insert_nodes([node])
            self.kg_index.insert_nodes([node])

        # Persist changes for indices that are not saved automatically.
        print("Persisting keyword and kg indices...")
        self.keyword_index.storage_context.persist(
            persist_dir=self.keyword_storage_path
        )
        self.kg_index.storage_context.persist(persist_dir=self.kg_storage_path)
        print("Nodes added and persisted successfully.")

    async def delete_document(self, doc_id: str):
        """Deletes a document and its associated nodes from all indices.

        Note: Deletion from the KnowledgeGraphIndex is currently commented out
            as it might require a more complex update strategy.

        Args:
            doc_id (str): The unique identifier of the document to be deleted.
        """
        print(f"Deleting document with doc_id='{doc_id}' from all indices...")
        # Use the built-in method to delete by document ID.
        await self.vector_index.adelete_ref_doc(doc_id, delete_from_docstore=True)
        await self.keyword_index.adelete_ref_doc(doc_id, delete_from_docstore=True)
        # self.kg_index.delete_ref_doc(doc_id, delete_from_docstore=True)

        # Persist the changes.
        self.keyword_index.storage_context.persist(
            persist_dir=self.keyword_storage_path
        )
        # self.kg_index.storage_context.persist(persist_dir=self.kg_storage_path)
        print(f"Document '{doc_id}' deleted successfully.")

    def get_all_retrievers(self) -> List[BaseRetriever]:
        """Gets a list of retrievers from each index for use in a query engine.

        Returns:
            List[BaseRetriever]: A list containing the retrievers for the
                                vector, keyword, and knowledge graph indices.
        """
        return [
            self.vector_index.as_retriever(similarity_top_k=settings.TOP_K),
            self.keyword_index.as_retriever(similarity_top_k=settings.TOP_K),
            self.kg_index.as_retriever(
                similarity_top_k=settings.TOP_K, include_text=False
            ),  # For the graph, relationships are more important than node text.
        ]

