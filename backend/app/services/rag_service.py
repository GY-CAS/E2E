import logging
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Document
from app.services.milvus_service import milvus_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        pass
    
    async def retrieve_relevant_context(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None
    ) -> str:
        similar_docs = await milvus_service.search_similar(
            project_id=project_id,
            query=query,
            top_k=top_k,
            document_ids=document_ids
        )
        
        if not similar_docs:
            return ""
        
        context_parts = []
        for doc in similar_docs:
            context_parts.append(
                f"[文档: {doc['document_name']}]\n{doc['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    async def retrieve_for_function_points(
        self,
        project_id: str,
        user_requirements: str,
        document_ids: Optional[List[str]] = None
    ) -> str:
        context = await self.retrieve_relevant_context(
            project_id=project_id,
            query=user_requirements,
            top_k=10,
            document_ids=document_ids
        )
        
        return context
    
    async def retrieve_for_test_case(
        self,
        project_id: str,
        function_point: Dict[str, Any],
        document_ids: Optional[List[str]] = None
    ) -> str:
        query = f"{function_point.get('name', '')} {function_point.get('description', '')} {function_point.get('acceptance_criteria', '')}"
        
        context = await self.retrieve_relevant_context(
            project_id=project_id,
            query=query,
            top_k=5,
            document_ids=document_ids
        )
        
        return context
    
    async def get_document_content(
        self,
        session: Session,
        project_id: str,
        document_ids: Optional[List[str]] = None
    ) -> str:
        query = select(Document).where(
            Document.project_id == project_id,
            Document.status == "parsed"
        )
        
        if document_ids:
            query = query.where(Document.id.in_(document_ids))
        
        documents = session.exec(query).all()
        
        all_content = []
        for doc in documents:
            if doc.parsed_content:
                all_content.append(f"=== 文档: {doc.name} ===\n{doc.parsed_content}")
        
        return "\n\n".join(all_content)
    
    async def hybrid_search(
        self,
        project_id: str,
        query: str,
        session: Session,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        vector_results = await milvus_service.search_similar(
            project_id=project_id,
            query=query,
            top_k=top_k,
            document_ids=document_ids
        )
        
        return vector_results


rag_service = RAGService()
