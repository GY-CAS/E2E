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
    TestCase, TestCaseCreate, TestCaseUpdate, TestCaseRead, TestStepSchema,
    TCStatus, TestType, Priority
)

router = APIRouter(prefix="/test-cases", tags=["Test Cases"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=TestCaseRead, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    tc_data: TestCaseCreate,
    session: Session = Depends(get_session)
) -> TestCase:
    operation = "创建测试用例"
    print_step_start(f"{operation}: {tc_data.title}", "TCAPI")

    try:
        tc_dict = tc_data.model_dump()
        test_steps = tc_dict.pop("test_steps", [])
        tags = tc_dict.pop("tags", [])
        test_data = tc_dict.pop("test_data", None)

        print_info(f"项目ID: {tc_dict.get('project_id')}, 测试类型: {tc_dict.get('test_type')}", "TCAPI")

        tc = TestCase(**tc_dict)
        tc.set_test_steps([s.model_dump() if hasattr(s, 'model_dump') else s for s in test_steps])
        tc.set_tags(tags)
        if test_data:
            tc.test_data = json.dumps(test_data, ensure_ascii=False)

        session.add(tc)
        session.commit()
        session.refresh(tc)

        print_step_end(f"{operation}", f"成功，ID: {tc.id}", "TCAPI")
        logger.info(f"Test case created: {tc.id} - {tc.title}")

        return TestCaseRead.from_orm_with_enum(tc)

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "TCAPI")
        logger.error(f"Failed to create test case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[TestCaseRead], status_code=status.HTTP_201_CREATED)
async def create_test_cases_batch(
    tc_list: List[TestCaseCreate],
    session: Session = Depends(get_session)
) -> List[TestCase]:
    operation = "批量创建测试用例"
    print_step_start(f"{operation}: {len(tc_list)} 个", "TCAPI")

    try:
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

        print_info(f"创建 {len(tcs)} 个测试用例", "TCAPI")

        session.commit()
        for tc in tcs:
            session.refresh(tc)

        print_step_end(f"{operation}", f"成功创建 {len(tcs)} 个", "TCAPI")
        logger.info(f"Batch created {len(tcs)} test cases")

        return [TestCaseRead.from_orm_with_enum(tc) for tc in tcs]

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "TCAPI")
        logger.error(f"Failed to batch create test cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[TestCaseRead])
async def list_test_cases(
    project_id: str = None,
    function_point_id: str = None,
    test_type: TestType = None,
    priority: Priority = None,
    status_filter: TCStatus = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    operation = "获取测试用例列表"
    print_step_start(f"{operation}", "TCAPI")

    try:
        query = select(TestCase)

        if project_id:
            print_info(f"项目ID: {project_id}", "TCAPI")
            try:
                query = query.where(TestCase.project_id == UUID(project_id))
            except ValueError:
                pass
        if function_point_id:
            print_info(f"功能点ID: {function_point_id}", "TCAPI")
            try:
                query = query.where(TestCase.function_point_id == UUID(function_point_id))
            except ValueError:
                pass
        if test_type:
            print_info(f"测试类型: {test_type}", "TCAPI")
            query = query.where(TestCase.test_type == test_type)
        if priority:
            print_info(f"优先级: {priority}", "TCAPI")
            query = query.where(TestCase.priority == priority)
        if status_filter:
            print_info(f"状态: {status_filter}", "TCAPI")
            query = query.where(TestCase.status == status_filter)

        query = query.offset(skip).limit(limit)
        tcs = session.exec(query).all()

        print_step_end(f"{operation}", f"共 {len(tcs)} 个", "TCAPI")
        logger.info(f"Listed test cases: {len(tcs)} items")

        return [TestCaseRead.from_orm_with_enum(tc) for tc in tcs]

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "TCAPI")
        logger.error(f"Failed to list test cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tc_id}", response_model=TestCaseRead)
async def get_test_case(
    tc_id: UUID,
    session: Session = Depends(get_session)
) -> TestCase:
    operation = "获取测试用例详情"
    print_step_start(f"{operation}: {tc_id}", "TCAPI")

    try:
        tc = session.get(TestCase, tc_id)
        if not tc:
            print_warning(f"测试用例不存在: {tc_id}", "TCAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test Case {tc_id} not found"
            )

        print_step_end(f"{operation}", f"标题: {tc.title}", "TCAPI")
        logger.info(f"Get test case: {tc_id}")

        return TestCaseRead.from_orm_with_enum(tc)

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "TCAPI")
        logger.error(f"Failed to get test case {tc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{tc_id}", response_model=TestCaseRead)
