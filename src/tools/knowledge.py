import logging
import threading  # [Add] For thread safety
from typing import Optional
from src.config import settings
from src.rag.adapters.chroma_repository import ChromaRepository
from src.rag.services.retriever import RetrievalService
from src.rag.services.ingestor import IngestionService

logger = logging.getLogger(__name__)

class RAGContainer:
    """
    RAG 子系統的簡易依賴注入容器 (Dependency Injection Container)。
    管理 Repository 和 Services 的生命週期。
    """
    _instance: Optional['RAGContainer'] = None
    _lock: threading.Lock = threading.Lock() # [Add] 類別層級鎖

    def __init__(self):
        logger.info("Initializing RAG Container...")
        self.repo = ChromaRepository(
            persist_directory=settings.rag_db_path, 
            embedding_model=settings.rag_embed_model
        )
        
        # [SRE Fix] 預熱：在容器啟動期間強制初始化 DB
        # 這將延遲成本從「第一次使用者請求」轉移到「應用程式啟動」
        logger.info("Warming up Vector DB connection...")
        _ = self.repo.db 
        
        self.retriever = RetrievalService(repo=self.repo)
        self.ingestor = IngestionService(repo=self.repo)

    @classmethod
    def get_instance(cls) -> 'RAGContainer':
        """使用雙重檢查鎖定 (Double-Checked Locking) 的單例存取器。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None: # Double check inside lock
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """測試用途。"""
        cls._instance = None

def ingest_documents(folder: Optional[str] = None) -> str:
    """
    從 docs 資料夾匯入文件的管理工具。
    """
    target_folder = folder or settings.rag_docs_folder
    container = RAGContainer.get_instance()
    container.ingestor.run_pipeline(target_folder)
    return f"Ingestion complete from {target_folder}"

async def search_knowledge_base(query: str) -> str:
    """
    搜尋內部知識庫 (文件、PDF) 以獲取相關資訊。
    當使用者詢問特定文件或內部資料時使用此工具。
    
    Args:
        query: 搜尋查詢 (例如："退款政策是什麼？", "專案 X 的摘要")。
    """
    container = RAGContainer.get_instance()
    return await container.retriever.query(query)
