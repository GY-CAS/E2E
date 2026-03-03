from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from uuid import UUID
from datetime import datetime
import json
import logging
import os

from fastapi.responses import FileResponse, Response

from app.core.database import get_session
from app.core.console_output import (
    print_step_start, print_step_end, print_success, print_error,
    print_warning, print_info
)
from app.models import (
    TestScript, TestScriptCreate, TestScriptUpdate, TestScriptRead,
    ScriptStatus, ScriptLanguage
)

router = APIRouter(prefix="/test-scripts", tags=["Test Scripts"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=TestScriptRead, status_code=status.HTTP_201_CREATED)
async def create_test_script(
    script_data: TestScriptCreate,
    session: Session = Depends(get_session)
) -> TestScript:
    operation = "创建测试脚本"
    print_step_start(f"{operation}: {script_data.name}", "ScriptAPI")

    try:
        script_dict = script_data.model_dump()
        dependencies = script_dict.pop("dependencies", [])

        print_info(f"项目ID: {script_dict.get('project_id')}, 语言: {script_dict.get('language')}", "ScriptAPI")

        script = TestScript(**script_dict)
        script.set_dependencies(dependencies)

        session.add(script)
        session.commit()
        session.refresh(script)

        print_step_end(f"{operation}", f"成功，ID: {script.id}", "ScriptAPI")
        logger.info(f"Test script created: {script.id} - {script.name}")

        return script

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ScriptAPI")
        logger.error(f"Failed to create test script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[TestScriptRead], status_code=status.HTTP_201_CREATED)
async def create_test_scripts_batch(
    script_list: List[TestScriptCreate],
    session: Session = Depends(get_session)
) -> List[TestScript]:
    operation = "批量创建测试脚本"
    print_step_start(f"{operation}: {len(script_list)} 个", "ScriptAPI")

    try:
        scripts = []
        for script_data in script_list:
            script_dict = script_data.model_dump()
            dependencies = script_dict.pop("dependencies", [])

            script = TestScript(**script_dict)
            script.set_dependencies(dependencies)

            session.add(script)
            scripts.append(script)

        print_info(f"创建 {len(scripts)} 个测试脚本", "ScriptAPI")

        session.commit()
        for script in scripts:
            session.refresh(script)

        print_step_end(f"{operation}", f"成功创建 {len(scripts)} 个", "ScriptAPI")
        logger.info(f"Batch created {len(scripts)} test scripts")

        return scripts

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ScriptAPI")
        logger.error(f"Failed to batch create test scripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    operation = "获取测试脚本列表"
    print_step_start(f"{operation}", "ScriptAPI")

    try:
        query = select(TestScript)

        if project_id:
            print_info(f"项目ID: {project_id}", "ScriptAPI")
            query = query.where(TestScript.project_id == project_id)
        if test_case_id:
            print_info(f"测试用例ID: {test_case_id}", "ScriptAPI")
            query = query.where(TestScript.test_case_id == test_case_id)
        if language:
            print_info(f"语言: {language}", "ScriptAPI")
            query = query.where(TestScript.language == language)
        if status_filter:
            print_info(f"状态: {status_filter}", "ScriptAPI")
            query = query.where(TestScript.status == status_filter)

        query = query.offset(skip).limit(limit)
        scripts = session.exec(query).all()

        print_step_end(f"{operation}", f"共 {len(scripts)} 个", "ScriptAPI")
        logger.info(f"Listed test scripts: {len(scripts)} items")

        return scripts

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ScriptAPI")
        logger.error(f"Failed to list test scripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{script_id}", response_model=TestScriptRead)
async def get_test_script(
    script_id: UUID,
    session: Session = Depends(get_session)
) -> TestScript:
    operation = "获取测试脚本详情"
    print_step_start(f"{operation}: {script_id}", "ScriptAPI")

    try:
        script = session.get(TestScript, script_id)
        if not script:
            print_warning(f"测试脚本不存在: {script_id}", "ScriptAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test Script {script_id} not found"
            )

        print_step_end(f"{operation}", f"名称: {script.name}", "ScriptAPI")
        logger.info(f"Get test script: {script_id}")

        return script

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ScriptAPI")
        logger.error(f"Failed to get test script {script_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{script_id}", response_model=TestScriptRead)
async def update_test_script(
    script_id: UUID,
    script_data: TestScriptUpdate,
    session: Session = Depends(get_session)
) -> TestScript:
    operation = "更新测试脚本"
    print_step_start(f"{operation}: {script_id}", "ScriptAPI")

    try:
        script = session.get(TestScript, script_id)
        if not script:
            print_warning(f"测试脚本不存在: {script_id}", "ScriptAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test Script {script_id} not found"
            )

        update_data = script_data.model_dump(exclude_unset=True)
        print_info(f"更新字段: {list(update_data.keys())}", "ScriptAPI")

        if "dependencies" in update_data:
            deps = update_data.pop("dependencies")
            script.set_dependencies(deps)

        for key, value in update_data.items():
            setattr(script, key, value)

        script.updated_at = datetime.utcnow()

        session.add(script)
        session.commit()
        session.refresh(script)

        print_step_end(f"{operation}", "成功", "ScriptAPI")
        logger.info(f"Test script updated: {script_id}")

        return script

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ScriptAPI")
        logger.error(f"Failed to update test script {script_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_script(
    script_id: UUID,
    session: Session = Depends(get_session)
):
    operation = "删除测试脚本"
    print_step_start(f"{operation}: {script_id}", "ScriptAPI")

    try:
        script = session.get(TestScript, script_id)
        if not script:
            print_warning(f"测试脚本不存在: {script_id}", "ScriptAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test Script {script_id} not found"
            )

        print_info(f"删除脚本: {script.name}", "ScriptAPI")

        session.delete(script)
        session.commit()

        print_step_end(f"{operation}", "成功", "ScriptAPI")
        logger.info(f"Test script deleted: {script_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ScriptAPI")
        logger.error(f"Failed to delete test script {script_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{script_id}/download")
async def download_test_script(
    script_id: UUID,
    session: Session = Depends(get_session)
):
    operation = "下载测试脚本"
    print_step_start(f"{operation}: {script_id}", "ScriptAPI")

    try:
        script = session.get(TestScript, script_id)
        if not script:
            print_warning(f"测试脚本不存在: {script_id}", "ScriptAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test Script {script_id} not found"
            )

        print_info(f"脚本名称: {script.name}, 语言: {script.language}", "ScriptAPI")

        if script.file_path and os.path.exists(script.file_path):
            ext = "py" if script.language == ScriptLanguage.PYTHON else "java"
            print_step_end(f"{operation}", f"从文件系统", "ScriptAPI")
            return FileResponse(
                path=script.file_path,
                filename=f"{script.name}.{ext}",
                media_type="text/plain"
            )

        ext = "py" if script.language == ScriptLanguage.PYTHON else "java"
        print_step_end(f"{operation}", f"从数据库", "ScriptAPI")
        logger.info(f"Test script downloaded from DB: {script_id}")

        return Response(
            content=script.content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={script.name}.{ext}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ScriptAPI")
        logger.error(f"Failed to download test script {script_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
