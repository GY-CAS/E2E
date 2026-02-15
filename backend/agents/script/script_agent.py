from abc import abstractmethod
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
import json

from agents.base.base_agent import BaseAgent


class BaseScriptGeneratorAgent(BaseAgent):
    def __init__(self, llm=None, template_loader=None):
        self.template_loader = template_loader
        super().__init__(llm, [], self._get_system_prompt())
    
    @abstractmethod
    def _get_language(self) -> str:
        pass
    
    @abstractmethod
    def _get_framework(self) -> str:
        pass


class PythonScriptAgent(BaseScriptGeneratorAgent):
    def _get_language(self) -> str:
        return "python"
    
    def _get_framework(self) -> str:
        return "pytest"
    
    def _get_system_prompt(self) -> str:
        return """你是一个Python测试脚本生成专家。根据测试用例生成pytest + Selenium/Playwright测试脚本。

代码规范：
1. 使用pytest框架
2. 遵循Page Object模式
3. 添加完整的注释和文档字符串
4. 包含断言和错误处理
5. 支持参数化测试

生成的代码需要：
- 可直接运行
- 结构清晰
- 易于维护
- 包含必要的导入语句

只输出代码，不要其他文字说明。"""
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """根据以下测试用例生成Python测试脚本：

测试用例：
{test_case}

请生成完整的pytest测试脚本代码。""")
        ])
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        test_cases = state.get("test_cases", [])
        project_id = state.get("project_id")
        scripts = []
        
        for tc in test_cases:
            chain = self.prompt_template | self.llm
            
            result = await chain.ainvoke({
                "test_case": json.dumps(tc, ensure_ascii=False, indent=2)
            })
            
            content = result.content
            if content.startswith("```python"):
                content = content.split("```python")[1].split("```")[0]
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0]
            
            scripts.append({
                "project_id": project_id,
                "test_case_id": tc.get("id"),
                "name": f"test_{tc.get('title', 'case').lower().replace(' ', '_')[:30]}",
                "language": "python",
                "framework": "pytest",
                "content": content.strip()
            })
        
        return {
            "test_scripts": scripts,
            "current_stage": "scripts_generated"
        }


class JavaScriptAgent(BaseScriptGeneratorAgent):
    def _get_language(self) -> str:
        return "java"
    
    def _get_framework(self) -> str:
        return "testng"
    
    def _get_system_prompt(self) -> str:
        return """你是一个Java测试脚本生成专家。根据测试用例生成TestNG + Selenium测试脚本。

代码规范：
1. 使用TestNG框架
2. 遵循Page Object模式
3. 添加完整的JavaDoc注释
4. 包含断言和异常处理
5. 支持数据驱动测试

生成的代码需要：
- 可直接编译运行
- 结构清晰
- 易于维护
- 包含必要的import语句

只输出代码，不要其他文字说明。"""
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """根据以下测试用例生成Java测试脚本：

测试用例：
{test_case}

请生成完整的TestNG测试脚本代码。""")
        ])
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        test_cases = state.get("test_cases", [])
        project_id = state.get("project_id")
        scripts = []
        
        for tc in test_cases:
            chain = self.prompt_template | self.llm
            
            result = await chain.ainvoke({
                "test_case": json.dumps(tc, ensure_ascii=False, indent=2)
            })
            
            content = result.content
            if content.startswith("```java"):
                content = content.split("```java")[1].split("```")[0]
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0]
            
            scripts.append({
                "project_id": project_id,
                "test_case_id": tc.get("id"),
                "name": f"Test{tc.get('title', 'Case').replace(' ', '')[:30]}",
                "language": "java",
                "framework": "testng",
                "content": content.strip()
            })
        
        return {
            "test_scripts": scripts,
            "current_stage": "scripts_generated"
        }
