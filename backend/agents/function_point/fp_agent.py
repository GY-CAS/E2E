from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import json

from agents.base.base_agent import BaseAgent
from app.models.schemas import FunctionPointCreate


class FunctionPointAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__(llm, [], self._get_system_prompt())
    
    def _get_system_prompt(self) -> str:
        return """你是一个测试专家，负责根据需求分析结果生成测试功能点。

测试类型分类：
- functional: 功能测试（前端UI、后端API、业务流程）
- performance: 性能测试（页面加载、接口响应、并发处理）
- security: 安全测试（认证授权、XSS/CSRF、SQL注入）
- reliability: 可靠性测试（异常处理、容错机制、稳定性）

优先级定义：
- p0: 核心功能，阻塞性问题
- p1: 重要功能，影响主流程
- p2: 一般功能，影响用户体验
- p3: 次要功能，优化类需求
- p4: 边缘场景，低优先级

请以JSON数组格式输出功能点列表，每个功能点包含：
- name: 功能点名称
- description: 功能点描述
- test_type: 测试类型
- priority: 优先级
- module: 所属模块
- acceptance_criteria: 验收标准"""
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """基于以下需求分析结果，生成测试功能点清单：

需求分析：
{requirement_analysis}

请生成完整的测试功能点列表，确保覆盖所有测试类型。只输出JSON数组，不要其他文字。""")
        ])
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        requirement = state.get("requirement_analysis", {})
        project_id = state.get("project_id")
        
        chain = self.prompt_template | self.llm
        
        result = await chain.ainvoke({
            "requirement_analysis": json.dumps(requirement, ensure_ascii=False, indent=2)
        })
        
        content = result.content
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        try:
            function_points = json.loads(content)
        except json.JSONDecodeError:
            function_points = []
        
        formatted_fps = []
        for fp in function_points:
            formatted_fp = {
                "project_id": project_id,
                "name": fp.get("name", ""),
                "description": fp.get("description", ""),
                "test_type": fp.get("test_type", "functional"),
                "priority": fp.get("priority", "p2"),
                "module": fp.get("module", ""),
                "acceptance_criteria": fp.get("acceptance_criteria", "")
            }
            formatted_fps.append(formatted_fp)
        
        return {
            "function_points": formatted_fps,
            "current_stage": "function_points_generated"
        }
