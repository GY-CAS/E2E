from typing import TypedDict, List, Annotated, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage
import operator
import asyncio

from agents.document import DocumentParserAgent
from agents.requirement import RequirementParserAgent
from agents.function_point import FunctionPointAgent
from agents.testcase import TestCaseGeneratorAgent
from agents.script import PythonScriptAgent, JavaScriptAgent


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    documents: List[dict]
    parsed_content: List[dict]
    requirement_analysis: dict
    function_points: List[dict]
    test_cases: List[dict]
    test_scripts: List[dict]
    mind_map: dict
    project_id: str
    current_stage: str
    errors: List[str]
    user_feedback: str
    generate_scripts: bool
    script_language: str


async def document_parser_node(state: AgentState) -> Dict[str, Any]:
    agent = DocumentParserAgent()
    result = await agent.execute(state)
    return result


async def requirement_parser_node(state: AgentState) -> Dict[str, Any]:
    agent = RequirementParserAgent()
    result = await agent.execute(state)
    return result


async def function_point_generator_node(state: AgentState) -> Dict[str, Any]:
    agent = FunctionPointAgent()
    result = await agent.execute(state)
    return result


async def user_review_node(state: AgentState) -> Dict[str, Any]:
    return {
        "current_stage": "user_review"
    }


async def testcase_generator_node(state: AgentState) -> Dict[str, Any]:
    agent = TestCaseGeneratorAgent()
    result = await agent.execute(state)
    return result


async def script_generator_node(state: AgentState) -> Dict[str, Any]:
    language = state.get("script_language", "python")
    
    if language == "java":
        agent = JavaScriptAgent()
    else:
        agent = PythonScriptAgent()
    
    result = await agent.execute(state)
    return result


async def mindmap_generator_node(state: AgentState) -> Dict[str, Any]:
    test_cases = state.get("test_cases", [])
    
    nodes = []
    for i, tc in enumerate(test_cases):
        nodes.append({
            "id": f"tc_{i}",
            "text": tc.get("title", ""),
            "node_type": "testcase",
            "children": [
                {
                    "id": f"step_{i}_{j}",
                    "text": step.get("action", ""),
                    "node_type": "step"
                }
                for j, step in enumerate(tc.get("test_steps", []))
            ]
        })
    
    return {
        "mind_map": {
            "root": {
                "id": "root",
                "text": "Test Cases",
                "node_type": "root",
                "children": nodes
            }
        },
        "current_stage": "completed"
    }


def route_after_review(state: AgentState) -> str:
    feedback = state.get("user_feedback", "")
    
    if feedback == "approved":
        return "approved"
    elif feedback == "rejected":
        return "rejected"
    else:
        return "modified"


def should_generate_scripts(state: AgentState) -> str:
    if state.get("generate_scripts", False):
        return "generate"
    return "skip"


def create_main_workflow():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("document_parser", document_parser_node)
    workflow.add_node("requirement_parser", requirement_parser_node)
    workflow.add_node("function_point_generator", function_point_generator_node)
    workflow.add_node("user_review", user_review_node)
    workflow.add_node("testcase_generator", testcase_generator_node)
    workflow.add_node("script_generator", script_generator_node)
    workflow.add_node("mindmap_generator", mindmap_generator_node)
    
    workflow.set_entry_point("document_parser")
    
    workflow.add_edge("document_parser", "requirement_parser")
    workflow.add_edge("requirement_parser", "function_point_generator")
    workflow.add_edge("function_point_generator", "user_review")
    
    workflow.add_conditional_edges(
        "user_review",
        route_after_review,
        {
            "approved": "testcase_generator",
            "rejected": "function_point_generator",
            "modified": "function_point_generator"
        }
    )
    
    workflow.add_edge("testcase_generator", "script_generator")
    
    workflow.add_conditional_edges(
        "script_generator",
        should_generate_scripts,
        {
            "generate": "mindmap_generator",
            "skip": "mindmap_generator"
        }
    )
    
    workflow.add_edge("mindmap_generator", END)
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


async def run_workflow(
    documents: List[dict],
    project_id: str,
    generate_scripts: bool = False,
    script_language: str = "python"
) -> Dict[str, Any]:
    workflow = create_main_workflow()
    
    initial_state: AgentState = {
        "messages": [],
        "documents": documents,
        "parsed_content": [],
        "requirement_analysis": {},
        "function_points": [],
        "test_cases": [],
        "test_scripts": [],
        "mind_map": {},
        "project_id": project_id,
        "current_stage": "init",
        "errors": [],
        "user_feedback": "approved",
        "generate_scripts": generate_scripts,
        "script_language": script_language
    }
    
    result = await workflow.ainvoke(initial_state)
    return result


async def stream_workflow_events(
    documents: List[dict],
    project_id: str,
    generate_scripts: bool = False,
    script_language: str = "python"
):
    workflow = create_main_workflow()
    
    initial_state: AgentState = {
        "messages": [],
        "documents": documents,
        "parsed_content": [],
        "requirement_analysis": {},
        "function_points": [],
        "test_cases": [],
        "test_scripts": [],
        "mind_map": {},
        "project_id": project_id,
        "current_stage": "init",
        "errors": [],
        "user_feedback": "approved",
        "generate_scripts": generate_scripts,
        "script_language": script_language
    }
    
    async for event in workflow.astream_events(initial_state, version="v1"):
        yield event
