import logging
import asyncio
import warnings
from typing import List

# [Google Engineer] 忽略 LangChain 的 DeprecationWarning 以保持輸出乾淨
# 這是為了回應 "忽略版本問題" 的需求，讓我們專注於功能本身
# 未來若升級套件解決衝突後，可移除此過濾器
try:
    from langchain_core._api.deprecation import LangChainDeprecationWarning
    warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
except ImportError:
    pass

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
    ChromaDB 的適配器 (Adapter) 實作。
    
    [架構設計 - 未來遷移指南]
    此類別實作了 `VectorStoreRepository` Protocol (Port)。
    目前的實作依賴 `ChromaDB`。
    
    若未來要遷移至 PostgreSQL (pgvector)：
    1. 建立新檔案 `src/rag/adapters/pgvector_repository.py`
    2. 建立 class `PgVectorRepository` 並實作 `add_chunks` 與 `search` 方法
    3. 在 `src/rag/bootstrap.py` 中，將 `ChromaRepository` 替換為 `PgVectorRepository`
    
    由於依賴反轉 (DIP)，上層的 Ingestor 和 Retriever 完全不需要修改程式碼。
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
        # 嘗試呼叫 persist，若新版移除則忽略
        if hasattr(self.db, "persist"):
            self.db.persist()
        logger.info(f"Persisted {len(chunks)} chunks to ChromaDB.")

    def delete_chunks_by_source(self, source_path: str) -> None:
        """
        根據來源路徑刪除 Chunks。
        ChromaDB 支援透過 metadata 過濾刪除。
        """
        try:
            # 注意：LangChain 的 Chroma wrapper 可能沒有直接暴露 delete 方法，
            # 但底層的 _collection 有。
            # 或者使用 db.delete(ids=...) 如果知道 IDs。
            # 這裡我們嘗試使用 db._collection.delete(where=...)
            
            # 正規化路徑分隔符號以匹配 metadata
            # 注意：metadata 中的 source 可能是絕對路徑或相對路徑，視 loader 而定。
            # 這裡假設 metadata['source'] 儲存的是完整路徑。
            
            logger.info(f"Deleting chunks for source: {source_path}")
            
            # LangChain Chroma 封裝的 delete 方法通常接受 ids。
            # 若要依 metadata 刪除，需存取底層 collection。
            if hasattr(self.db, "_collection"):
                self.db._collection.delete(where={"source": source_path})
                logger.info(f"Deleted chunks for {source_path} from ChromaDB.")
            else:
                logger.warning("Could not access underlying Chroma collection for deletion.")
                
        except Exception as e:
            logger.error(f"Failed to delete chunks for {source_path}: {e}")

    async def search(self, query: str, k: int = 4) -> List[SearchResult]:
        """
        非同步執行相似度搜尋並將結果映射回領域物件。
        """
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
