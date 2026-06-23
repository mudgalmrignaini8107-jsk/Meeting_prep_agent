# app/services/pinecone_service.py

from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from loguru import logger
from app.config import settings

class PineconeService:
    def __init__(self):
        self.pc: Optional[Pinecone] = None
        self.index = None
        
        if not settings.PINECONE_API_KEY:
            logger.warning("PINECONE_API_KEY is not set. Pinecone RAG operations will run in mock mode.")
            return
            
        try:
            # Initialize Pinecone Client
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Check or create index (standard 1536 dim for text-embedding-3-small)
            index_name = settings.PINECONE_INDEX_NAME
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {index_name}...")
                self.pc.create_index(
                    name=index_name,
                    dimension=1536,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT or "us-east-1"
                    )
                )
                
            self.index = self.pc.Index(index_name)
            logger.info(f"Connected to Pinecone Index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone Client: {e}. Falling back to mock mode.")
            self.pc = None
            self.index = None

    def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        """
        Upsert a list of vectors. 
        Each entry in vectors should be a dictionary:
        {
            "id": str,
            "values": List[float],
            "metadata": Dict[str, Any]
        }
        """
        if not self.index:
            logger.warning("Pinecone Index not initialized. Mocking vector upsert.")
            return True
            
        try:
            self.index.upsert(vectors=vectors)
            return True
        except Exception as e:
            logger.error(f"Pinecone Upsert failed: {e}")
            return False

    def query_vectors(self, vector: List[float], top_k: int = 5, workspace_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query Pinecone index for similar vectors. Filters by workspace_id if supplied.
        """
        if not self.index:
            logger.warning("Pinecone Index not initialized. Returning empty mock query results.")
            return []
            
        try:
            filter_dict = {}
            if workspace_id:
                filter_dict["workspace_id"] = workspace_id
                
            response = self.index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            results = []
            for match in response.matches:
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            return results
        except Exception as e:
            logger.error(f"Pinecone Query failed: {e}")
            return []

# Export singleton instance
pinecone_service = PineconeService()
