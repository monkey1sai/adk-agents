import logging
from typing import List
from src.rag.ports.repository import VectorStoreRepository

logger = logging.getLogger(__name__)

class RetrievalService:
    """
    處理檢索邏輯。
    """
    def __init__(self, repo: VectorStoreRepository):
        self.repo = repo

    async def query(self, query_text: str, k: int = 4) -> str:
        """
        檢索相關上下文並將其格式化為字串以供 LLM 使用。
        """
        try:
            results = await self.repo.search(query_text, k=k)
            
            if not results:
                return "No relevant information found in the knowledge base."
                
            # Format context
            context_parts = []
            for i, res in enumerate(results, 1):
                source = res.chunk.metadata.get('source', 'Unknown')
                context_parts.append(f"--- Source {i} ({source}) ---\n{res.chunk.content}\n")
                
            return "\n".join(context_parts)
        except Exception as e:
            # [SRE Fix] 錯誤邊界：捕獲例外並回傳優雅的訊息
            logger.error(f"RAG Retrieval failed: {e}", exc_info=True)
            return "Error: Unable to access the knowledge base at this moment. Please try again later."
