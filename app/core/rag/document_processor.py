"""Document processing utilities for parsing files into nodes with contextual sentence windows.

This module provides the DocumentProcessor class for loading documents, parsing them into nodes,
and attaching relevant metadata for downstream processing.
"""

import os
from typing import List

from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.schema import BaseNode

from app.core.logging import logger


class DocumentProcessor:
    """Processes documents by parsing them into nodes with contextual sentence windows.

    Methods:
    -------
    process_document(file_path: str, doc_id: str) -> List[BaseNode]
        Loads a document, parses it into nodes, and attaches metadata.
    """
    def __init__(self):
        """Initialize the DocumentProcessor with a sentence window node parser."""
        logger.debug("document_processor_initializing")
        self.node_parser = SentenceWindowNodeParser.from_defaults(
            window_size=3,  # Количество предложений до и после для контекста
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        )
        logger.debug("document_processor_initializing_success")

    def process_document(self, file_path: str, doc_id: str) -> List[BaseNode]:
        """Loads a document from the given file path, parses it into nodes with contextual sentence windows, attaches metadata, and returns the list of nodes.

        Parameters:
        ----------
        file_path : str
            The path to the document file to be processed.
        doc_id : str
            The unique identifier to assign to the document and its nodes.

        Returns:
        -------
        List[BaseNode]
            A list of nodes parsed from the document, each with attached metadata.

        Raises:
        ------
        FileNotFoundError
            If the file does not exist at the specified path.
        ValueError
            If the document could not be parsed.
        """
        logger.debug("process_document", file_path=file_path, document_id=doc_id)
        if not os.path.exists(file_path):
            logger.error("process_document_failed", messages=f"FileNotFound {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        reader = SimpleDirectoryReader(input_files=[file_path])
        documents = reader.load_data()

        if not documents:
            logger.error("process_document_failed", message=f"Could not parse the document {file_path}")
            raise ValueError(f"Could not parse the document {file_path}")
        document = documents[0]
        document.id_ = doc_id

        nodes = self.node_parser.get_nodes_from_documents([document])
        for node in nodes:
            node.metadata["doc_id"] = doc_id
            node.metadata["file_name"] = os.path.basename(file_path)

        logger.info("process_document_success", len_chunks=len(nodes))
        return nodes