from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
import json

from agents.base.base_agent import BaseAgent


class TestCaseGeneratorAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__(llm, [], self._get_system_prompt())
    
    def _get_system_prompt(self) -> str:
        return """你是一个专业的测试用例设计专家。根据功能点生成详细的测试用例。

测试用例格式要求：
1. title: 测试用例标题，简洁明了
2. description: 测试用例描述
3. test_type: 测试类型（functional/performance/security/reliability）
4. test_category: 测试分类（frontend/backend/api/integration）
5. priority: 优先级（p0/p1/p2/p3/p4）
6. preconditions: 前置条件
7. test_steps: 测试步骤数组，每个步骤包含：
   - step_num: 步骤编号
   - action: 操作描述
   - expected_result: 预期结果
   - test_data: 测试数据（可选）
8. expected_results: 整体预期结果
9. tags: 标签数组

测试类型详细说明：
- 功能测试：
  * 前端UI：页面渲染、交互逻辑、表单验证、响应式布局
  * 后端API：接口调用、参数校验、响应验证、错误处理
  * 业务流程：端到端场景、数据流转、状态转换

- 性能测试：
  * 页面加载时间、首屏渲染时间
  * 接口响应时间、吞吐量
  * 并发处理能力、资源消耗

- 安全测试：
  * 认证授权：登录验证、权限控制、会话管理
  * 注入攻击：SQL注入、XSS、CSRF
  * 数据安全：敏感数据加密、传输安全

- 可靠性测试：
  * 异常处理：网络异常、服务异常、数据异常
  * 容错机制：重试机制、降级处理
  * 稳定性：长时间运行、压力测试

请以JSON数组格式输出测试用例列表。"""
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """根据以下功能点生成测试用例：

功能点：
{function_points}

请为每个功能点生成详细的测试用例，确保覆盖正常流程、异常流程和边界条件。只输出JSON数组，不要其他文字。""")
        ])
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        function_points = state.get("function_points", [])
        project_id = state.get("project_id")
        
        all_test_cases = []
        
        for fp in function_points:
            chain = self.prompt_template | self.llm
            
            result = await chain.ainvoke({
                "function_points": json.dumps(fp, ensure_ascii=False, indent=2)
            })
            
            content = result.content
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            try:
                test_cases = json.loads(content)
            except json.JSONDecodeError:
                test_cases = []
            
            for tc in test_cases:
                formatted_tc = {
                    "project_id": project_id,
                    "function_point_id": fp.get("id"),
                    "title": tc.get("title", ""),
                    "description": tc.get("description", ""),
                    "test_type": tc.get("test_type", "functional"),
                    "test_category": tc.get("test_category", "frontend"),
                    "priority": tc.get("priority", "p2"),
                    "preconditions": tc.get("preconditions", ""),
                    "test_steps": tc.get("test_steps", []),
                    "expected_results": tc.get("expected_results", ""),
                    "test_data": tc.get("test_data"),
                    "tags": tc.get("tags", [])
                }
                all_test_cases.append(formatted_tc)
        
        return {
            "test_cases": all_test_cases,
            "current_stage": "test_cases_generated"
        }
