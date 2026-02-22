from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
import json


class DocType(str, Enum):
    REQUIREMENT = "requirement"
    SPEC = "spec"
    DESIGN = "design"
    API = "api"
    MANUAL = "manual"
    IMAGE = "image"


class TestType(str, Enum):
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    RELIABILITY = "reliability"


class Priority(str, Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"


class TestStepSchema(BaseModel):
    step_num: int
    action: str
    expected_result: str
    test_data: Optional[Dict[str, Any]] = None


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    project_id: UUID
    name: str = Field(..., max_length=255)
    doc_type: DocType = DocType.REQUIREMENT


class DocumentRead(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    doc_type: DocType
    file_path: str
    file_size: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FunctionPointCreate(BaseModel):
    project_id: UUID
    document_id: Optional[UUID] = None
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    test_type: TestType = TestType.FUNCTIONAL
    priority: Priority = Priority.P2
    module: Optional[str] = None
    acceptance_criteria: Optional[str] = None


class FunctionPointUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    test_type: Optional[TestType] = None
    priority: Optional[Priority] = None
    module: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    status: Optional[str] = None


class FunctionPointRead(BaseModel):
    id: UUID
    project_id: UUID
    document_id: Optional[UUID]
    name: str
    description: Optional[str]
    test_type: str
    priority: str
    module: Optional[str]
    acceptance_criteria: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_enum(cls, obj):
        data = {
            'id': obj.id,
            'project_id': obj.project_id,
            'document_id': obj.document_id,
            'name': obj.name,
            'description': obj.description,
            'test_type': obj.test_type.value if hasattr(obj.test_type, 'value') else obj.test_type,
            'priority': obj.priority.value if hasattr(obj.priority, 'value') else obj.priority,
            'module': obj.module,
            'acceptance_criteria': obj.acceptance_criteria,
            'status': obj.status.value if hasattr(obj.status, 'value') else obj.status,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at
        }
        return cls(**data)


class TestCaseCreate(BaseModel):
    project_id: UUID
    function_point_id: Optional[UUID] = None
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    test_type: TestType = TestType.FUNCTIONAL
    test_category: str = "frontend"
    priority: Priority = Priority.P2
    preconditions: Optional[str] = None
    test_steps: List[TestStepSchema] = []
    expected_results: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None
    tags: List[str] = []


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    test_type: Optional[TestType] = None
    test_category: Optional[str] = None
    priority: Optional[Priority] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[TestStepSchema]] = None
    expected_results: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class TestCaseRead(BaseModel):
    id: UUID
    project_id: UUID
    function_point_id: Optional[UUID]
    title: str
    description: Optional[str]
    test_type: str
    test_category: str
    priority: str
    preconditions: Optional[str]
    test_steps: List[TestStepSchema]
    expected_results: Optional[str]
    test_data: Optional[Dict[str, Any]]
    tags: List[str]
    status: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_enum(cls, obj):
        data = {
            'id': obj.id,
            'project_id': obj.project_id,
            'function_point_id': obj.function_point_id,
            'title': obj.title,
            'description': obj.description,
            'test_type': obj.test_type.value if hasattr(obj.test_type, 'value') else obj.test_type,
            'test_category': obj.test_category,
            'priority': obj.priority.value if hasattr(obj.priority, 'value') else obj.priority,
            'preconditions': obj.preconditions,
            'test_steps': obj.get_test_steps() if hasattr(obj, 'get_test_steps') else [],
            'expected_results': obj.expected_results,
            'test_data': json.loads(obj.test_data) if obj.test_data else None,
            'tags': obj.get_tags() if hasattr(obj, 'get_tags') else [],
            'status': obj.status.value if hasattr(obj.status, 'value') else obj.status,
            'version': obj.version,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at
        }
        return cls(**data)


class TestScriptCreate(BaseModel):
    project_id: UUID
    test_case_id: Optional[UUID] = None
    name: str = Field(..., max_length=255)
    language: str = "python"
    framework: str = "pytest"
    content: str = ""
    dependencies: List[str] = []


class TestScriptUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    dependencies: Optional[List[str]] = None
    status: Optional[str] = None


class TestScriptRead(BaseModel):
    id: UUID
    project_id: UUID
    test_case_id: Optional[UUID]
    name: str
    language: str
    framework: str
    content: str
    file_path: Optional[str]
    dependencies: List[str]
    status: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    project_id: UUID
    document_ids: List[UUID] = []
    test_types: List[TestType] = [TestType.FUNCTIONAL]
    generate_scripts: bool = False
    script_language: str = "python"


class GenerateFunctionPointsRequest(BaseModel):
    project_id: UUID
    document_ids: List[UUID]
    test_types: List[TestType] = [TestType.FUNCTIONAL]


class GenerateTestCasesRequest(BaseModel):
    project_id: UUID
    function_point_ids: List[UUID]


class GenerateScriptsRequest(BaseModel):
    project_id: UUID
    test_case_ids: List[UUID]
    language: str = "python"
    framework: str = "pytest"


class MindMapNodeCreate(BaseModel):
    project_id: UUID
    test_case_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    text: str = Field(..., max_length=500)
    node_type: str = "module"
    position: Dict[str, float] = {"x": 0, "y": 0}
    style: Dict[str, Any] = {}


class MindMapNodeRead(BaseModel):
    id: UUID
    project_id: UUID
    test_case_id: Optional[UUID]
    parent_id: Optional[UUID]
    text: str
    node_type: str
    position: Dict[str, float]
    style: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequirementAnalysis(BaseModel):
    business_goal: str
    core_modules: List[str]
    business_flows: List[Dict[str, Any]]
    data_entities: List[str]
    dependencies: List[Dict[str, Any]]
    boundary_conditions: List[str]
    exception_scenarios: List[str]


class FunctionPointList(BaseModel):
    function_points: List[FunctionPointCreate]


class TestCaseList(BaseModel):
    test_cases: List[TestCaseCreate]


class SSEEvent(BaseModel):
    event_type: str
    stage: str
    message: str
    data: Optional[Dict[str, Any]] = None
