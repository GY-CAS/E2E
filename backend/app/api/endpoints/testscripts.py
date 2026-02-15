from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from uuid import UUID
from datetime import datetime
import json

from app.core.database import get_session
from app.models import (
    TestScript, TestScriptCreate, TestScriptUpdate, TestScriptRead,
    ScriptStatus, ScriptLanguage
)

router = APIRouter(prefix="/test-scripts", tags=["Test Scripts"])


@router.post("/", response_model=TestScriptRead, status_code=status.HTTP_201_CREATED)
async def create_test_script(
    script_data: TestScriptCreate,
    session: Session = Depends(get_session)
) -> TestScript:
    script_dict = script_data.model_dump()
    dependencies = script_dict.pop("dependencies", [])
    
    script = TestScript(**script_dict)
    script.set_dependencies(dependencies)
    
    session.add(script)
    session.commit()
    session.refresh(script)
    return script


@router.post("/batch", response_model=List[TestScriptRead], status_code=status.HTTP_201_CREATED)
async def create_test_scripts_batch(
    script_list: List[TestScriptCreate],
    session: Session = Depends(get_session)
) -> List[TestScript]:
    scripts = []
    for script_data in script_list:
        script_dict = script_data.model_dump()
        dependencies = script_dict.pop("dependencies", [])
        
        script = TestScript(**script_dict)
        script.set_dependencies(dependencies)
        
        session.add(script)
        scripts.append(script)
    
    session.commit()
    for script in scripts:
        session.refresh(script)
    
    return scripts


@router.get("/", response_model=List[TestScriptRead])
async def list_test_scripts(
    project_id: UUID = None,
    test_case_id: UUID = None,
    language: ScriptLanguage = None,
    status_filter: ScriptStatus = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
) -> List[TestScript]:
    query = select(TestScript)
    
    if project_id:
        query = query.where(TestScript.project_id == project_id)
    if test_case_id:
        query = query.where(TestScript.test_case_id == test_case_id)
    if language:
        query = query.where(TestScript.language == language)
    if status_filter:
        query = query.where(TestScript.status == status_filter)
    
    query = query.offset(skip).limit(limit)
    scripts = session.exec(query).all()
    return scripts


@router.get("/{script_id}", response_model=TestScriptRead)
async def get_test_script(
    script_id: UUID,
    session: Session = Depends(get_session)
) -> TestScript:
    script = session.get(TestScript, script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test Script {script_id} not found"
        )
    return script


@router.patch("/{script_id}", response_model=TestScriptRead)
async def update_test_script(
    script_id: UUID,
    script_data: TestScriptUpdate,
    session: Session = Depends(get_session)
) -> TestScript:
    script = session.get(TestScript, script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test Script {script_id} not found"
        )
    
    update_data = script_data.model_dump(exclude_unset=True)
    
    if "dependencies" in update_data:
        deps = update_data.pop("dependencies")
        script.set_dependencies(deps)
    
    for key, value in update_data.items():
        setattr(script, key, value)
    
    script.updated_at = datetime.utcnow()
    
    session.add(script)
    session.commit()
    session.refresh(script)
    return script


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_script(
    script_id: UUID,
    session: Session = Depends(get_session)
):
    script = session.get(TestScript, script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test Script {script_id} not found"
        )
    
    session.delete(script)
    session.commit()
    return None


@router.get("/{script_id}/download")
async def download_test_script(
    script_id: UUID,
    session: Session = Depends(get_session)
):
    import os
    from fastapi.responses import FileResponse
    
    script = session.get(TestScript, script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test Script {script_id} not found"
        )
    
    if script.file_path and os.path.exists(script.file_path):
        return FileResponse(
            path=script.file_path,
            filename=f"{script.name}.{'py' if script.language == ScriptLanguage.PYTHON else 'java'}",
            media_type="text/plain"
        )
    
    from fastapi.responses import Response
    ext = "py" if script.language == ScriptLanguage.PYTHON else "java"
    return Response(
        content=script.content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={script.name}.{ext}"
        }
    )
