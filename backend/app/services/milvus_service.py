import logging
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility
)
from datetime import datetime

from app.core.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class MilvusService:
    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.collection_prefix = settings.MILVUS_COLLECTION_NAME
        self._connected = False
    
    def connect(self):
        if not self._connected:
            try:
                connections.connect(
                    alias="default",
                    host=self.host,
                    port=self.port
                )
                self._connected = True
                logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"Failed to connect to Milvus: {e}")
                raise
    
    def disconnect(self):
        if self._connected:
            try:
                connections.disconnect("default")
                self._connected = False
                logger.info("Disconnected from Milvus")
            except Exception as e:
                logger.error(f"Failed to disconnect from Milvus: {e}")
    
    def get_collection_name(self, project_id: str) -> str:
        safe_id = str(project_id).replace("-", "_").lower()[:20]
        return f"{self.collection_prefix}_{safe_id}"
    
    def create_collection(self, project_id: str, embedding_dim: int = 1024) -> Collection:
        self.connect()
        
        collection_name = self.get_collection_name(project_id)
        
        if utility.has_collection(collection_name):
            logger.info(f"Collection {collection_name} already exists")
            return Collection(collection_name)
        
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="document_name", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="content_type", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
            FieldSchema(name="created_at", dtype=DataType.INT64),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description=f"Document vectors for project {project_id}",
            enable_dynamic_field=True
        )
        
        collection = Collection(
            name=collection_name,
            schema=schema
        )
        
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        logger.info(f"Created collection {collection_name} with embedding dimension {embedding_dim}")
        
        return collection
    
    def delete_collection(self, project_id: str) -> bool:
        self.connect()
        
        collection_name = self.get_collection_name(project_id)
        
        try:
            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)
                logger.info(f"Deleted collection {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    async def insert_vectors(
        self,
        project_id: str,
        document_id: str,
        document_name: str,
        chunks: List[Dict[str, Any]],
        content_type: str = "text"
    ) -> int:
        self.connect()
        
        if not chunks:
            return 0
        
        texts = [chunk["content"] for chunk in chunks]
        
        embeddings = await llm_service.embed_texts(texts)
        
        if not embeddings or len(embeddings) == 0:
            logger.error("Failed to generate embeddings")
            return 0
        
        embedding_dim = len(embeddings[0])
        
        collection = self.create_collection(project_id, embedding_dim)
        
        import uuid
        from datetime import datetime
        
        data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            data.append({
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "document_name": document_name,
                "chunk_index": i,
                "content": chunk["content"][:65500],
                "content_type": content_type,
                "embedding": embedding,
                "created_at": int(datetime.utcnow().timestamp()),
                "metadata": {
                    "char_count": chunk.get("char_count", len(chunk["content"])),
                    "source": chunk.get("source", "document")
                }
            })
        
        collection.insert(data)
        collection.flush()
        
        logger.info(f"Inserted {len(data)} vectors into collection for project {project_id}")
        
        return len(data)
    
    async def search_similar(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        self.connect()
        
        collection_name = self.get_collection_name(project_id)
        
        if not utility.has_collection(collection_name):
            logger.warning(f"Collection {collection_name} does not exist")
            return []
        
        collection = Collection(collection_name)
        collection.load()
        
        query_embedding = await llm_service.embed_query(query)
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 16}
        }
        
        filter_expr = None
        if document_ids:
            doc_ids_str = ", ".join([f'"{doc_id}"' for doc_id in document_ids])
            filter_expr = f'document_id in [{doc_ids_str}]'
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["document_id", "document_name", "chunk_index", "content", "content_type", "metadata"]
        )
        
        similar_docs = []
        for hits in results:
            for hit in hits:
                similar_docs.append({
                    "id": hit.id,
                    "distance": hit.distance,
                    "document_id": hit.entity.get("document_id"),
                    "document_name": hit.entity.get("document_name"),
                    "chunk_index": hit.entity.get("chunk_index"),
                    "content": hit.entity.get("content"),
                    "content_type": hit.entity.get("content_type"),
                    "metadata": hit.entity.get("metadata")
                })
        
        return similar_docs
    
    def delete_document_vectors(self, project_id: str, document_id: str) -> bool:
        self.connect()
        
        collection_name = self.get_collection_name(project_id)
        
        if not utility.has_collection(collection_name):
            return True
        
        try:
            collection = Collection(collection_name)
            collection.delete(f'document_id == "{document_id}"')
            collection.flush()
            logger.info(f"Deleted vectors for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document vectors: {e}")
            return False
    
    def get_collection_stats(self, project_id: str) -> Dict[str, Any]:
        self.connect()
        
        collection_name = self.get_collection_name(project_id)
        
        if not utility.has_collection(collection_name):
            return {"exists": False, "count": 0}
        
        collection = Collection(collection_name)
        stats = collection.num_entities
        
        return {
            "exists": True,
            "count": stats,
            "collection_name": collection_name
        }


milvus_service = MilvusService()
