from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from uuid import UUID
from datetime import datetime
import json

from app.core.database import get_session
from app.models import (
    TestCase, TestCaseCreate, TestCaseUpdate, TestCaseRead, TestStepSchema,
    TCStatus, TestType, Priority
)

router = APIRouter(prefix="/test-cases", tags=["Test Cases"])


@router.post("/", response_model=TestCaseRead, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    tc_data: TestCaseCreate,
    session: Session = Depends(get_session)
) -> TestCase:
    tc_dict = tc_data.model_dump()
    test_steps = tc_dict.pop("test_steps", [])
    tags = tc_dict.pop("tags", [])
    test_data = tc_dict.pop("test_data", None)
    
    tc = TestCase(**tc_dict)
    tc.set_test_steps([s.model_dump() if hasattr(s, 'model_dump') else s for s in test_steps])
    tc.set_tags(tags)
    if test_data:
        tc.test_data = json.dumps(test_data, ensure_ascii=False)
    
    session.add(tc)
    session.commit()
    session.refresh(tc)
    return tc


@router.post("/batch", response_model=List[TestCaseRead], status_code=status.HTTP_201_CREATED)
async def create_test_cases_batch(
    tc_list: List[TestCaseCreate],
    session: Session = Depends(get_session)
) -> List[TestCase]:
    tcs = []
    for tc_data in tc_list:
        tc_dict = tc_data.model_dump()
        test_steps = tc_dict.pop("test_steps", [])
        tags = tc_dict.pop("tags", [])
        test_data = tc_dict.pop("test_data", None)
        
        tc = TestCase(**tc_dict)
        tc.set_test_steps([s.model_dump() if hasattr(s, 'model_dump') else s for s in test_steps])
        tc.set_tags(tags)
        if test_data:
            tc.test_data = json.dumps(test_data, ensure_ascii=False)
        
        session.add(tc)
        tcs.append(tc)
    
    session.commit()
    for tc in tcs:
        session.refresh(tc)
    
    return tcs


@router.get("/", response_model=List[TestCaseRead])
async def list_test_cases(
    project_id: UUID = None,
    function_point_id: UUID = None,
    test_type: TestType = None,
    priority: Priority = None,
    status_filter: TCStatus = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
) -> List[TestCase]:
    query = select(TestCase)
    
    if project_id:
        query = query.where(TestCase.project_id == project_id)
    if function_point_id:
        query = query.where(TestCase.function_point_id == function_point_id)
    if test_type:
        query = query.where(TestCase.test_type == test_type)
    if priority:
        query = query.where(TestCase.priority == priority)
    if status_filter:
        query = query.where(TestCase.status == status_filter)
    
    query = query.offset(skip).limit(limit)
    tcs = session.exec(query).all()
    return tcs


@router.get("/{tc_id}", response_model=TestCaseRead)
async def get_test_case(
    tc_id: UUID,
    session: Session = Depends(get_session)
) -> TestCase:
    tc = session.get(TestCase, tc_id)
    if not tc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test Case {tc_id} not found"
        )
    return tc


@router.patch("/{tc_id}", response_model=TestCaseRead)
async def update_test_case(
    tc_id: UUID,
    tc_data: TestCaseUpdate,
    session: Session = Depends(get_session)
) -> TestCase:
    tc = session.get(TestCase, tc_id)
    if not tc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test Case {tc_id} not found"
        )
    
    update_data = tc_data.model_dump(exclude_unset=True)
    
    if "test_steps" in update_data:
        steps = update_data.pop("test_steps")
        tc.set_test_steps([s.model_dump() if hasattr(s, 'model_dump') else s for s in steps])
    
    if "tags" in update_data:
        tags = update_data.pop("tags")
        tc.set_tags(tags)
    
    if "test_data" in update_data:
        test_data = update_data.pop("test_data")
        tc.test_data = json.dumps(test_data, ensure_ascii=False) if test_data else None
    
    for key, value in update_data.items():
        setattr(tc, key, value)
    
    tc.updated_at = datetime.utcnow()
    
    session.add(tc)
    session.commit()
    session.refresh(tc)
    return tc


@router.post("/{tc_id}/approve", response_model=TestCaseRead)
async def approve_test_case(
    tc_id: UUID,
    session: Session = Depends(get_session)
) -> TestCase:
    tc = session.get(TestCase, tc_id)
    if not tc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test Case {tc_id} not found"
        )
    
    tc.status = TCStatus.APPROVED
    tc.updated_at = datetime.utcnow()
    
    session.add(tc)
    session.commit()
    session.refresh(tc)
    return tc


@router.delete("/{tc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    tc_id: UUID,
    session: Session = Depends(get_session)
):
    tc = session.get(TestCase, tc_id)
    if not tc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test Case {tc_id} not found"
        )
    
    session.delete(tc)
    session.commit()
    return None
