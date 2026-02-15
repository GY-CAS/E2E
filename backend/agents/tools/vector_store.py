from typing import List, Optional, Dict, Any
from langchain_openai import OpenAIEmbeddings
from pymilvus import MilvusClient
import asyncio

from app.core.config import settings


class MilvusVectorStore:
    def __init__(
        self,
        collection_name: str = None,
        embedding_model: str = None
    ):
        self.collection_name = collection_name or settings.MILVUS_COLLECTION_NAME
        self.client = MilvusClient(
            uri=f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}"
        )
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model or settings.EMBEDDING_MODEL,
            api_key=settings.EMBEDDING_API_KEY or settings.LLM_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL or settings.LLM_BASE_URL
        )
        self._ensure_collection()
    
    def _ensure_collection(self):
        if not self.client.has_collection(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                dimension=1536
            )
    
    async def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None
    ) -> List[str]:
        if not texts:
            return []
        
        vectors = await self.embeddings.aembed_documents(texts)
        
        data = []
        ids = []
        for i, (text, vector) in enumerate(zip(texts, vectors)):
            doc_id = f"doc_{i}_{hash(text) % 1000000}"
            ids.append(doc_id)
            data.append({
                "id": doc_id,
                "vector": vector,
                "text": text,
                "metadata": metadatas[i] if metadatas else {}
            })
        
        self.client.insert(
            collection_name=self.collection_name,
            data=data
        )
        
        return ids
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        query_vector = await self.embeddings.aembed_query(query)
        
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=k,
            output_fields=["text", "metadata"]
        )
        
        return [
            {
                "text": r["entity"]["text"],
                "metadata": r["entity"]["metadata"],
                "score": r["distance"]
            }
            for r in results[0]
        ]
    
    async def delete_documents(self, ids: List[str]):
        if ids:
            self.client.delete(
                collection_name=self.collection_name,
                ids=ids
            )
    
    def drop_collection(self):
        if self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)
