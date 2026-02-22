import logging
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import re

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.llm_api_key = settings.LLM_API_KEY
        self.llm_base_url = settings.LLM_BASE_URL
        self.llm_model = settings.LLM_MODEL
        
        self.embedding_api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        self.embedding_base_url = settings.EMBEDDING_BASE_URL or settings.LLM_BASE_URL
        self.embedding_model = settings.EMBEDDING_MODEL
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        try:
            chat_messages = []
            
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            
            chat_messages.extend(messages)
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.llm_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.llm_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.llm_model,
                        "messages": chat_messages,
                        "temperature": 0.7
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise
    
    async def understand_requirements(self, user_input: str) -> Dict[str, Any]:
        system_prompt = """你是一个专业的测试需求分析专家。请分析用户输入的测试需求，提取关键信息。

分析要点：
1. 核心功能模块：识别需要测试的主要功能模块
2. 测试类型：判断需要进行的测试类型（功能/性能/安全/可靠性）
3. 优先级建议：根据业务重要性给出优先级建议
4. 关键场景：识别核心业务场景和边界条件
5. 技术关注点：识别技术实现相关的测试关注点

请以JSON格式输出分析结果，包含以下字段：
{
    "modules": ["模块1", "模块2"],
    "test_types": ["functional", "performance"],
    "priority_suggestion": "p0/p1/p2",
    "key_scenarios": ["场景1", "场景2"],
    "technical_points": ["关注点1", "关注点2"],
    "summary": "需求摘要"
}"""
        
        messages = [{"role": "user", "content": user_input}]
        response = await self.chat(messages, system_prompt)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        return {
            "modules": [],
            "test_types": ["functional"],
            "priority_suggestion": "p2",
            "key_scenarios": [],
            "technical_points": [],
            "summary": user_input[:200]
        }
    
    async def generate_function_points(
        self,
        user_requirements: str,
        document_context: str,
        test_types: List[str],
        requirements_analysis: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        system_prompt = """你是一个专业的测试设计专家。根据用户需求、文档内容和需求分析结果，生成详细的测试功能点清单。

测试类型分类：
- functional: 功能测试（前端UI、后端API、业务流程）
- performance: 性能测试（页面加载、接口响应、并发处理）
- security: 安全测试（认证授权、XSS/CSRF、SQL注入）
- reliability: 可靠性测试（异常处理、容错机制、稳定性）

优先级定义：
- p0: 核心功能，阻塞性问题，必须测试
- p1: 重要功能，影响主流程
- p2: 一般功能，影响用户体验
- p3: 次要功能，优化类需求
- p4: 边缘场景，低优先级

功能点要求：
1. 名称简洁明确，能清晰表达测试目标
2. 描述详细，包含测试范围和目标
3. 验收标准具体可执行

请以JSON数组格式输出功能点列表，每个功能点包含：
{
    "name": "功能点名称",
    "description": "功能点描述",
    "test_type": "functional/performance/security/reliability",
    "priority": "p0/p1/p2/p3/p4",
    "module": "所属模块",
    "acceptance_criteria": "验收标准"
}

只输出JSON数组，不要其他文字说明。"""
        
        analysis_info = ""
        if requirements_analysis:
            analysis_info = f"""
需求分析结果：
- 核心模块: {', '.join(requirements_analysis.get('modules', []))}
- 测试类型建议: {', '.join(requirements_analysis.get('test_types', []))}
- 优先级建议: {requirements_analysis.get('priority_suggestion', 'p2')}
- 关键场景: {', '.join(requirements_analysis.get('key_scenarios', []))}
"""
        
        user_prompt = f"""用户需求：
{user_requirements}

{analysis_info}

文档知识库内容：
{document_context[:4000] if document_context else '暂无相关文档'}

需要生成的测试类型：{', '.join(test_types)}

请根据以上信息生成完整的测试功能点清单。确保功能点覆盖所有关键场景和边界条件。"""
        
        messages = [{"role": "user", "content": user_prompt}]
        response = await self.chat(messages, system_prompt)
        
        function_points = self._parse_function_points(response)
        
        logger.info(f"Generated {len(function_points)} function points")
        
        return function_points
    
    async def refine_function_point(
        self,
        function_point: Dict[str, Any],
        user_feedback: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        system_prompt = """你是一个测试设计专家。根据用户反馈优化功能点。

优化要点：
1. 名称：使名称更准确、简洁、专业
2. 描述：使描述更清晰、完整、具体
3. 测试类型：确认测试类型是否合适
4. 优先级：根据重要性调整优先级
5. 模块归属：确认模块归属是否正确
6. 验收标准：补充或优化验收标准，使其可执行、可验证

以JSON格式输出优化后的功能点，包含所有字段。"""
        
        context_info = f"\n\n上下文信息：\n{context[:1000]}" if context else ""
        
        messages = [{
            "role": "user", 
            "content": f"原功能点：\n{json.dumps(function_point, ensure_ascii=False)}\n\n用户反馈：{user_feedback}{context_info}"
        }]
        
        response = await self.chat(messages, system_prompt)
        
        refined_point = self._parse_function_point(response)
        
        return refined_point
    
    async def generate_test_case(
        self,
        function_point: Dict[str, Any],
        document_context: Optional[str] = None
    ) -> Dict[str, Any]:
        system_prompt = """你是一个测试用例设计专家。根据功能点生成详细的测试用例。

测试用例设计原则：
1. 完整性：覆盖正常流程、异常流程、边界条件
2. 可执行性：测试步骤清晰、具体、可操作
3. 可验证性：预期结果明确、可验证
4. 独立性：每个测试用例独立，不依赖其他用例

测试步骤要求：
- 每个步骤清晰描述操作动作
- 预期结果具体可验证
- 包含必要的测试数据

请以JSON格式输出测试用例：
{
    "title": "测试用例标题",
    "description": "测试用例描述",
    "test_type": "functional/performance/security/reliability",
    "test_category": "frontend/backend/api/integration",
    "priority": "p0/p1/p2/p3/p4",
    "preconditions": "前置条件",
    "test_steps": [
        {
            "step_num": 1,
            "action": "操作步骤",
            "expected_result": "预期结果"
        }
    ],
    "expected_results": "整体预期结果",
    "test_data": {}
}"""
        
        context_info = f"\n\n相关文档内容：\n{document_context[:2000]}" if document_context else ""
        
        messages = [{
            "role": "user",
            "content": f"""功能点信息：
名称: {function_point.get('name')}
描述: {function_point.get('description')}
测试类型: {function_point.get('test_type')}
优先级: {function_point.get('priority')}
模块: {function_point.get('module')}
验收标准: {function_point.get('acceptance_criteria')}
{context_info}

请生成详细的测试用例，确保覆盖正常流程、异常流程和边界条件。"""
        }]
        
        response = await self.chat(messages, system_prompt)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            try:
                test_case = json.loads(json_match.group(0))
                test_case["function_point_id"] = function_point.get("id")
                test_case["project_id"] = function_point.get("project_id")
                return test_case
            except:
                pass
        
        return {
            "title": f"测试_{function_point.get('name', '未命名')}",
            "description": function_point.get("description", ""),
            "test_type": function_point.get("test_type", "functional"),
            "test_category": "functional",
            "priority": function_point.get("priority", "p2"),
            "preconditions": "",
            "test_steps": [],
            "expected_results": function_point.get("acceptance_criteria", ""),
            "function_point_id": function_point.get("id"),
            "project_id": function_point.get("project_id")
        }
    
    async def generate_test_script(
        self,
        test_case: Dict[str, Any],
        language: str = "python",
        framework: str = "pytest"
    ) -> str:
        system_prompt = f"""你是一个{'Python' if language == 'python' else 'Java'}测试脚本生成专家。

使用{framework}框架生成测试脚本。

代码规范：
1. 结构清晰，易于维护
2. 包含必要的注释说明
3. 包含断言和错误处理
4. 遵循{framework}最佳实践
5. 使用Page Object模式（如适用）
6. 包含测试数据管理

只输出代码，不要其他文字说明。"""
        
        messages = [{
            "role": "user",
            "content": f"""测试用例信息：
标题: {test_case.get('title')}
描述: {test_case.get('description')}
前置条件: {test_case.get('preconditions')}
测试步骤: {json.dumps(test_case.get('test_steps', []), ensure_ascii=False, indent=2)}
预期结果: {test_case.get('expected_results')}

请生成完整的测试脚本代码。"""
        }]
        
        response = await self.chat(messages, system_prompt)
        
        content = response
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
        
        return content.strip()
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.embedding_base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.embedding_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.embedding_model,
                        "input": texts
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                return [item["embedding"] for item in result["data"]]
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise
    
    async def embed_query(self, text: str) -> List[float]:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.embedding_base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.embedding_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.embedding_model,
                        "input": text
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Query embedding error: {e}")
            raise
    
    def _parse_function_points(self, response: str) -> List[Dict[str, Any]]:
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        
        if json_match:
            try:
                fps = json.loads(json_match.group(0))
                return [self._normalize_fp(fp) for fp in fps]
            except json.JSONDecodeError:
                pass
        
        function_points = []
        lines = response.split('\n')
        current_fp = {}
        
        for line in lines:
            if '功能点名称' in line or '"name"' in line.lower():
                if current_fp and current_fp.get('name'):
                    function_points.append(self._normalize_fp(current_fp))
                current_fp = {}
            
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace('"', '').replace("'", '')
                value = value.strip().strip(',').strip('"').strip("'")
                
                if 'name' in key or '名称' in key:
                    current_fp['name'] = value
                elif 'description' in key or '描述' in key:
                    current_fp['description'] = value
                elif 'test_type' in key or '测试类型' in key:
                    current_fp['test_type'] = value
                elif 'priority' in key or '优先级' in key:
                    current_fp['priority'] = value.lower() if value else 'p2'
                elif 'module' in key or '模块' in key:
                    current_fp['module'] = value
                elif 'acceptance' in key or '验收' in key:
                    current_fp['acceptance_criteria'] = value
        
        if current_fp and current_fp.get('name'):
            function_points.append(self._normalize_fp(current_fp))
        
        return function_points
    
    def _parse_function_point(self, response: str) -> Dict[str, Any]:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            try:
                fp = json.loads(json_match.group(0))
                return self._normalize_fp(fp)
            except json.JSONDecodeError:
                pass
        
        result = {}
        lines = response.split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip().strip(',').strip('"').strip("'")
                
                if 'name' in key or '名称' in key:
                    result['name'] = value
                elif 'description' in key or '描述' in key:
                    result['description'] = value
                elif 'test_type' in key or '测试类型' in key:
                    result['test_type'] = value
                elif 'priority' in key or '优先级' in key:
                    result['priority'] = value.lower() if value else 'p2'
                elif 'module' in key or '模块' in key:
                    result['module'] = value
                elif 'acceptance' in key or '验收' in key:
                    result['acceptance_criteria'] = value
        
        return self._normalize_fp(result)
    
    def _normalize_fp(self, fp: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": fp.get("name", "未命名功能点"),
            "description": fp.get("description", ""),
            "test_type": fp.get("test_type", "functional"),
            "priority": fp.get("priority", "p2").lower() if fp.get("priority") else "p2",
            "module": fp.get("module", ""),
            "acceptance_criteria": fp.get("acceptance_criteria", "")
        }


llm_service = LLMService()
