from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, Response
from sqlmodel import Session, select
from typing import List
from uuid import UUID
from datetime import datetime
import json
import asyncio
import logging

from app.core.database import get_session
from app.core.config import settings
from app.core.console_output import (
    print_step_start, print_step_end, print_success, print_error,
    print_warning, print_info
)
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
    operation = "上传文档"
    print_step_start(f"{operation}: {file.filename}", "DocumentsAPI")

    try:
        project = session.get(Project, project_id)
        if not project:
            print_warning(f"项目不存在: {project_id}", "DocumentsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        if doc_type is None:
            doc_type = detect_doc_type(file.filename or "unknown")
            print_info(f"自动检测文档类型: {doc_type}", "DocumentsAPI")

        content_type = get_content_type(file.filename or "unknown")

        file_content = await file.read()
        file_size = len(file_content)
        print_info(f"文件大小: {file_size} bytes", "DocumentsAPI")

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"

        print_step_start(f"上传到MinIO: {safe_filename}", "DocumentsAPI")
        try:
            upload_result = await minio_service.upload_file(
                project_id=str(project_id),
                file_name=safe_filename,
                file_data=__import__('io').BytesIO(file_content),
                content_type=content_type,
                file_size=file_size
            )
            minio_path = f"{upload_result['bucket_name']}/{safe_filename}"
            print_step_end(f"上传到MinIO", "成功", "DocumentsAPI")
        except Exception as e:
            print_error(f"MinIO上传失败: {str(e)[:50]}", "DocumentsAPI")
            logger.error(f"Failed to upload to MinIO: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )

        print_info(f"创建文档记录: {file.filename}", "DocumentsAPI")
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

        print_step_end(f"{operation}", f"成功，文档ID: {document.id}", "DocumentsAPI")
        logger.info(f"Document uploaded: {document.id} - {document.name}")

        return document

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "DocumentsAPI")
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[DocumentRead])
async def list_documents(
    project_id: UUID = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
) -> List[Document]:
    operation = "获取文档列表"
    print_step_start(f"{operation}", "DocumentsAPI")

    try:
        query = select(Document)
        if project_id:
            print_info(f"项目ID: {project_id}", "DocumentsAPI")
            query = query.where(Document.project_id == project_id)

        query = query.offset(skip).limit(limit)
        documents = session.exec(query).all()

        print_step_end(f"{operation}", f"共 {len(documents)} 个文档", "DocumentsAPI")
        logger.info(f"Listed documents: {len(documents)} items")

        return documents

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "DocumentsAPI")
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: UUID,
    session: Session = Depends(get_session)
) -> Document:
    operation = "获取文档详情"
    print_step_start(f"{operation}: {document_id}", "DocumentsAPI")

    try:
        document = session.get(Document, document_id)
        if not document:
            print_warning(f"文档不存在: {document_id}", "DocumentsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        print_step_end(f"{operation}", f"文档名称: {document.name}", "DocumentsAPI")
        logger.info(f"Get document: {document_id}")

        return document

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "DocumentsAPI")
        logger.error(f"Failed to get document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    operation = "下载文档"
    print_step_start(f"{operation}: {document_id}", "DocumentsAPI")

    try:
        document = session.get(Document, document_id)
        if not document:
            print_warning(f"文档不存在: {document_id}", "DocumentsAPI")
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

        print_info(f"从MinIO下载: {object_name}", "DocumentsAPI")
        file_data = minio_service.download_file(document.project_id, object_name)

        if file_data is None:
            print_error("文件在MinIO中未找到", "DocumentsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in MinIO"
            )

        content_type = get_content_type(document.name)
        print_step_end(f"{operation}", f"成功，大小: {len(file_data)} bytes", "DocumentsAPI")
        logger.info(f"Document downloaded: {document_id}")

        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={document.name}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "DocumentsAPI")
        logger.error(f"Failed to download document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    operation = "删除文档"
    print_step_start(f"{operation}: {document_id}", "DocumentsAPI")

    try:
        document = session.get(Document, document_id)
        if not document:
            print_warning(f"文档不存在: {document_id}", "DocumentsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        print_info(f"删除文档: {document.name}", "DocumentsAPI")

        if document.file_path:
            parts = document.file_path.split("/")
            object_name = "/".join(parts[1:])
            print_info(f"删除MinIO文件: {object_name}", "DocumentsAPI")
            minio_service.delete_file(document.project_id, object_name)

        print_info(f"删除Milvus向量数据", "DocumentsAPI")
        milvus_service.delete_document_vectors(str(document.project_id), str(document_id))

        session.delete(document)
        session.commit()

        print_step_end(f"{operation}", "成功", "DocumentsAPI")
        logger.info(f"Document deleted: {document_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "DocumentsAPI")
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/parse", status_code=status.HTTP_202_ACCEPTED)
async def parse_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    operation = "解析文档"
    print_step_start(f"{operation}: {document_id}", "DocumentsAPI")

    try:
        document = session.get(Document, document_id)
        if not document:
            print_warning(f"文档不存在: {document_id}", "DocumentsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        print_info(f"文档名称: {document.name}, 类型: {document.doc_type}", "DocumentsAPI")
        document.status = DocStatus.PROCESSING
        session.add(document)
        session.commit()

        background_tasks.add_task(
            parse_document_task,
            document_id=str(document_id)
        )

        print_step_end(f"{operation}", "已启动后台任务", "DocumentsAPI")
        logger.info(f"Document parsing started: {document_id}")

        return {"message": "Document parsing started", "document_id": str(document_id)}

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "DocumentsAPI")
        logger.error(f"Failed to start document parsing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def parse_document_task(document_id: str):
    from sqlmodel import Session
    from app.core.database import engine
    from app.core.console_output import print_step_start, print_step_end, print_success, print_error

    print_step_start(f"解析文档任务: {document_id}", "ParseTask")

    with Session(engine) as session:
        document = session.get(Document, document_id)
        if not document:
            print_error(f"文档不存在: {document_id}", "ParseTask")
            logger.error(f"Document {document_id} not found in background task")
            return

        try:
            parts = document.file_path.split("/")
            object_name = "/".join(parts[1:])

            print_step_start(f"下载文档: {document.name}", "ParseTask")
            file_data = minio_service.download_file(document.project_id, object_name)

            if file_data is None:
                print_error("文档下载失败", "ParseTask")
                document.status = DocStatus.FAILED
                session.add(document)
                session.commit()
                return
            print_step_end(f"下载文档", f"大小: {len(file_data)} bytes", "ParseTask")

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
                print_success(f"文档解析成功: {result['metadata']['chunk_count']} 个块", "ParseTask")
                logger.info(f"Document {document_id} parsed successfully, {result['metadata']['chunk_count']} chunks stored to Milvus")
            else:
                document.status = DocStatus.FAILED
                print_error(f"文档解析失败: {result.get('error')}", "ParseTask")
                logger.error(f"Document {document_id} parsing failed: {result.get('error')}")

            session.add(document)
            session.commit()
            print_step_end(f"解析文档任务", f"状态: {document.status}", "ParseTask")

        except Exception as e:
            print_error(f"解析异常: {str(e)[:50]}", "ParseTask")
            logger.error(f"Error parsing document {document_id}: {e}")
            document.status = DocStatus.FAILED
            session.add(document)
            session.commit()


@router.get("/{document_id}/parse-status")
async def get_parse_status(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    operation = "获取解析状态"
    print_step_start(f"{operation}: {document_id}", "DocumentsAPI")

    try:
        document = session.get(Document, document_id)
        if not document:
            print_warning(f"文档不存在: {document_id}", "DocumentsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        vector_stats = milvus_service.get_collection_stats(str(document.project_id))

        result = {
            "document_id": str(document_id),
            "status": document.status,
            "has_content": bool(document.parsed_content),
            "content_length": len(document.parsed_content) if document.parsed_content else 0,
            "vector_collection": vector_stats
        }

        print_step_end(f"{operation}", f"状态: {document.status}", "DocumentsAPI")
        logger.info(f"Get parse status for {document_id}: {document.status}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "DocumentsAPI")
        logger.error(f"Failed to get parse status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    operation = "获取文档内容"
    print_step_start(f"{operation}: {document_id}", "DocumentsAPI")

    try:
        document = session.get(Document, document_id)
        if not document:
            print_warning(f"文档不存在: {document_id}", "DocumentsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        if document.status != DocStatus.PARSED:
            print_warning(f"文档未解析，当前状态: {document.status}", "DocumentsAPI")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document not parsed yet. Current status: {document.status}"
            )

        print_step_end(f"{operation}", f"内容长度: {len(document.parsed_content)}", "DocumentsAPI")
        logger.info(f"Get document content: {document_id}")

        return {
            "document_id": str(document_id),
            "content": document.parsed_content
        }

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "DocumentsAPI")
        logger.error(f"Failed to get document content: {e}")
        raise HTTPException(status_code=500, detail=str(e))
