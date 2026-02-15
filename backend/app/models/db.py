from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
import json


class DocType(str, Enum):
    REQUIREMENT = "requirement"
    SPEC = "spec"
    DESIGN = "design"
    API = "api"
    MANUAL = "manual"
    IMAGE = "image"


class DocStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PARSED = "parsed"
    FAILED = "failed"


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


class FPStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TCStatus(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ScriptLanguage(str, Enum):
    PYTHON = "python"
    JAVA = "java"


class ScriptStatus(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class NodeType(str, Enum):
    ROOT = "root"
    MODULE = "module"
    TESTCASE = "testcase"
    STEP = "step"


class Project(SQLModel, table=True):
    __tablename__ = "projects"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None)
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    documents: List["Document"] = Relationship(back_populates="project")
    function_points: List["FunctionPoint"] = Relationship(back_populates="project")
    test_cases: List["TestCase"] = Relationship(back_populates="project")
    test_scripts: List["TestScript"] = Relationship(back_populates="project")
    mind_map_nodes: List["MindMapNode"] = Relationship(back_populates="project")


class Document(SQLModel, table=True):
    __tablename__ = "documents"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    name: str = Field(max_length=255)
    doc_type: DocType = Field(default=DocType.REQUIREMENT)
    file_path: str = Field(max_length=500)
    file_size: int = Field(default=0)
    status: DocStatus = Field(default=DocStatus.PENDING)
    parsed_content: Optional[str] = Field(default=None)
    vector_ids: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    project: Optional[Project] = Relationship(back_populates="documents")
    function_points: List["FunctionPoint"] = Relationship(back_populates="document")
    
    def get_vector_ids(self) -> List[str]:
        if self.vector_ids:
            return json.loads(self.vector_ids)
        return []
    
    def set_vector_ids(self, ids: List[str]):
        self.vector_ids = json.dumps(ids)


class FunctionPoint(SQLModel, table=True):
    __tablename__ = "function_points"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    document_id: Optional[UUID] = Field(default=None, foreign_key="documents.id")
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None)
    test_type: TestType = Field(default=TestType.FUNCTIONAL)
    priority: Priority = Field(default=Priority.P2)
    module: Optional[str] = Field(default=None, max_length=100)
    acceptance_criteria: Optional[str] = Field(default=None)
    status: FPStatus = Field(default=FPStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    project: Optional[Project] = Relationship(back_populates="function_points")
    document: Optional[Document] = Relationship(back_populates="function_points")
    test_cases: List["TestCase"] = Relationship(back_populates="function_point")


class TestCase(SQLModel, table=True):
    __tablename__ = "test_cases"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    function_point_id: Optional[UUID] = Field(default=None, foreign_key="function_points.id", index=True)
    title: str = Field(max_length=500, index=True)
    description: Optional[str] = Field(default=None)
    test_type: TestType = Field(default=TestType.FUNCTIONAL)
    test_category: str = Field(default="frontend", max_length=50)
    priority: Priority = Field(default=Priority.P2)
    preconditions: Optional[str] = Field(default=None)
    test_steps: str = Field(default="[]")
    expected_results: Optional[str] = Field(default=None)
    test_data: Optional[str] = Field(default=None)
    tags: Optional[str] = Field(default=None)
    status: TCStatus = Field(default=TCStatus.DRAFT)
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    project: Optional[Project] = Relationship(back_populates="test_cases")
    function_point: Optional[FunctionPoint] = Relationship(back_populates="test_cases")
    test_scripts: List["TestScript"] = Relationship(back_populates="test_case")
    mind_map_nodes: List["MindMapNode"] = Relationship(back_populates="test_case")
    
    def get_test_steps(self) -> List[dict]:
        return json.loads(self.test_steps)
    
    def set_test_steps(self, steps: List[dict]):
        self.test_steps = json.dumps(steps, ensure_ascii=False)
    
    def get_tags(self) -> List[str]:
        if self.tags:
            return json.loads(self.tags)
        return []
    
    def set_tags(self, tags: List[str]):
        self.tags = json.dumps(tags)


class TestScript(SQLModel, table=True):
    __tablename__ = "test_scripts"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    test_case_id: Optional[UUID] = Field(default=None, foreign_key="test_cases.id", index=True)
    name: str = Field(max_length=255, index=True)
    language: ScriptLanguage = Field(default=ScriptLanguage.PYTHON)
    framework: str = Field(default="pytest", max_length=50)
    content: str = Field(default="")
    file_path: Optional[str] = Field(default=None, max_length=500)
    dependencies: Optional[str] = Field(default=None)
    status: ScriptStatus = Field(default=ScriptStatus.DRAFT)
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    project: Optional[Project] = Relationship(back_populates="test_scripts")
    test_case: Optional[TestCase] = Relationship(back_populates="test_scripts")
    
    def get_dependencies(self) -> List[str]:
        if self.dependencies:
            return json.loads(self.dependencies)
        return []
    
    def set_dependencies(self, deps: List[str]):
        self.dependencies = json.dumps(deps)


class MindMapNode(SQLModel, table=True):
    __tablename__ = "mind_map_nodes"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    test_case_id: Optional[UUID] = Field(default=None, foreign_key="test_cases.id")
    parent_id: Optional[UUID] = Field(default=None, foreign_key="mind_map_nodes.id")
    text: str = Field(max_length=500)
    node_type: NodeType = Field(default=NodeType.MODULE)
    position: Optional[str] = Field(default=None)
    style: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    project: Optional[Project] = Relationship(back_populates="mind_map_nodes")
    test_case: Optional[TestCase] = Relationship(back_populates="mind_map_nodes")
    children: List["MindMapNode"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"remote_side": "MindMapNode.id"}
    )
    parent: Optional["MindMapNode"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "MindMapNode.id", "foreign_keys": "[MindMapNode.parent_id]"}
    )
    
    def get_position(self) -> dict:
        if self.position:
            return json.loads(self.position)
        return {"x": 0, "y": 0}
    
    def set_position(self, pos: dict):
        self.position = json.dumps(pos)
    
    def get_style(self) -> dict:
        if self.style:
            return json.loads(self.style)
        return {}
    
    def set_style(self, style: dict):
        self.style = json.dumps(style)
