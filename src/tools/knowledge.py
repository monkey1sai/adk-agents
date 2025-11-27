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
    Simple Dependency Injection Container for RAG subsystem.
    Manages the lifecycle of Repository and Services.
    """
    _instance: Optional['RAGContainer'] = None
    _lock: threading.Lock = threading.Lock() # [Add] Class-level lock

    def __init__(self):
        logger.info("Initializing RAG Container...")
        self.repo = ChromaRepository(
            persist_directory=settings.rag_db_path, 
            embedding_model=settings.rag_embed_model
        )
        
        # [SRE Fix] Warm-up: Force DB initialization during container startup
        # This shifts the latency cost from "First User Request" to "App Startup"
        logger.info("Warming up Vector DB connection...")
        _ = self.repo.db 
        
        self.retriever = RetrievalService(repo=self.repo)
        self.ingestor = IngestionService(repo=self.repo)

    @classmethod
    def get_instance(cls) -> 'RAGContainer':
        """Singleton accessor with Double-Checked Locking."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None: # Double check inside lock
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """For testing purposes."""
        cls._instance = None

def ingest_documents(folder: Optional[str] = None) -> str:
    """
    Admin tool to ingest documents from the docs folder.
    """
    target_folder = folder or settings.rag_docs_folder
    container = RAGContainer.get_instance()
    container.ingestor.run_pipeline(target_folder)
    return f"Ingestion complete from {target_folder}"

async def search_knowledge_base(query: str) -> str:
    """
    Search the internal knowledge base (documents, PDFs) for relevant information.
    Use this tool when the user asks about specific documents or internal data.
    
    Args:
        query: The search query (e.g., "What is the refund policy?", "Summary of project X").
    """
    container = RAGContainer.get_instance()
    return await container.retriever.query(query)
