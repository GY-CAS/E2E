from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from uuid import UUID
from datetime import datetime
import json
import logging

from app.core.database import get_session
from app.core.console_output import (
    print_step_start, print_step_end, print_success, print_error,
    print_warning, print_info
)
from app.models import (
    FunctionPoint, FunctionPointCreate, FunctionPointUpdate, FunctionPointRead,
    FPStatus, TestType, Priority
)

router = APIRouter(prefix="/function-points", tags=["Function Points"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=FunctionPointRead, status_code=status.HTTP_201_CREATED)
async def create_function_point(
    fp_data: FunctionPointCreate,
    session: Session = Depends(get_session)
) -> FunctionPoint:
    operation = "创建功能点"
    print_step_start(f"{operation}: {fp_data.name}", "FPAPI")

    try:
        fp = FunctionPoint(**fp_data.model_dump())
        print_info(f"项目ID: {fp.project_id}, 测试类型: {fp.test_type}", "FPAPI")

        session.add(fp)
        session.commit()
        session.refresh(fp)

        print_step_end(f"{operation}", f"成功，ID: {fp.id}", "FPAPI")
        logger.info(f"Function point created: {fp.id} - {fp.name}")

        return fp

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "FPAPI")
        logger.error(f"Failed to create function point: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[FunctionPointRead], status_code=status.HTTP_201_CREATED)
async def create_function_points_batch(
    fp_list: List[FunctionPointCreate],
    session: Session = Depends(get_session)
) -> List[FunctionPoint]:
    operation = "批量创建功能点"
    print_step_start(f"{operation}: {len(fp_list)} 个", "FPAPI")

    try:
        fps = []
        for fp_data in fp_list:
            fp = FunctionPoint(**fp_data.model_dump())
            session.add(fp)
            fps.append(fp)

        print_info(f"创建 {len(fps)} 个功能点", "FPAPI")

        session.commit()
        for fp in fps:
            session.refresh(fp)

        print_step_end(f"{operation}", f"成功创建 {len(fps)} 个", "FPAPI")
        logger.info(f"Batch created {len(fps)} function points")

        return fps

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "FPAPI")
        logger.error(f"Failed to batch create function points: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[FunctionPointRead])
async def list_function_points(
    project_id: str = None,
    test_type: TestType = None,
    priority: Priority = None,
    status_filter: FPStatus = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    operation = "获取功能点列表"
    print_step_start(f"{operation}", "FPAPI")

    try:
        query = select(FunctionPoint)

        if project_id:
            print_info(f"项目ID: {project_id}", "FPAPI")
            try:
                query = query.where(FunctionPoint.project_id == UUID(project_id))
            except ValueError:
                pass
        if test_type:
            print_info(f"测试类型: {test_type}", "FPAPI")
            query = query.where(FunctionPoint.test_type == test_type)
        if priority:
            print_info(f"优先级: {priority}", "FPAPI")
            query = query.where(FunctionPoint.priority == priority)
        if status_filter:
            print_info(f"状态: {status_filter}", "FPAPI")
            query = query.where(FunctionPoint.status == status_filter)

        query = query.offset(skip).limit(limit)
        fps = session.exec(query).all()

        print_step_end(f"{operation}", f"共 {len(fps)} 个", "FPAPI")
        logger.info(f"Listed function points: {len(fps)} items")

        return [FunctionPointRead.from_orm_with_enum(fp) for fp in fps]

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "FPAPI")
        logger.error(f"Failed to list function points: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{fp_id}", response_model=FunctionPointRead)
async def get_function_point(
    fp_id: UUID,
    session: Session = Depends(get_session)
) -> FunctionPoint:
    operation = "获取功能点详情"
    print_step_start(f"{operation}: {fp_id}", "FPAPI")

    try:
        fp = session.get(FunctionPoint, fp_id)
        if not fp:
            print_warning(f"功能点不存在: {fp_id}", "FPAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Function Point {fp_id} not found"
            )

        print_step_end(f"{operation}", f"名称: {fp.name}", "FPAPI")
        logger.info(f"Get function point: {fp_id}")

        return fp

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "FPAPI")
        logger.error(f"Failed to get function point {fp_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{fp_id}", response_model=FunctionPointRead)
