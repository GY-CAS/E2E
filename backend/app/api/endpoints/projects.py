from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func, delete
from typing import List, Dict, Any
from uuid import UUID
import logging

from app.core.database import get_session
from app.models import (
    Project, ProjectCreate, ProjectUpdate, ProjectRead,
    ProjectStatus, Document, FunctionPoint, TestCase, TestScript, MindMapNode, DocStatus
)

router = APIRouter(prefix="/projects", tags=["Projects"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    session: Session = Depends(get_session)
) -> Project:
    project = Project(**project_data.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("/", response_model=List[ProjectRead])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    status_filter: ProjectStatus = None,
    session: Session = Depends(get_session)
) -> List[Project]:
    query = select(Project)
    if status_filter:
        query = query.where(Project.status == status_filter)
    query = query.offset(skip).limit(limit)
    projects = session.exec(query).all()
    return projects


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    session: Session = Depends(get_session)
) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return project


@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: UUID,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    doc_count = session.exec(
        select(func.count(Document.id)).where(Document.project_id == project_id)
    ).one()
    
    parsed_doc_count = session.exec(
        select(func.count(Document.id)).where(
            Document.project_id == project_id,
            Document.status == DocStatus.PARSED
        )
    ).one()
    
    fp_count = session.exec(
        select(func.count(FunctionPoint.id)).where(FunctionPoint.project_id == project_id)
    ).one()
    
    tc_count = session.exec(
        select(func.count(TestCase.id)).where(TestCase.project_id == project_id)
    ).one()
    
    return {
        "project_id": str(project_id),
        "project_name": project.name,
        "document_count": doc_count,
        "parsed_document_count": parsed_doc_count,
        "function_point_count": fp_count,
        "test_case_count": tc_count
    }


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    session: Session = Depends(get_session)
) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    update_data = project_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    
    from datetime import datetime
    project.updated_at = datetime.utcnow()
    
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    session: Session = Depends(get_session)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    logger.info(f"Deleting project {project_id} and all related data")
    
    session.exec(delete(MindMapNode).where(MindMapNode.project_id == project_id))
    
    session.exec(delete(TestScript).where(TestScript.project_id == project_id))
    
    session.exec(delete(TestCase).where(TestCase.project_id == project_id))
    
    session.exec(delete(FunctionPoint).where(FunctionPoint.project_id == project_id))
    
    session.exec(delete(Document).where(Document.project_id == project_id))
    
    session.delete(project)
    session.commit()
    
    logger.info(f"Project {project_id} deleted successfully")
    return None