async def update_test_case(
    tc_id: UUID,
    tc_data: TestCaseUpdate,
    session: Session = Depends(get_session)
) -> TestCase:
    operation = "更新测试用例"
    print_step_start(f"{operation}: {tc_id}", "TCAPI")

    try:
        tc = session.get(TestCase, tc_id)
        if not tc:
            print_warning(f"测试用例不存在: {tc_id}", "TCAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test Case {tc_id} not found"
            )

        try:
            update_data = tc_data.model_dump(exclude_unset=True)
            print_info(f"更新字段: {list(update_data.keys())}", "TCAPI")
            logger.info(f"Update data: {update_data}")

            if "test_steps" in update_data:
                steps = update_data.pop("test_steps")
                if steps:
                    tc.set_test_steps([s.model_dump() if hasattr(s, 'model_dump') else s for s in steps])
                else:
                    tc.set_test_steps([])

            if "tags" in update_data:
                tags = update_data.pop("tags")
                tc.set_tags(tags or [])

            if "test_data" in update_data:
                test_data = update_data.pop("test_data")
                tc.test_data = json.dumps(test_data, ensure_ascii=False) if test_data else None

            for key, value in update_data.items():
                setattr(tc, key, value)

            tc.updated_at = datetime.utcnow()

            session.add(tc)
            session.commit()
            session.refresh(tc)

            print_step_end(f"{operation}", "成功", "TCAPI")
            logger.info(f"Test case updated: {tc_id}")

            return TestCaseRead.from_orm_with_enum(tc)
        except Exception as e:
            print_error(f"更新数据失败: {str(e)[:50]}", "TCAPI")
            logger.error(f"Failed to update test case: {e}", exc_info=True)
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新失败: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "TCAPI")
        logger.error(f"Failed to update test case {tc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tc_id}/approve", response_model=TestCaseRead)
async def approve_test_case(
    tc_id: UUID,
    session: Session = Depends(get_session)
) -> TestCase:
    operation = "审批测试用例"
    print_step_start(f"{operation}: {tc_id}", "TCAPI")

    try:
        tc = session.get(TestCase, tc_id)
        if not tc:
            print_warning(f"测试用例不存在: {tc_id}", "TCAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test Case {tc_id} not found"
            )

        print_info(f"测试用例标题: {tc.title}", "TCAPI")
        tc.status = TCStatus.APPROVED
        tc.updated_at = datetime.utcnow()

        session.add(tc)
        session.commit()
        session.refresh(tc)

        print_step_end(f"{operation}", "已审批", "TCAPI")
        logger.info(f"Test case approved: {tc_id}")

        return TestCaseRead.from_orm_with_enum(tc)

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "TCAPI")
        logger.error(f"Failed to approve test case {tc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tc_id}/reject", response_model=TestCaseRead)
async def reject_test_case(
    tc_id: UUID,
    session: Session = Depends(get_session)
) -> TestCase:
    operation = "拒绝测试用例"
    print_step_start(f"{operation}: {tc_id}", "TCAPI")

    try:
        tc = session.get(TestCase, tc_id)
        if not tc:
            print_warning(f"测试用例不存在: {tc_id}", "TCAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test Case {tc_id} not found"
            )

        print_info(f"测试用例标题: {tc.title}", "TCAPI")
        tc.status = TCStatus.REJECTED
        tc.updated_at = datetime.utcnow()

        session.add(tc)
        session.commit()
        session.refresh(tc)

        print_step_end(f"{operation}", "已拒绝", "TCAPI")
        logger.info(f"Test case rejected: {tc_id}")

        return TestCaseRead.from_orm_with_enum(tc)

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "TCAPI")
        logger.error(f"Failed to reject test case {tc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    tc_id: UUID,
    session: Session = Depends(get_session)
):
    operation = "删除测试用例"
    print_step_start(f"{operation}: {tc_id}", "TCAPI")

    try:
        tc = session.get(TestCase, tc_id)
        if not tc:
            print_warning(f"测试用例不存在: {tc_id}", "TCAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test Case {tc_id} not found"
            )

        print_info(f"删除测试用例: {tc.title}", "TCAPI")

        session.delete(tc)
        session.commit()

        print_step_end(f"{operation}", "成功", "TCAPI")
        logger.info(f"Test case deleted: {tc_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "TCAPI")
        logger.error(f"Failed to delete test case {tc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
