import logging
from typing import Callable, Awaitable, Optional
from src.rag.services.retriever import RetrievalService
from src.rag.services.ingestor import IngestionService
from src.config import settings

logger = logging.getLogger(__name__)

# 定義 Tool 的型別別名，讓程式碼更易讀
SearchTool = Callable[[str], Awaitable[str]]
IngestTool = Callable[[Optional[str]], str]

def create_search_tool(retriever: RetrievalService, ingestor: IngestionService) -> SearchTool:
    """
    建立搜尋工具的 Factory Function。
    使用 Closure (閉包) 將依賴 (retriever, ingestor) 封裝在函式內部。
    
    Args:
        retriever: 檢索服務實例
        ingestor: 匯入服務實例 (用於自動匯入檢查)
    """
    
    async def search_knowledge_base(query: str) -> str:
        """
        搜尋內部知識庫 (文件、PDF) 以獲取相關資訊。
        當使用者詢問特定文件或內部資料時使用此工具。
        
        Args:
            query: 搜尋查詢 (例如："退款政策是什麼？", "專案 X 的摘要")。
        """
        # [Auto-Ingestion Check]
        # 每次搜尋前都檢查是否有新檔案需要匯入。
        try:
            # 直接使用閉包中的 ingestor，不再依賴全域容器
            ingestor.run_pipeline(settings.rag.docs_folder)
        except Exception as e:
            logger.error(f"自動匯入檢查失敗: {e}")

        # 直接使用閉包中的 retriever
        return await retriever.query(query)

    return search_knowledge_base

def create_ingest_tool(ingestor: IngestionService) -> IngestTool:
    """
    建立匯入工具的 Factory Function。
    """
    def ingest_documents(folder: Optional[str] = None) -> str:
        """
        從 docs 資料夾匯入文件的管理工具。
        """
        target_folder = folder or settings.rag.docs_folder
        ingestor.run_pipeline(target_folder)
        return f"從 {target_folder} 匯入完成"
        
    return ingest_documents
