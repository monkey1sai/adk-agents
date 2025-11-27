import logging
import asyncio
from typing import List
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
try:
    from langchain_core.documents import Document as LangChainDocument
except ImportError:
    from langchain.docstore.document import Document as LangChainDocument

from src.rag.domain.models import Chunk, SearchResult
from src.rag.ports.repository import VectorStoreRepository

logger = logging.getLogger(__name__)

class ChromaRepository(VectorStoreRepository):
    """
    Adapter implementation for ChromaDB using LangChain.
    """
    
    def __init__(self, persist_directory: str, embedding_model: str):
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self._db = None
        
    @property
    def db(self):
        """Lazy initialization of the DB connection."""
        if self._db is None:
            logger.info(f"Initializing ChromaDB at {self.persist_directory} with model {self.embedding_model}")
            embeddings = OllamaEmbeddings(model=self.embedding_model)
            self._db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=embeddings
            )
        return self._db

    def add_chunks(self, chunks: List[Chunk]) -> None:
        """
        Converts domain Chunks to LangChain Documents and persists them.
        """
        lc_docs = [
            LangChainDocument(page_content=c.content, metadata=c.metadata)
            for c in chunks
        ]
        self.db.add_documents(lc_docs)
        self.db.persist()
        logger.info(f"Persisted {len(chunks)} chunks to ChromaDB.")

    async def search(self, query: str, k: int = 4) -> List[SearchResult]:
        """
        Performs similarity search asynchronously and maps results back to domain objects.
        """
        # Chroma.similarity_search_with_score returns (Document, score)
        # Note: Chroma scores are distances (lower is better), but LangChain might normalize them depending on version.
        # Usually we just return them as is.
        
        # Run blocking DB call in a thread pool
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None, 
            lambda: self.db.similarity_search_with_score(query, k=k)
        )
        
        domain_results = []
        for doc, score in results:
            chunk = Chunk(
                content=doc.page_content,
                metadata=doc.metadata
            )
            domain_results.append(SearchResult(chunk=chunk, score=score))
            
        return domain_results
