from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from uuid import UUID
from datetime import datetime
import json

from app.core.database import get_session
from app.models import (
    FunctionPoint, FunctionPointCreate, FunctionPointUpdate, FunctionPointRead,
    FPStatus, TestType, Priority
)

router = APIRouter(prefix="/function-points", tags=["Function Points"])


@router.post("/", response_model=FunctionPointRead, status_code=status.HTTP_201_CREATED)
async def create_function_point(
    fp_data: FunctionPointCreate,
    session: Session = Depends(get_session)
) -> FunctionPoint:
    fp = FunctionPoint(**fp_data.model_dump())
    session.add(fp)
    session.commit()
    session.refresh(fp)
    return fp


@router.post("/batch", response_model=List[FunctionPointRead], status_code=status.HTTP_201_CREATED)
async def create_function_points_batch(
    fp_list: List[FunctionPointCreate],
    session: Session = Depends(get_session)
) -> List[FunctionPoint]:
    fps = []
    for fp_data in fp_list:
        fp = FunctionPoint(**fp_data.model_dump())
        session.add(fp)
        fps.append(fp)
    
    session.commit()
    for fp in fps:
        session.refresh(fp)
    
    return fps


@router.get("/", response_model=List[FunctionPointRead])
async def list_function_points(
    project_id: UUID = None,
    test_type: TestType = None,
    priority: Priority = None,
    status_filter: FPStatus = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
) -> List[FunctionPoint]:
    query = select(FunctionPoint)
    
    if project_id:
        query = query.where(FunctionPoint.project_id == project_id)
    if test_type:
        query = query.where(FunctionPoint.test_type == test_type)
    if priority:
        query = query.where(FunctionPoint.priority == priority)
    if status_filter:
        query = query.where(FunctionPoint.status == status_filter)
    
    query = query.offset(skip).limit(limit)
    fps = session.exec(query).all()
    return fps


@router.get("/{fp_id}", response_model=FunctionPointRead)
async def get_function_point(
    fp_id: UUID,
    session: Session = Depends(get_session)
) -> FunctionPoint:
    fp = session.get(FunctionPoint, fp_id)
    if not fp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function Point {fp_id} not found"
        )
    return fp


@router.patch("/{fp_id}", response_model=FunctionPointRead)
async def update_function_point(
    fp_id: UUID,
    fp_data: FunctionPointUpdate,
    session: Session = Depends(get_session)
) -> FunctionPoint:
    fp = session.get(FunctionPoint, fp_id)
    if not fp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function Point {fp_id} not found"
        )
    
    update_data = fp_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(fp, key, value)
    
    fp.updated_at = datetime.utcnow()
    
    session.add(fp)
    session.commit()
    session.refresh(fp)
    return fp


@router.post("/{fp_id}/approve", response_model=FunctionPointRead)
async def approve_function_point(
    fp_id: UUID,
    session: Session = Depends(get_session)
) -> FunctionPoint:
    fp = session.get(FunctionPoint, fp_id)
    if not fp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function Point {fp_id} not found"
        )
    
    fp.status = FPStatus.APPROVED
    fp.updated_at = datetime.utcnow()
    
    session.add(fp)
    session.commit()
    session.refresh(fp)
    return fp


@router.post("/{fp_id}/reject", response_model=FunctionPointRead)
async def reject_function_point(
    fp_id: UUID,
    session: Session = Depends(get_session)
) -> FunctionPoint:
    fp = session.get(FunctionPoint, fp_id)
    if not fp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function Point {fp_id} not found"
        )
    
    fp.status = FPStatus.REJECTED
    fp.updated_at = datetime.utcnow()
    
    session.add(fp)
    session.commit()
    session.refresh(fp)
    return fp


@router.delete("/{fp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_function_point(
    fp_id: UUID,
    session: Session = Depends(get_session)
):
    fp = session.get(FunctionPoint, fp_id)
    if not fp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function Point {fp_id} not found"
        )
    
    session.delete(fp)
    session.commit()
    return None
