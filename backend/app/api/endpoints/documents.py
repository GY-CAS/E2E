from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlmodel import Session, select
from typing import List
from uuid import UUID
import os
import aiofiles
from datetime import datetime

from app.core.database import get_session
from app.core.config import settings
from app.models import (
    Document, DocumentCreate, DocumentRead, DocType, DocStatus
)

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_upload_dir():
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


async def save_upload_file(file: UploadFile, project_id: UUID) -> str:
    upload_dir = get_upload_dir()
    project_dir = os.path.join(upload_dir, str(project_id))
    os.makedirs(project_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(project_dir, safe_filename)
    
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    
    return file_path


def detect_doc_type(filename: str) -> DocType:
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    
    type_mapping = {
        "pdf": DocType.REQUIREMENT,
        "docx": DocType.REQUIREMENT,
        "doc": DocType.REQUIREMENT,
        "md": DocType.SPEC,
        "txt": DocType.REQUIREMENT,
        "xlsx": DocType.SPEC,
        "xls": DocType.SPEC,
        "png": DocType.IMAGE,
        "jpg": DocType.IMAGE,
        "jpeg": DocType.IMAGE,
    }
    
    return type_mapping.get(ext, DocType.REQUIREMENT)


@router.post("/upload/{project_id}", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    doc_type: DocType = None,
    session: Session = Depends(get_session)
) -> Document:
    from app.models import Project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    if doc_type is None:
        doc_type = detect_doc_type(file.filename or "unknown")
    
    file_path = await save_upload_file(file, project_id)
    file_size = os.path.getsize(file_path)
    
    document = Document(
        project_id=project_id,
        name=file.filename or "unnamed",
        doc_type=doc_type,
        file_path=file_path,
        file_size=file_size,
        status=DocStatus.PENDING
    )
    
    session.add(document)
    session.commit()
    session.refresh(document)
    
    return document


@router.get("/", response_model=List[DocumentRead])
async def list_documents(
    project_id: UUID = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
) -> List[Document]:
    query = select(Document)
    if project_id:
        query = query.where(Document.project_id == project_id)
    query = query.offset(skip).limit(limit)
    documents = session.exec(query).all()
    return documents


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: UUID,
    session: Session = Depends(get_session)
) -> Document:
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    session.delete(document)
    session.commit()
    return None


@router.post("/{document_id}/parse", status_code=status.HTTP_202_ACCEPTED)
async def parse_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    document.status = DocStatus.PROCESSING
    session.add(document)
    session.commit()
    
    return {"message": "Document parsing started", "document_id": document_id}
