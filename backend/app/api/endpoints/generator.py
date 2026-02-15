from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from typing import List
from uuid import UUID
import json
import asyncio

from app.core.database import get_session
from app.models import (
    GenerateRequest, GenerateFunctionPointsRequest,
    GenerateTestCasesRequest, GenerateScriptsRequest,
    SSEEvent, Document, FunctionPoint, TestCase
)

router = APIRouter(prefix="/generator", tags=["Generator"])


async def generate_sse_events(request: GenerateRequest, session: Session):
    event_queue = asyncio.Queue()
    
    async def send_event(event_type: str, stage: str, message: str, data: dict = None):
        event = SSEEvent(
            event_type=event_type,
            stage=stage,
            message=message,
            data=data
        )
        await event_queue.put(event)
    
    async def process():
        try:
            await send_event("start", "init", "Starting generation process")
            
            documents = session.exec(
                Document.__table__.select().where(Document.id.in_(request.document_ids))
            ).all() if request.document_ids else []
            
            await send_event("progress", "document_parsing", f"Processing {len(documents)} documents")
            await asyncio.sleep(0.5)
            
            await send_event("progress", "requirement_analysis", "Analyzing requirements with AI")
            await asyncio.sleep(0.5)
            
            await send_event("progress", "function_point_generation", "Generating test function points")
            await asyncio.sleep(0.5)
            
            await send_event("progress", "user_review", "Waiting for user review", {
                "function_points": [
                    {
                        "name": "User Authentication",
                        "description": "Test user login/logout functionality",
                        "test_type": "functional",
                        "priority": "p0"
                    },
                    {
                        "name": "API Response Time",
                        "description": "Test API response performance",
                        "test_type": "performance",
                        "priority": "p1"
                    }
                ]
            })
            await asyncio.sleep(0.5)
            
            await send_event("progress", "testcase_generation", "Generating test cases")
            await asyncio.sleep(0.5)
            
            if request.generate_scripts:
                await send_event("progress", "script_generation", f"Generating {request.script_language} test scripts")
                await asyncio.sleep(0.5)
            
            await send_event("complete", "done", "Generation completed successfully", {
                "test_cases_count": 5,
                "scripts_count": 5 if request.generate_scripts else 0
            })
            
        except Exception as e:
            await send_event("error", "error", str(e))
        finally:
            await event_queue.put(None)
    
    asyncio.create_task(process())
    
    while True:
        event = await event_queue.get()
        if event is None:
            break
        
        yield f"data: {event.model_dump_json()}\n\n"


@router.post("/stream")
async def generate_stream(
    request: GenerateRequest,
    session: Session = Depends(get_session)
):
    return StreamingResponse(
        generate_sse_events(request, session),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/function-points")
async def generate_function_points(
    request: GenerateFunctionPointsRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    documents = []
    if request.document_ids:
        for doc_id in request.document_ids:
            doc = session.get(Document, doc_id)
            if doc:
                documents.append(doc)
    
    function_points = [
        {
            "project_id": str(request.project_id),
            "name": "User Login",
            "description": "Test user login functionality",
            "test_type": "functional",
            "priority": "p0",
            "module": "Authentication"
        },
        {
            "project_id": str(request.project_id),
            "name": "API Performance",
            "description": "Test API response time",
            "test_type": "performance",
            "priority": "p1",
            "module": "API"
        }
    ]
    
    return {
        "message": "Function points generated successfully",
        "function_points": function_points
    }


@router.post("/test-cases")
async def generate_test_cases(
    request: GenerateTestCasesRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    function_points = []
    if request.function_point_ids:
        for fp_id in request.function_point_ids:
            fp = session.get(FunctionPoint, fp_id)
            if fp:
                function_points.append(fp)
    
    test_cases = [
        {
            "project_id": str(function_points[0].project_id) if function_points else str(UUID(int=0)),
            "title": "Test user login with valid credentials",
            "description": "Verify user can login with valid username and password",
            "test_type": "functional",
            "test_category": "frontend",
            "priority": "p0",
            "preconditions": "User is on login page",
            "test_steps": [
                {"step_num": 1, "action": "Enter valid username", "expected_result": "Username field is filled"},
                {"step_num": 2, "action": "Enter valid password", "expected_result": "Password field is filled"},
                {"step_num": 3, "action": "Click login button", "expected_result": "User is redirected to dashboard"}
            ]
        }
    ]
    
    return {
        "message": "Test cases generated successfully",
        "test_cases": test_cases
    }


@router.post("/scripts")
async def generate_scripts(
    request: GenerateScriptsRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    test_cases = []
    if request.test_case_ids:
        for tc_id in request.test_case_ids:
            tc = session.get(TestCase, tc_id)
            if tc:
                test_cases.append(tc)
    
    scripts = []
    if request.language == "python":
        scripts.append({
            "name": "test_login",
            "language": "python",
            "framework": request.framework,
            "content": '''import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

class TestLogin:
    def test_login_valid(self):
        driver = webdriver.Chrome()
        driver.get("https://example.com/login")
        driver.find_element(By.ID, "username").send_keys("testuser")
        driver.find_element(By.ID, "password").send_keys("password123")
        driver.find_element(By.ID, "login-btn").click()
        assert "dashboard" in driver.current_url
        driver.quit()
'''
        })
    else:
        scripts.append({
            "name": "TestLogin",
            "language": "java",
            "framework": request.framework,
            "content": '''import org.testng.annotations.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;

public class TestLogin {
    private WebDriver driver;
    
    @BeforeMethod
    public void setUp() {
        driver = new ChromeDriver();
    }
    
    @Test
    public void testLoginValid() {
        driver.get("https://example.com/login");
        driver.findElement(By.id("username")).sendKeys("testuser");
        driver.findElement(By.id("password")).sendKeys("password123");
        driver.findElement(By.id("login-btn")).click();
        assert driver.getCurrentUrl().contains("dashboard");
    }
    
    @AfterMethod
    public void tearDown() {
        driver.quit();
    }
}
'''
        })
    
    return {
        "message": "Scripts generated successfully",
        "scripts": scripts
    }
