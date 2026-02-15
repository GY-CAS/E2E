from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from uuid import UUID

from app.core.database import get_session
from app.models import (
    Project, ProjectCreate, ProjectUpdate, ProjectRead,
    ProjectStatus
)

router = APIRouter(prefix="/projects", tags=["Projects"])


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
    
    session.delete(project)
    session.commit()
    return None
