from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import settings


class BaseAgent(ABC):
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None
    ):
        self.llm = llm or self._default_llm()
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.prompt_template = self._build_prompt_template()
    
    def _default_llm(self) -> BaseChatModel:
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=0.7
        )
    
    @abstractmethod
    def _build_prompt_template(self) -> ChatPromptTemplate:
        pass
    
    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def bind_tools(self):
        if self.tools:
            return self.llm.bind_tools(self.tools)
        return self.llm
    
    async def ainvoke(self, input_data: Dict[str, Any]) -> Any:
        chain = self.prompt_template | self.llm
        return await chain.ainvoke(input_data)
