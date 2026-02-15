from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from agents.base.base_agent import BaseAgent
from app.models.schemas import RequirementAnalysis


class RequirementParserAgent(BaseAgent):
    def __init__(self, llm=None, vector_store=None):
        self.vector_store = vector_store
        super().__init__(llm, [], self._get_system_prompt())
        self.output_parser = PydanticOutputParser(pydantic_object=RequirementAnalysis)
    
    def _get_system_prompt(self) -> str:
        return """你是一个资深的需求分析专家。基于提供的文档内容，你需要：
1. 理解业务需求和目标
2. 识别核心功能模块
3. 提取业务流程和数据实体
4. 分析模块间的依赖关系
5. 识别边界条件和异常场景

{format_instructions}"""
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "基于以下文档内容进行需求分析：\n\n{context}\n\n请分析需求并输出结构化结果。")
        ])
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = "提取所有功能需求、业务流程、数据实体和模块关系"
        
        context = ""
        if self.vector_store:
            relevant_docs = await self.vector_store.similarity_search(
                query=query,
                k=10
            )
            context = "\n\n".join([doc.get("text", "") for doc in relevant_docs])
        else:
            parsed_content = state.get("parsed_content", [])
            context = "\n\n".join([p.get("content", "") for p in parsed_content])
        
        chain = self.prompt_template | self.llm | self.output_parser
        
        result = await chain.ainvoke({
            "context": context,
            "format_instructions": self.output_parser.get_format_instructions()
        })
        
        return {
            "requirement_analysis": result.model_dump(),
            "current_stage": "requirement_parsed"
        }
