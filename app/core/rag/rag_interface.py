import os
import uuid
from typing import List

from pydantic import BaseModel

from app.core.logging import logger
from app.core.rag import DocumentProcessor, MultiIndexManager, RAGQueryEngine


class DocumentInfo(BaseModel):
    doc_id: str
    file_name: str

class RAGResponse(BaseModel):
    answer: str
    sources: List[str]

class RagInterface:
    """Interface for interacting with the Retrieval-Augmented Generation (RAG) system.

    This class provides methods to add, delete, list documents, and perform search queries
    using the RAG engine.

    Attributes:
    ----------
    doc_processor : DocumentProcessor
        Handles document processing and node extraction.
    index_manager : MultiIndexManager
        Manages document indices for retrieval.
    query_engine : RAGQueryEngine
        Executes search queries using the RAG system.
    upload_dir : str
        Directory path for uploaded documents.

    Methods:
    -------
    add_document(file_path: str, file_name: str) -> str
        Asynchronously add a document to the RAG system.
    delete_document(doc_id: str) -> bool
        Delete a document by its ID.
    list_documents() -> List[DocumentInfo]
        List all managed documents.
    search(query: str) -> RAGResponse
        Asynchronously search for an answer to a query.
    """
    def __init__(self): #noqa
        logger.debug("init_rag_interface")
        self.doc_processor = DocumentProcessor()
        self.index_manager = MultiIndexManager()
        self.query_engine = RAGQueryEngine(self.index_manager)
        
        self.upload_dir = "./uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
        logger.debug("init_rag_interface_success")

    async def add_document(self, file_path: str, file_name: str) -> str:
        """Asynchronously add a document to the RAG system.

        Parameters
        ----------
        file_path : str
            The path to the file to be added.
        file_name : str
            The name of the file to be added.

        Returns:
        -------
        str
            The unique document ID assigned to the added document.
        """
        doc_id = f"{os.path.splitext(file_name)[0]}_{uuid.uuid4().hex[:8]}"
        logger.info("add_document_start", file_path=file_path, file_name=file_name)
        
        nodes = self.doc_processor.process_document(file_path, doc_id)
        self.index_manager.add_document(nodes)
        
        logger.info("add_document_success", file_path=file_path, file_name=file_name)
        return doc_id

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the RAG system by its document ID.

        Parameters
        ----------
        doc_id : str
            The unique identifier of the document to be deleted.

        Returns:
        -------
        bool
            True if the document was deleted successfully, False otherwise.
        """
        try:
            await self.index_manager.delete_document(doc_id)
            return True
        except Exception as e:
            logger.error("delete_document_failed", error=str(e))
            return False

    def list_documents(self) -> List[DocumentInfo]:
        """List all documents currently managed by the RAG system.

        Returns:
        -------
        List[DocumentInfo]
            A list of DocumentInfo objects containing document IDs and file names.
        """
        docstore = self.index_manager.storage_context.docstore
        all_docs_info = docstore.get_all_ref_doc_info()
        
        if not all_docs_info:
            return []
            
        return [
            DocumentInfo(doc_id=doc_id, file_name=info.metadata.get("file_name", "N/A"))
            for doc_id, info in all_docs_info.items()
        ]

    async def search(self, query: str) -> RAGResponse:
        """Asynchronously search for an answer to the given query using the RAG engine.

        Parameters
        ----------
        query : str
            The user's query string.

        Returns:
        -------
        RAGResponse
            The response containing the answer and its sources.
        """
        response = await self.query_engine.aquery(query)
        return RAGResponse(
            answer=str(response), # Приводим к строке на всякий случай
            sources=response.metadata.get("sources", [])
        )