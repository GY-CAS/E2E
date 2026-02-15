from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter

from agents.base.base_agent import BaseAgent
from app.core.config import settings


class DocumentParserAgent(BaseAgent):
    def __init__(self, llm=None, vector_store=None):
        super().__init__(llm, [], self._get_system_prompt())
        self.vector_store = vector_store
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def _get_system_prompt(self) -> str:
        return """你是一个专业的文档解析专家。你的任务是：
1. 解析用户上传的文档内容
2. 提取关键信息和结构
3. 识别文档类型（需求文档/设计文档/接口说明等）
4. 将文档内容向量化存储

请确保提取的信息完整、准确。"""
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "请解析以下文档内容：\n\n{document_content}")
        ])
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        documents = state.get("documents", [])
        parsed_results = []
        
        for doc in documents:
            content = await self._load_document(doc)
            chunks = self.text_splitter.split_text(content)
            
            vector_ids = []
            if self.vector_store:
                vector_ids = await self.vector_store.add_documents(
                    texts=chunks,
                    metadatas=[{"source": doc.get("name", ""), "type": doc.get("type", "")}] * len(chunks)
                )
            
            parsed_results.append({
                "doc_name": doc.get("name", ""),
                "doc_type": doc.get("type", ""),
                "content": content,
                "chunks_count": len(chunks),
                "vector_ids": vector_ids
            })
        
        return {
            "parsed_content": parsed_results,
            "current_stage": "document_parsed"
        }
    
    async def _load_document(self, doc: Dict) -> str:
        file_path = doc.get("file_path", "")
        file_type = doc.get("type", "txt")
        
        if file_type == "pdf":
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            return "\n".join([d.page_content for d in docs])
        
        elif file_type in ["docx", "doc"]:
            from langchain_community.document_loaders import Docx2txtLoader
            loader = Docx2txtLoader(file_path)
            docs = loader.load()
            return "\n".join([d.page_content for d in docs])
        
        elif file_type == "md":
            from langchain_community.document_loaders import UnstructuredMarkdownLoader
            loader = UnstructuredMarkdownLoader(file_path)
            docs = loader.load()
            return "\n".join([d.page_content for d in docs])
        
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
