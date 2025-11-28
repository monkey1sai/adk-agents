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
    使用 LangChain 的 ChromaDB 適配器實作。
    """
    
    def __init__(self, persist_directory: str, embedding_model: str):
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self._db = None
        
    @property
    def db(self):
        """資料庫連線的延遲初始化 (Lazy initialization)。"""
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
        將領域 Chunks 轉換為 LangChain Documents 並持久化。
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
        非同步執行相似度搜尋並將結果映射回領域物件。
        """
        # Chroma.similarity_search_with_score 回傳 (Document, score)
        # 注意：Chroma 的分數是距離 (越低越好)，但 LangChain 可能會根據版本進行正規化。
        # 通常我們直接回傳即可。
        
        # 在執行緒池中執行阻塞的 DB 呼叫
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
