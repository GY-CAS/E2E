from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from typing import List
from uuid import UUID
from datetime import datetime
import json
import asyncio
import logging

from app.core.database import get_session
from app.core.config import settings
from app.models import (
    Document, DocumentCreate, DocumentRead, DocType, DocStatus, Project
)
from app.services import minio_service, document_parser, milvus_service

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


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
        "pptx": DocType.DESIGN,
        "ppt": DocType.DESIGN,
        "png": DocType.IMAGE,
        "jpg": DocType.IMAGE,
        "jpeg": DocType.IMAGE,
    }
    
    return type_mapping.get(ext, DocType.REQUIREMENT)


def get_content_type(filename: str) -> str:
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    
    content_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "md": "text/markdown",
        "txt": "text/plain",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "ppt": "application/vnd.ms-powerpoint",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }
    
    return content_types.get(ext, "application/octet-stream")


@router.post("/upload/{project_id}", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    doc_type: DocType = None,
    session: Session = Depends(get_session)
) -> Document:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    if doc_type is None:
        doc_type = detect_doc_type(file.filename or "unknown")
    
    content_type = get_content_type(file.filename or "unknown")
    
    file_content = await file.read()
    file_size = len(file_content)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    
    try:
        upload_result = await minio_service.upload_file(
            project_id=str(project_id),
            file_name=safe_filename,
            file_data=__import__('io').BytesIO(file_content),
            content_type=content_type,
            file_size=file_size
        )
        
        minio_path = f"{upload_result['bucket_name']}/{safe_filename}"
        
    except Exception as e:
        logger.error(f"Failed to upload to MinIO: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    
    document = Document(
        project_id=project_id,
        name=file.filename or "unnamed",
        doc_type=doc_type,
        file_path=minio_path,
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


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    if not document.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage"
        )
    
    parts = document.file_path.split("/")
    object_name = "/".join(parts[1:])
    
    file_data = minio_service.download_file(document.project_id, object_name)
    
    if file_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in MinIO"
        )
    
    from fastapi.responses import Response
    content_type = get_content_type(document.name)
    
    return Response(
        content=file_data,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={document.name}"
        }
    )


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
    
    if document.file_path:
        parts = document.file_path.split("/")
        object_name = "/".join(parts[1:])
        minio_service.delete_file(document.project_id, object_name)
    
    milvus_service.delete_document_vectors(str(document.project_id), str(document_id))
    
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
    
    background_tasks.add_task(
        parse_document_task,
        document_id=str(document_id)
    )
    
    return {"message": "Document parsing started", "document_id": str(document_id)}


async def parse_document_task(document_id: str):
    from sqlmodel import Session
    from app.core.database import engine
    
    with Session(engine) as session:
        document = session.get(Document, document_id)
        if not document:
            logger.error(f"Document {document_id} not found in background task")
            return
        
        try:
            parts = document.file_path.split("/")
            object_name = "/".join(parts[1:])
            
            file_data = minio_service.download_file(document.project_id, object_name)
            
            if file_data is None:
                document.status = DocStatus.FAILED
                session.add(document)
                session.commit()
                return
            
            result = await document_parser.parse_and_store(
                project_id=str(document.project_id),
                document_id=str(document_id),
                file_name=document.name,
                file_data=file_data,
                doc_type=document.doc_type
            )
            
            if result["success"]:
                document.parsed_content = result["content"]
                document.status = DocStatus.PARSED
                logger.info(f"Document {document_id} parsed successfully, {result['metadata']['chunk_count']} chunks stored to Milvus")
            else:
                document.status = DocStatus.FAILED
                logger.error(f"Document {document_id} parsing failed: {result.get('error')}")
            
            session.add(document)
            session.commit()
            
        except Exception as e:
            logger.error(f"Error parsing document {document_id}: {e}")
            document.status = DocStatus.FAILED
            session.add(document)
            session.commit()


@router.get("/{document_id}/parse-status")
async def get_parse_status(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    vector_stats = milvus_service.get_collection_stats(str(document.project_id))
    
    return {
        "document_id": str(document_id),
        "status": document.status,
        "has_content": bool(document.parsed_content),
        "content_length": len(document.parsed_content) if document.parsed_content else 0,
        "vector_collection": vector_stats
    }


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    if document.status != DocStatus.PARSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document not parsed yet. Current status: {document.status}"
        )
    
    return {
        "document_id": str(document_id),
        "content": document.parsed_content
    }
