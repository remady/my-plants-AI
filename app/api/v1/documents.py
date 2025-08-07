"""Documents management API endpoints.

This modules provides APIs for create / list / delete user documents
"""

import os
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)

from app.api.v1.auth import get_current_session
from app.core.logging import logger
from app.core.rag import RagInterface
from app.models.session import Session
from app.schemas.document import DocumentResponse
from app.services.database import database_service
from app.utils.file_utils import remove_file, save_file_by_chunks

DOCUMENTS_FOLDER = Path("User_documents")
router = APIRouter()
rag_instance = RagInterface()


def get_rag_dep():
    """RAG FastAPI dependency."""
    return rag_instance


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    request: Request,
    document: UploadFile = File(...),
    rag: RagInterface = Depends(get_rag_dep),
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
        index_id = await rag.add_document(file_path=file_path, file_name=document.filename)
        doc = await database_service.create_upload_document(
            user_id=session.user_id,
            file_name=document.filename,
            size=document.size,
            extension=os.path.splitext(document.filename)[-1].lower(),
        )

        remove_file(file_path)
        return DocumentResponse(id=doc.id, index_id=index_id, name=doc.filename, size=doc.size, extension=doc.extension)
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
    rag: RagInterface = Depends(get_rag_dep),
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
        status = await rag.delete_document(removed_document.index_id)
        return {"ok": status}
    except Exception as e:
        logger.error("delete_document_failed", session_id=session.id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
