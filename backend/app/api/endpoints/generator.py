from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
import json
import asyncio
import logging

from app.core.database import get_session
from app.models import (
    Document, FunctionPoint, FunctionPointCreate, FunctionPointRead,
    TestCase, TestScript, FPStatus, DocStatus, TestType, Priority
)
from app.services import llm_service, rag_service, milvus_service, document_parser, minio_service

router = APIRouter(prefix="/generator", tags=["Generator"])
logger = logging.getLogger(__name__)


class GenerateFunctionPointsRequest(BaseModel):
    project_id: str
    document_ids: Optional[List[str]] = None
    test_types: List[str] = ["functional"]
    user_requirements: Optional[str] = ""


class GenerateTestCasesRequest(BaseModel):
    project_id: str
    function_point_ids: List[str]


class GenerateScriptsRequest(BaseModel):
    project_id: str
    test_case_ids: List[str]
    language: str = "python"
    framework: str = "pytest"


class RefineFunctionPointRequest(BaseModel):
    function_point: dict
    user_feedback: str
    project_id: Optional[str] = None


class UnderstandRequirementsRequest(BaseModel):
    user_input: str


class FunctionPointSaveItem(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None
    test_type: str = "functional"
    priority: str = "p2"
    module: Optional[str] = None
    acceptance_criteria: Optional[str] = None


@router.post("/understand-requirements")
async def understand_requirements(
    request: UnderstandRequirementsRequest
):
    try:
        analysis = await llm_service.understand_requirements(request.user_input)
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Failed to understand requirements: {e}")
        return {
            "success": False,
            "error": str(e),
            "analysis": None
        }


def parse_test_type(test_type: str) -> TestType:
    mapping = {
        "functional": TestType.FUNCTIONAL,
        "performance": TestType.PERFORMANCE,
        "security": TestType.SECURITY,
        "reliability": TestType.RELIABILITY
    }
    return mapping.get(test_type.lower(), TestType.FUNCTIONAL)


def parse_priority(priority: str) -> Priority:
    mapping = {
        "p0": Priority.P0,
        "p1": Priority.P1,
        "p2": Priority.P2,
        "p3": Priority.P3,
        "p4": Priority.P4
    }
    return mapping.get(priority.lower(), Priority.P2)


@router.post("/function-points")
async def generate_function_points(
    request: GenerateFunctionPointsRequest,
    session: Session = Depends(get_session)
):
    logger.info(f"Generating function points for project {request.project_id}")
    
    try:
        requirements_analysis = None
        if request.user_requirements:
            requirements_analysis = await llm_service.understand_requirements(request.user_requirements)
        
        document_context = await rag_service.retrieve_for_function_points(
            project_id=request.project_id,
            user_requirements=request.user_requirements or "生成测试功能点",
            document_ids=request.document_ids
        )
        
        if not document_context:
            document_content = await rag_service.get_document_content(
                session=session,
                project_id=request.project_id,
                document_ids=request.document_ids
            )
            document_context = document_content[:4000] if document_content else ""
        
        function_points = await llm_service.generate_function_points(
            user_requirements=request.user_requirements or "根据文档内容生成测试功能点",
            document_context=document_context,
            test_types=request.test_types,
            requirements_analysis=requirements_analysis
        )
        
        formatted_fps = []
        for fp in function_points:
            formatted_fp = {
                "project_id": request.project_id,
                "name": fp.get("name", "未命名功能点"),
                "description": fp.get("description", ""),
                "test_type": fp.get("test_type", "functional"),
                "priority": fp.get("priority", "p2"),
                "module": fp.get("module", ""),
                "acceptance_criteria": fp.get("acceptance_criteria", ""),
                "status": "pending"
            }
            formatted_fps.append(formatted_fp)
        
        logger.info(f"Generated {len(formatted_fps)} function points")
        
        return {
            "success": True,
            "message": "功能点生成成功",
            "function_points": formatted_fps,
            "requirements_analysis": requirements_analysis
        }
        
    except Exception as e:
        logger.error(f"Error generating function points: {e}")
        return {
            "success": False,
            "message": f"生成失败: {str(e)}",
            "function_points": []
        }


@router.post("/function-points/save")
async def save_function_points(
    function_points: List[FunctionPointSaveItem],
    session: Session = Depends(get_session)
):
    logger.info(f"Saving {len(function_points)} function points")
    saved_fps = []
    
    try:
        for fp_data in function_points:
            fp = FunctionPoint(
                project_id=UUID(fp_data.project_id),
                name=fp_data.name,
                description=fp_data.description,
                test_type=parse_test_type(fp_data.test_type),
                priority=parse_priority(fp_data.priority),
                module=fp_data.module,
                acceptance_criteria=fp_data.acceptance_criteria,
                status=FPStatus.PENDING
            )
            session.add(fp)
            saved_fps.append(fp)
        
        session.commit()
        
        for fp in saved_fps:
            session.refresh(fp)
        
        logger.info(f"Successfully saved {len(saved_fps)} function points")
        
        from app.models.schemas import FunctionPointRead
        serialized_fps = [FunctionPointRead.from_orm_with_enum(fp) for fp in saved_fps]
        
        return {
            "success": True,
            "message": f"成功保存 {len(saved_fps)} 个功能点",
            "function_points": serialized_fps
        }
    except Exception as e:
        logger.error(f"Error saving function points: {e}")
        session.rollback()
        return {
            "success": False,
            "message": f"保存失败: {str(e)}",
            "function_points": []
        }


@router.post("/function-points/refine")
async def refine_function_point(
    request: RefineFunctionPointRequest,
    session: Session = Depends(get_session)
):
    try:
        context = ""
        if request.project_id:
            context = await rag_service.retrieve_relevant_context(
                project_id=request.project_id,
                query=request.function_point.get("name", ""),
                top_k=3
            )
        
        refined_fp = await llm_service.refine_function_point(
            function_point=request.function_point,
            user_feedback=request.user_feedback,
            context=context
        )
        
        return {
            "success": True,
            "message": "功能点优化成功",
            "function_point": refined_fp
        }
    except Exception as e:
        logger.error(f"Failed to refine: {e}")
        return {
            "success": False,
            "message": f"优化失败: {str(e)}",
            "function_point": request.function_point
        }


@router.post("/test-cases")
async def generate_test_cases(
    request: GenerateTestCasesRequest,
    session: Session = Depends(get_session)
):
    import asyncio
    
    logger.info(f"Generating test cases for project {request.project_id}")
    logger.info(f"Function point IDs: {request.function_point_ids}")
    
    function_points = []
    if request.function_point_ids:
        for fp_id in request.function_point_ids:
            try:
                fp = session.get(FunctionPoint, fp_id)
                if fp:
                    function_points.append(fp)
                    logger.info(f"Found function point: {fp.name}")
                else:
                    logger.warning(f"Function point not found: {fp_id}")
            except Exception as e:
                logger.error(f"Error getting function point {fp_id}: {e}")
    
    if not function_points:
        logger.warning("No function points found")
        return {
            "success": False,
            "message": "未找到功能点",
            "test_cases": []
        }
    
    async def generate_single_test_case(fp):
        try:
            logger.info(f"Generating test case for FP: {fp.name}")
            
            document_context = await rag_service.retrieve_for_test_case(
                project_id=str(fp.project_id),
                function_point={
                    "name": fp.name,
                    "description": fp.description,
                    "acceptance_criteria": fp.acceptance_criteria
                }
            )
            
            logger.info(f"Document context length for {fp.name}: {len(document_context) if document_context else 0}")
            
            tc_data = await llm_service.generate_test_case(
                function_point={
                    "id": str(fp.id),
                    "project_id": str(fp.project_id),
                    "name": fp.name,
                    "description": fp.description,
                    "test_type": fp.test_type.value if hasattr(fp.test_type, 'value') else str(fp.test_type),
                    "priority": fp.priority.value if hasattr(fp.priority, 'value') else str(fp.priority),
                    "module": fp.module,
                    "acceptance_criteria": fp.acceptance_criteria
                },
                document_context=document_context
            )
            
            logger.info(f"Generated test case: {tc_data.get('title', 'No title')}")
            return tc_data
            
        except Exception as e:
            logger.error(f"Failed to generate test case for FP {fp.id}: {e}", exc_info=True)
            return {
                "title": f"测试_{fp.name}",
                "description": fp.description or "",
                "test_type": fp.test_type.value if hasattr(fp, 'test_type') and hasattr(fp.test_type, 'value') else "functional",
                "test_category": "functional",
                "priority": fp.priority.value if hasattr(fp, 'priority') and hasattr(fp.priority, 'value') else "p2",
                "preconditions": "",
                "test_steps": [],
                "expected_results": fp.acceptance_criteria or "",
                "function_point_id": str(fp.id),
                "project_id": str(fp.project_id),
                "error": str(e)
            }
    
    logger.info(f"Starting parallel generation for {len(function_points)} function points")
    
    tasks = [generate_single_test_case(fp) for fp in function_points]
    test_cases = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_test_cases = []
    for i, tc in enumerate(test_cases):
        if isinstance(tc, Exception):
            logger.error(f"Exception in task {i}: {tc}")
        elif tc:
            valid_test_cases.append(tc)
    
    logger.info(f"Generated {len(valid_test_cases)} test cases out of {len(function_points)} function points")
    
    return {
        "success": True,
        "message": f"成功生成 {len(valid_test_cases)} 个测试用例",
        "test_cases": valid_test_cases
    }


@router.post("/test-cases/save")
async def save_test_cases(
    test_cases: List[dict],
    session: Session = Depends(get_session)
):
    import json
    from uuid import UUID
    
    saved_tcs = []
    
    try:
        for tc_data in test_cases:
            project_id = tc_data.get("project_id")
            function_point_id = tc_data.get("function_point_id")
            
            if isinstance(project_id, str):
                try:
                    project_id = UUID(project_id)
                except ValueError:
                    project_id = None
            
            if isinstance(function_point_id, str):
                try:
                    function_point_id = UUID(function_point_id)
                except ValueError:
                    function_point_id = None
            
            test_steps = tc_data.get("test_steps", [])
            if isinstance(test_steps, list):
                test_steps = json.dumps(test_steps, ensure_ascii=False)
            elif not test_steps:
                test_steps = "[]"
            
            tags = tc_data.get("tags", [])
            if isinstance(tags, list):
                tags = json.dumps(tags, ensure_ascii=False)
            elif not tags:
                tags = None
            
            test_data = tc_data.get("test_data")
            if isinstance(test_data, dict):
                test_data = json.dumps(test_data, ensure_ascii=False)
            
            tc = TestCase(
                project_id=project_id,
                function_point_id=function_point_id,
                title=tc_data.get("title", "未命名测试用例"),
                description=tc_data.get("description"),
                test_type=tc_data.get("test_type", "functional"),
                test_category=tc_data.get("test_category", "functional"),
                priority=tc_data.get("priority", "p2"),
                preconditions=tc_data.get("preconditions"),
                test_steps=test_steps,
                expected_results=tc_data.get("expected_results"),
                test_data=test_data,
                tags=tags,
                status="draft"
            )
            session.add(tc)
            saved_tcs.append(tc)
        
        session.commit()
        
        for tc in saved_tcs:
            session.refresh(tc)
        
        from app.models.schemas import TestCaseRead
        serialized_tcs = [TestCaseRead.from_orm_with_enum(tc) for tc in saved_tcs]
        
        return {
            "success": True,
            "message": f"成功保存 {len(saved_tcs)} 个测试用例",
            "test_cases": serialized_tcs
        }
    except Exception as e:
        logger.error(f"Failed to save test cases: {e}", exc_info=True)
        session.rollback()
        return {
            "success": False,
            "message": f"保存失败: {str(e)}",
            "test_cases": []
        }


@router.post("/scripts")
async def generate_scripts(
    request: GenerateScriptsRequest,
    session: Session = Depends(get_session)
):
    test_cases = []
    if request.test_case_ids:
        for tc_id in request.test_case_ids:
            tc = session.get(TestCase, tc_id)
            if tc:
                test_cases.append(tc)
    
    if not test_cases:
        return {
            "success": False,
            "message": "未找到测试用例",
            "scripts": []
        }
    
    scripts = []
    
    for tc in test_cases:
        try:
            script_content = await llm_service.generate_test_script(
                test_case={
                    "title": tc.title,
                    "description": tc.description,
                    "preconditions": tc.preconditions,
                    "test_steps": tc.test_steps,
                    "expected_results": tc.expected_results
                },
                language=request.language,
                framework=request.framework
            )
            
            scripts.append({
                "project_id": str(tc.project_id),
                "test_case_id": str(tc.id),
                "name": f"test_{tc.title.lower().replace(' ', '_')[:30]}",
                "language": request.language,
                "framework": request.framework,
                "content": script_content
            })
            
        except Exception as e:
            logger.error(f"Failed to generate script for TC {tc.id}: {e}")
    
    return {
        "success": True,
        "message": "测试脚本生成成功",
        "scripts": scripts
    }


@router.post("/scripts/save")
async def save_scripts(
    scripts: List[dict],
    session: Session = Depends(get_session)
):
    saved_scripts = []
    
    for script_data in scripts:
        script = TestScript(
            project_id=script_data.get("project_id"),
            test_case_id=script_data.get("test_case_id"),
            name=script_data.get("name", "未命名脚本"),
            language=script_data.get("language", "python"),
            framework=script_data.get("framework", "pytest"),
            content=script_data.get("content", ""),
            dependencies=script_data.get("dependencies", []),
            status="draft"
        )
        session.add(script)
        saved_scripts.append(script)
    
    session.commit()
    
    return {
        "success": True,
        "message": f"成功保存 {len(saved_scripts)} 个测试脚本",
        "scripts": saved_scripts
    }


@router.get("/vector-stats/{project_id}")
async def get_vector_stats(project_id: str):
    stats = milvus_service.get_collection_stats(project_id)
    return stats
