"""Chatbot API endpoints for handling chat interactions.

This module provides endpoints for chat interactions, including regular chat,
streaming chat, message history management, and chat history clearing.
"""

import os
from pathlib import Path
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    File,
    UploadFile,
)

from app.api.v1.auth import get_current_session
from app.core.logging import logger
from app.models.session import Session
from app.schemas.document import DocumentResponse
from app.core.vectorstore import vector_store
from app.services.database import database_service
from app.utils.file_utils import remove_file, save_file_by_chunks


DOCUMENTS_FOLDER = Path("User_documents")
router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    request: Request,
    document: UploadFile = File(...),
    session: Session = Depends(get_current_session),
):
    """Pass."""
    try:
        logger.info("document_upload_request_received", session_id=session.id, filename=document.filename)

        # Do not save document multiple times
        doc = await database_service.get_uploaded_document(
            user_id=session.user_id, file_name=document.filename, size=document.size
        )
        if doc:
            logger.debug("document_found", session_id=session.id, filename=doc.filename)
            return DocumentResponse(id=doc.id, name=doc.filename, size=doc.size, extension=doc.extension)

        file_path: Path = DOCUMENTS_FOLDER / str(session.user_id) / document.filename
        await save_file_by_chunks(file_path=file_path, file=document)
        await vector_store.add_documents_from_files([file_path])
        doc = await database_service.create_upload_document(
            user_id=session.user_id,
            file_name=document.filename,
            size=document.size,
            extension=os.path.splitext(document.filename)[-1].lower(),
        )

        remove_file(file_path)
        return DocumentResponse(id=doc.id, name=doc.filename, size=doc.size, extension=doc.extension)
    except Exception as e:
        logger.error("upload_document_failed", session_id=session.id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    request: Request,
    session: Session = Depends(get_current_session),
):
    """List all user documents."""
    try:
        logger.info(
            "list_all_documents",
            session_id=session.id,
        )
        documents = await database_service.get_all_upload_documents(user_id=session.user_id)
        return [
            DocumentResponse(id=doc.id, name=doc.filename, size=doc.size, extension=doc.extension) for doc in documents
        ]
    except Exception as e:
        logger.error("list_all_documents_failed", session_id=session.id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    request: Request,
    document_id: uuid.UUID,
    session: Session = Depends(get_current_session),
):
    """Delete user document file."""
    try:
        logger.info("delete_document", session_id=session.id)
        removed_document = await database_service.delete_upload_document(
            user_id=session.user_id, document_id=document_id
        )
        if not removed_document:
            raise HTTPException(status_code=404, detail="No such document exist")
        ids = vector_store.get_ids_by_document_name(name=removed_document.filename)
        await vector_store.delete_documents(ids)
        return {"status": "ok"}
    except Exception as e:
        logger.error("delete_document_failed", session_id=session.id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
