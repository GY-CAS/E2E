from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select, func, delete
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from datetime import datetime

from app.core.database import get_session
from app.core.console_output import (
    print_step_start, print_step_end, print_success, print_error,
    print_warning, print_info, console
)
from app.core.logging_utils import SensitiveDataMasker
from app.models import (
    Project, ProjectCreate, ProjectUpdate, ProjectRead, ProjectDetail,
    ProjectStatus, Document, FunctionPoint, TestCase, TestScript, MindMapNode, DocStatus
)

router = APIRouter(prefix="/projects", tags=["Projects"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    request: Request,
    session: Session = Depends(get_session)
) -> Project:
    operation = "创建项目"
    print_step_start(f"{operation}: {project_data.name}", "ProjectsAPI")

    try:
        project = Project(**project_data.model_dump())

        print_info(f"项目名称: {project.name}, 描述: {project.description[:50] if project.description else '无'}...", "ProjectsAPI")

        session.add(project)
        session.commit()
        session.refresh(project)

        print_step_end(f"{operation}", f"成功，ID: {project.id}", "ProjectsAPI")
        logger.info(f"Project created: {project.id} - {project.name}")

        return project

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ProjectsAPI")
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ProjectRead])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    status_filter: ProjectStatus = None,
    request: Request = None,
    session: Session = Depends(get_session)
) -> List[Project]:
    operation = "获取项目列表"
    print_step_start(f"{operation}", "ProjectsAPI")

    try:
        query = select(Project)
        if status_filter:
            print_info(f"状态过滤: {status_filter}", "ProjectsAPI")
            query = query.where(Project.status == status_filter)

        query = query.offset(skip).limit(limit)
        projects = session.exec(query).all()

        print_step_end(f"{operation}", f"共 {len(projects)} 个项目", "ProjectsAPI")
        logger.info(f"Listed projects: {len(projects)} items")

        return projects

    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ProjectsAPI")
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    request: Request = None,
    session: Session = Depends(get_session)
) -> Project:
    operation = "获取项目详情"
    print_step_start(f"{operation}: {project_id}", "ProjectsAPI")

    try:
        project = session.get(Project, project_id)
        if not project:
            print_warning(f"项目不存在: {project_id}", "ProjectsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        print_step_end(f"{operation}", f"项目名称: {project.name}", "ProjectsAPI")
        logger.info(f"Get project: {project_id}")

        return project

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ProjectsAPI")
        logger.error(f"Failed to get project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: UUID,
    request: Request = None,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    operation = "获取项目统计"
    print_step_start(f"{operation}: {project_id}", "ProjectsAPI")

    try:
        project = session.get(Project, project_id)
        if not project:
            print_warning(f"项目不存在: {project_id}", "ProjectsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        print_info(f"统计项目: {project.name}", "ProjectsAPI")

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

        result = {
            "project_id": str(project_id),
            "project_name": project.name,
            "document_count": doc_count,
            "parsed_document_count": parsed_doc_count,
            "function_point_count": fp_count,
            "test_case_count": tc_count
        }

        print_step_end(f"{operation}",
            f"文档: {doc_count}, 功能点: {fp_count}, 测试用例: {tc_count}", "ProjectsAPI")
        logger.info(f"Project stats for {project_id}: {result}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ProjectsAPI")
        logger.error(f"Failed to get project stats {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/detail", response_model=ProjectDetail)
async def get_project_detail(
    project_id: UUID,
    request: Request = None,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    operation = "获取项目详细信息"
    print_step_start(f"{operation}: {project_id}", "ProjectsAPI")

    try:
        project = session.get(Project, project_id)
        if not project:
            print_warning(f"项目不存在: {project_id}", "ProjectsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        print_info(f"获取项目详情: {project.name}", "ProjectsAPI")

        total_docs = session.exec(
            select(func.count(Document.id)).where(Document.project_id == project_id)
        ).one()

        parsed_docs = session.exec(
            select(func.count(Document.id)).where(
                Document.project_id == project_id,
                Document.status == DocStatus.PARSED
            )
        ).one()

        pending_docs = session.exec(
            select(func.count(Document.id)).where(
                Document.project_id == project_id,
                Document.status == DocStatus.PENDING
            )
        ).one()

        processing_docs = session.exec(
            select(func.count(Document.id)).where(
                Document.project_id == project_id,
                Document.status == DocStatus.PROCESSING
            )
        ).one()

        failed_docs = session.exec(
            select(func.count(Document.id)).where(
                Document.project_id == project_id,
                Document.status == DocStatus.FAILED
            )
        ).one()

        fp_count = session.exec(
            select(func.count(FunctionPoint.id)).where(FunctionPoint.project_id == project_id)
        ).one()

        manual_tc_count = session.exec(
            select(func.count(TestCase.id)).where(
                TestCase.project_id == project_id,
                TestCase.test_category == "manual"
            )
        ).one()

        auto_tc_count = session.exec(
            select(func.count(TestCase.id)).where(
                TestCase.project_id == project_id,
                TestCase.test_category == "auto"
            )
        ).one()

        frontend_tc_count = session.exec(
            select(func.count(TestCase.id)).where(
                TestCase.project_id == project_id,
                TestCase.test_category == "frontend"
            )
        ).one()

        backend_tc_count = session.exec(
            select(func.count(TestCase.id)).where(
                TestCase.project_id == project_id,
                TestCase.test_category == "backend"
            )
        ).one()

        script_count = session.exec(
            select(func.count(TestScript.id)).where(TestScript.project_id == project_id)
        ).one()

        result = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status.value if hasattr(project.status, 'value') else project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "document_stats": {
                "total": total_docs,
                "parsed": parsed_docs,
                "pending": pending_docs,
                "processing": processing_docs,
                "failed": failed_docs
            },
            "function_point_count": fp_count,
            "test_case_stats": {
                "total": manual_tc_count + auto_tc_count,
                "manual": manual_tc_count,
                "auto": auto_tc_count,
                "frontend": frontend_tc_count,
                "backend": backend_tc_count
            },
            "test_script_count": script_count
        }

        print_step_end(f"{operation}",
            f"文档: {total_docs}, 功能点: {fp_count}, 测试用例: {manual_tc_count + auto_tc_count}, 脚本: {script_count}",
            "ProjectsAPI")
        logger.info(f"Project detail for {project_id}: {result}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ProjectsAPI")
        logger.error(f"Failed to get project detail {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    request: Request = None,
    session: Session = Depends(get_session)
) -> Project:
    operation = "更新项目"
    print_step_start(f"{operation}: {project_id}", "ProjectsAPI")

    try:
        project = session.get(Project, project_id)
        if not project:
            print_warning(f"项目不存在: {project_id}", "ProjectsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        update_data = project_data.model_dump(exclude_unset=True)
        print_info(f"更新字段: {list(update_data.keys())}", "ProjectsAPI")

        for key, value in update_data.items():
            setattr(project, key, value)

        project.updated_at = datetime.utcnow()

        session.add(project)
        session.commit()
        session.refresh(project)

        print_step_end(f"{operation}", f"成功", "ProjectsAPI")
        logger.info(f"Project updated: {project_id}")

        return project

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ProjectsAPI")
        logger.error(f"Failed to update project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    request: Request = None,
    session: Session = Depends(get_session)
):
    operation = "删除项目"
    print_step_start(f"{operation}: {project_id}", "ProjectsAPI")

    try:
        project = session.get(Project, project_id)
        if not project:
            print_warning(f"项目不存在: {project_id}", "ProjectsAPI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        print_info(f"删除项目及其所有关联数据: {project.name}", "ProjectsAPI")

        mindmap_count = session.exec(delete(MindMapNode).where(MindMapNode.project_id == project_id)).rowcount
        print_info(f"删除思维导图节点: {mindmap_count} 个", "ProjectsAPI")

        script_count = session.exec(delete(TestScript).where(TestScript.project_id == project_id)).rowcount
        print_info(f"删除测试脚本: {script_count} 个", "ProjectsAPI")

        testcase_count = session.exec(delete(TestCase).where(TestCase.project_id == project_id)).rowcount
        print_info(f"删除测试用例: {testcase_count} 个", "ProjectsAPI")

        fp_count = session.exec(delete(FunctionPoint).where(FunctionPoint.project_id == project_id)).rowcount
        print_info(f"删除功能点: {fp_count} 个", "ProjectsAPI")

        doc_count = session.exec(delete(Document).where(Document.project_id == project_id)).rowcount
        print_info(f"删除文档: {doc_count} 个", "ProjectsAPI")

        session.delete(project)
        session.commit()

        print_step_end(f"{operation}",
            f"成功，删除了 {doc_count} 文档 + {fp_count} 功能点 + {testcase_count} 用例 + {script_count} 脚本 + {mindmap_count} 节点",
            "ProjectsAPI")
        logger.info(f"Project deleted: {project_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        print_error(f"{operation} 失败: {str(e)[:50]}", "ProjectsAPI")
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
