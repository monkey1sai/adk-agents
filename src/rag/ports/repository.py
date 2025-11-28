from typing import List, Protocol
from src.rag.domain.models import Chunk, SearchResult

class VectorStoreRepository(Protocol):
    """
    向量儲存操作的埠 (Port) 定義。
    將業務邏輯與具體的資料庫實作 (Chroma, Pinecone 等) 解耦。
    """
    
    def add_chunks(self, chunks: List[Chunk]) -> None:
        """將 Chunks 持久化到向量儲存中。"""
        ...

    async def search(self, query: str, k: int = 4) -> List[SearchResult]:
        """非同步地檢索給定查詢的相關 Chunks。"""
        ...