async def update_function_point(
    fp_id: UUID,
    fp_data: FunctionPointUpdate,
    session: Session = Depends(get_session)
) -> FunctionPoint:
    operation = "更新功能点"
    print_step_start(f"{operation}: {fp_id}", "FPAPI")

    try:
        fp = session.get(FunctionPoint, fp_id)
        if not fp:
            print_warning(f"功能点不存在: {fp_id}", "FPAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Function Point {fp_id} not found"
            )

        update_data = fp_data.model_dump(exclude_unset=True)
        print_info(f"更新字段: {list(update_data.keys())}", "FPAPI")

        for key, value in update_data.items():
            setattr(fp, key, value)

        fp.updated_at = datetime.utcnow()

        session.add(fp)
        session.commit()
        session.refresh(fp)

        print_step_end(f"{operation}", "成功", "FPAPI")
        logger.info(f"Function point updated: {fp_id}")

        return fp

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "FPAPI")
        logger.error(f"Failed to update function point {fp_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{fp_id}/approve", response_model=FunctionPointRead)
async def approve_function_point(
    fp_id: UUID,
    session: Session = Depends(get_session)
) -> FunctionPoint:
    operation = "审批功能点"
    print_step_start(f"{operation}: {fp_id}", "FPAPI")

    try:
        fp = session.get(FunctionPoint, fp_id)
        if not fp:
            print_warning(f"功能点不存在: {fp_id}", "FPAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Function Point {fp_id} not found"
            )

        print_info(f"功能点名称: {fp.name}", "FPAPI")
        fp.status = FPStatus.APPROVED
        fp.updated_at = datetime.utcnow()

        session.add(fp)
        session.commit()
        session.refresh(fp)

        print_step_end(f"{operation}", "已审批", "FPAPI")
        logger.info(f"Function point approved: {fp_id}")

        return fp

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "FPAPI")
        logger.error(f"Failed to approve function point {fp_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{fp_id}/reject", response_model=FunctionPointRead)
async def reject_function_point(
    fp_id: UUID,
    session: Session = Depends(get_session)
) -> FunctionPoint:
    operation = "拒绝功能点"
    print_step_start(f"{operation}: {fp_id}", "FPAPI")

    try:
        fp = session.get(FunctionPoint, fp_id)
        if not fp:
            print_warning(f"功能点不存在: {fp_id}", "FPAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Function Point {fp_id} not found"
            )

        print_info(f"功能点名称: {fp.name}", "FPAPI")
        fp.status = FPStatus.REJECTED
        fp.updated_at = datetime.utcnow()

        session.add(fp)
        session.commit()
        session.refresh(fp)

        print_step_end(f"{operation}", "已拒绝", "FPAPI")
        logger.info(f"Function point rejected: {fp_id}")

        return fp

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "FPAPI")
        logger.error(f"Failed to reject function point {fp_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{fp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_function_point(
    fp_id: UUID,
    session: Session = Depends(get_session)
):
    operation = "删除功能点"
    print_step_start(f"{operation}: {fp_id}", "FPAPI")

    try:
        fp = session.get(FunctionPoint, fp_id)
        if not fp:
            print_warning(f"功能点不存在: {fp_id}", "FPAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Function Point {fp_id} not found"
            )

        print_info(f"删除功能点: {fp.name}", "FPAPI")

        session.delete(fp)
        session.commit()

        print_step_end(f"{operation}", "成功", "FPAPI")
        logger.info(f"Function point deleted: {fp_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "FPAPI")
        logger.error(f"Failed to delete function point {fp_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
