import logging
from typing import Tuple
from src.config import settings
from src.rag.adapters.chroma_repository import ChromaRepository
from src.rag.services.retriever import RetrievalService
from src.rag.services.ingestor import IngestionService
from src.tools.knowledge import create_search_tool, create_ingest_tool, SearchTool, IngestTool

logger = logging.getLogger(__name__)

def bootstrap_rag() -> Tuple[SearchTool, IngestTool]:
    """
    RAG 子系統的啟動引導 (Bootstrap)。
    負責初始化所有 RAG 相關的服務與 Repository，並組裝出可用的 Tools。
    
    Returns:
        Tuple[SearchTool, IngestTool]: 已注入依賴的工具函式。
    """
    logger.info("Bootstrapping RAG Subsystem...")
    
    # 1. 初始化 Repository (Infrastructure Layer)
    repo = ChromaRepository(
        persist_directory=settings.rag_db_path, 
        embedding_model=settings.rag_embed_model
    )
    
    # [SRE] 預熱 DB 連線
    logger.info("Warming up Vector DB connection...")
    _ = repo.db
    
    # 2. 初始化 Services (Application Layer)
    retriever = RetrievalService(repo=repo)
    ingestor = IngestionService(repo=repo)
    
    # 3. 建立 Tools (Presentation/Interface Layer)
    # 透過 Factory Function 將 Service 注入到 Tool 中
    search_tool = create_search_tool(retriever, ingestor)
    ingest_tool = create_ingest_tool(ingestor)
    
    logger.info("RAG Subsystem ready.")
    return search_tool, ingest_tool
