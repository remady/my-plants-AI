"""."""

import os
import sqlite3
from chromadb.config import Settings
from langchain_chroma import Chroma

from app.core.embeddings import embeddings

from typing import List, Dict, Any, Literal, Optional, Union
import uuid
from datetime import datetime
from app.core.logging import logger
from langchain_core.documents import Document
from langchain.embeddings.base import Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    JSONLoader,
)


class ChromaWrapper:
    """Wrapper class for managing a Chroma vector store with document splitting, file loading, search, and logging capabilities.
    
    Attributes:
    ----------
    collection_name : str
        The name of the Chroma collection.
    embedding_function : Embeddings
        The embedding function used for vectorization.
    persist_directory : Optional[str]
        Directory to persist the vector store.
    chunk_size : int
        Size of text chunks for splitting documents.
    chunk_overlap : int
        Overlap between text chunks.
    log_db_path : str
        Path to the SQLite database for logging actions.

    Methods:
    -------
    add_documents(docs, ids=None, split=True)
        Add documents to the vector store.
    delete_documents(ids)
        Delete documents by their IDs.
    search(query, k=5)
        Search for similar documents.
    search_with_metadata_filter(query, metadata_filter, k=5)
        Search with metadata filtering.
    clear_all()
        Remove all documents from the store.
    add_documents_from_files(file_paths, common_metadata=None)
        Load and add documents from files.
    """

    def __init__(
        self,
        collection_name: str,
        embedding_function: Embeddings,
        persist_directory: Optional[str] = None,
        chunk_size: int = 200,
        chunk_overlap: int = 50,
    ):
        """Initialize the ChromaWrapper with collection name, embedding function, persistence directory, chunking options, and log database path.

        Parameters
        ----------
        collection_name : str
            The name of the Chroma collection.
        embedding_function : Embeddings
            The embedding function used for vectorization.
        persist_directory : Optional[str], optional
            Directory to persist the vector store.
        chunk_size : int, optional
            Size of text chunks for splitting documents.
        chunk_overlap : int, optional
            Overlap between text chunks.
        log_db_path : str, optional
            Path to the SQLite database for logging actions.
        """
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.persist_directory = persist_directory

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
        )

        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
            persist_directory=self.persist_directory,
            client_settings=Settings(anonymized_telemetry=False)
        )

    def as_retriever(
        self, 
        search_type: Literal["similarity", "mmr", "similarity_score_threshold"], 
        search_kwargs: dict = None
    ):
        """Return a retriever object for querying the vector store."""
        return self.vector_store.as_retriever(search_type=search_type, search_kwargs=search_kwargs)

    def split_documents(self, docs: List[Document]) -> List[Document]:
        """Split a list of documents into smaller chunks using the configured text splitter.

        Parameters
        ----------
        docs : List[Document]
            The documents to be split.

        Returns:
        -------
        List[Document]
            The resulting list of split documents.
        """
        return self.text_splitter.split_documents(docs)

    async def add_documents(self, docs: List[Document], ids: Optional[List[str]] = None, split: bool = True):
        """Add documents to the vector store, optionally splitting them into chunks.

        Parameters
        ----------
        docs : List[Document]
            The documents to add.
        ids : Optional[List[str]], optional
            List of document IDs. If None, random UUIDs are generated.
        split : bool, optional
            Whether to split documents into chunks before adding, by default True.
        """
        if split:
            docs = self.split_documents(docs)
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(docs))]
        await self.vector_store.aadd_documents(documents=docs, ids=ids)
        logger.info("documents_added_to_vectorstore", num=len(docs))
        self._persist()

    async def delete_documents(self, ids: List[str]):
        """Delete documents from the vector store by their IDs.

        Parameters
        ----------
        ids : List[str]
            List of document IDs to delete.
        """
        await self.vector_store.adelete(ids)
        logger.info(f"Deleted documents: {ids}")
        self._persist()

    def list_ids(self) -> List[str]:
        """Return a list of all document IDs currently stored in the vector store.

        Returns:
        -------
        List[str]
            A list of document IDs.
        """
        return self.vector_store.get()["ids"]

    def search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents in the vector store.

        Parameters
        ----------
        query : str
            The query string to search for.
        k : int, optional
            The number of top results to return, by default 5.

        Returns:
        -------
        List[Document]
            A list of documents most similar to the query.
        """
        results = self.vector_store.similarity_search(query, k=k)
        logger.info(f"Search '{query}' returned {len(results)} results.")
        return results

    def search_with_metadata_filter(self, query: str, metadata_filter: Dict[str, str], k: int = 5) -> List[Document]:
        """Search for similar documents in the vector store using a metadata filter.

        Parameters
        ----------
        query : str
            The query string to search for.
        metadata_filter : Dict[str, str]
            Metadata key-value pairs to filter the search results.
        k : int, optional
            The number of top results to return, by default 5.

        Returns:
        -------
        List[Document]
            A list of documents most similar to the query and matching the metadata filter.
        """
        results = self.vector_store.similarity_search(query=query, k=k, filter=metadata_filter)
        logger.info(f"Search '{query}' with filter {metadata_filter} returned {len(results)} results.")
        return results
    
    def get_ids_by_document_name(self, name: str) -> list[str]:
        """Return a list of document IDs that match the given document name."""
        logger.info("get_document_ids_by_name", document_name=name)
        ids = self.vector_store.get(where={'filename': name})["ids"]
        return ids

    async def clear_all(self):
        """Remove all documents from the vector store.

        This method deletes all documents currently stored in the vector store and logs the action.
        """
        ids = self.list_ids()
        if ids:
            await self.delete_documents(ids)
            logger.info("Cleared all documents.")

    async def add_documents_from_files(self, file_paths: List[str], common_metadata: Optional[Dict] = None, loader_kw: Optional[Dict] = None):
        """Load documents from the specified file paths, optionally add common metadata, and add them to the vector store.

        Parameters:
        ----------
        file_paths : List[str]
            List of file paths to load documents from.
        common_metadata : Optional[Dict], optional
            Metadata to be added to each document, by default None.
        """
        docs = []
        if loader_kw is None:
            loader_kw = {}
        for path in file_paths:
            ext = os.path.splitext(path)[-1].lower()
            
            match ext:
                case '.txt':
                    loader = TextLoader(path, **loader_kw)
                case ".pdf":
                    loader = PyPDFLoader(path, **loader_kw)
                case ".md":
                    loader = UnstructuredMarkdownLoader(path, **loader_kw)
                case ".html" | ".htm":
                    loader = UnstructuredHTMLLoader(path, **loader_kw)
                case ".json":
                    if "jq_schema" not in loader_kw:
                        loader_kw["jq_schema"] = "."
                    loader = JSONLoader(path, text_content=False, json_lines=False, **loader_kw)
                case ".jsonl":
                    if "jq_schema" not in loader_kw:
                        loader_kw["jq_schema"] = r'to_entries | map("\(.key): \(.value | tostring)") | join("\n")'
                    loader = JSONLoader(path, text_content=False, json_lines=True, **loader_kw)
                case _:
                    logger.warning(f"Unsupported file type: {ext}")
                    continue

            file_docs = loader.load()
            for doc in file_docs:
                doc.metadata["filename"] = os.path.basename(path)
                if common_metadata:
                    doc.metadata.update(common_metadata)
            docs.extend(file_docs)

        await self.add_documents(docs, split=True)
        
    def add_documents_from_content(
        self,
        content: list[str],
        metadata: Optional[Dict] = None,
        split: bool = True
    ):
        """Add a document from provided content, with optional metadata and splitting."""
        if not content.strip():
            logger.warning("empty_document")
            return

        doc = Document(page_content=content)
        if metadata:
            doc.metadata.update(metadata)

        self.add_documents([doc], split=split)

    def _persist(self):
        pass
        # if self.persist_directory:
        #     self.vector_store.persist()


vector_store = ChromaWrapper('collection', embeddings, persist_directory="./chroma_langchain_db")
