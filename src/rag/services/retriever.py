import logging
from typing import List
from src.rag.ports.repository import VectorStoreRepository
from src.rag.domain.models import SearchResult

logger = logging.getLogger(__name__)

class RetrievalService:
    """
    處理檢索邏輯。
    """
    def __init__(self, repo: VectorStoreRepository):
        self.repo = repo

    async def query(self, query_text: str, k: int = 4) -> str:
        try:
            print(f"[DEBUG] RetrievalService.query 收到查詢: '{query_text}'")
            logger.info(f"🔍 正在檢索: '{query_text}' (k={k})")
            
            results = await self.repo.search(query_text, k=k)
            
            if not results:
                print("[DEBUG] Repo 回傳空列表 []")
                logger.warning(f"⚠️ 檢索結果為空: '{query_text}'")
                return "在知識庫中找不到相關資訊。"
            
            print(f"[DEBUG] Repo 回傳了 {len(results)} 筆資料")
            logger.info(f"✅ 找到 {len(results)} 筆相關資料")
            return self._format_results(results)
            
        except Exception as e:
            print(f"[DEBUG] RetrievalService 發生例外: {e}")
            logger.error(f"RAG Retrieval failed: {e}")
            return f"檢索失敗: {e}"

    def _format_results(self, results: List[SearchResult]) -> str:
        formatted = []
        for i, res in enumerate(results, 1):
            source = res.chunk.metadata.get('source', 'unknown')
            # 簡單處理路徑顯示
            source_name = str(source).split('\\')[-1].split('/')[-1]
            formatted.append(f"--- 來源 {i} ({source_name}) ---\n{res.chunk.content}\n")
        return "\n".join(formatted)
