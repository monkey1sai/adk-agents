import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import logging
from src.rag.adapters.chroma_repository import ChromaRepository
from src.rag.domain.models import Chunk, SearchResult

class TestChromaRepository(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        # [Fix] 抑制測試期間的 Log 輸出，保持測試報告乾淨
        logging.disable(logging.CRITICAL)
        self.addCleanup(lambda: logging.disable(logging.NOTSET))

        # [Fix] 使用 patcher.start() 確保 patch 在測試方法執行期間仍然有效
        # 如果只裝飾 setUp，patch 只在 setUp 執行期間有效，測試方法執行時已經失效
        
        self.chroma_patcher = patch('src.rag.adapters.chroma_repository.Chroma')
        self.embeddings_patcher = patch('src.rag.adapters.chroma_repository.OllamaEmbeddings')
        
        self.mock_chroma_cls = self.chroma_patcher.start()
        self.mock_embeddings_cls = self.embeddings_patcher.start()
        
        # 確保測試結束後停止 patch
        self.addCleanup(self.chroma_patcher.stop)
        self.addCleanup(self.embeddings_patcher.stop)
        
        # 設定 Mock 的回傳值
        self.mock_embeddings_instance = self.mock_embeddings_cls.return_value
        self.mock_chroma_instance = self.mock_chroma_cls.return_value
        
        # 初始化待測物件
        self.repo = ChromaRepository(persist_directory="test_db", embedding_model="test_model")

    def test_initialization(self):
        # Access db to trigger lazy init
        # 這會觸發 self.repo.db -> 呼叫 OllamaEmbeddings() 和 Chroma()
        _ = self.repo.db
        
        # 驗證是否使用了正確的參數呼叫 Mock 類別
        self.mock_embeddings_cls.assert_called_with(model="test_model")
        self.mock_chroma_cls.assert_called_once()

    def test_initialization_idempotency(self):
        # [Test] 驗證 Lazy Initialization 的冪等性
        # 第一次存取
        db1 = self.repo.db
        # 第二次存取
        db2 = self.repo.db
        
        # 驗證物件是同一個實例
        self.assertIs(db1, db2)
        # 驗證建構子只被呼叫一次
        self.mock_chroma_cls.assert_called_once()
        self.mock_embeddings_cls.assert_called_once()

    def test_add_chunks(self):
        # Arrange
        # 強制初始化 db，這會使用我們的 Mock 物件
        _ = self.repo.db
        
        chunks = [
            Chunk(content="區塊1", metadata={"source": "文件1"}),
            Chunk(content="區塊2", metadata={"source": "文件2"})
        ]
        
        # Act
        self.repo.add_chunks(chunks)
        
        # Assert
        # 驗證是否呼叫了 Mock Chroma 實例的 add_documents 方法
        self.mock_chroma_instance.add_documents.assert_called_once()
        call_args = self.mock_chroma_instance.add_documents.call_args[0][0]
        self.assertEqual(len(call_args), 2)
        self.assertEqual(call_args[0].page_content, "區塊1")

    def test_add_chunks_empty(self):
        # [Test] 驗證空輸入的處理
        _ = self.repo.db
        self.repo.add_chunks([])
        
        # 驗證 add_documents 被呼叫且參數為空列表 (依據目前實作)
        self.mock_chroma_instance.add_documents.assert_called_once()
        call_args = self.mock_chroma_instance.add_documents.call_args[0][0]
        self.assertEqual(call_args, [])

    def test_delete_chunks_by_source(self):
        # [Test] 驗證刪除邏輯
        _ = self.repo.db
        
        # Mock 底層 collection
        mock_collection = MagicMock()
        self.mock_chroma_instance._collection = mock_collection
        
        source_path = "path/to/file.txt"
        self.repo.delete_chunks_by_source(source_path)
        
        # 驗證是否呼叫了底層 collection 的 delete 方法
        mock_collection.delete.assert_called_once_with(where={"source": source_path})

    async def test_search(self):
        # Arrange
        _ = self.repo.db
        
        # Mock search results from Chroma (Document, score)
        mock_doc = MagicMock()
        mock_doc.page_content = "找到的內容"
        mock_doc.metadata = {"source": "找到的文件"}
        
        # 設定 similarity_search_with_score 的回傳值
        self.mock_chroma_instance.similarity_search_with_score.return_value = [(mock_doc, 0.85)]
        
        # Act
        results = await self.repo.search("查詢", k=2)
        
        # Assert
        self.mock_chroma_instance.similarity_search_with_score.assert_called_with("查詢", k=2)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], SearchResult)
        self.assertEqual(results[0].chunk.content, "找到的內容")
        self.assertEqual(results[0].score, 0.85)

if __name__ == '__main__':
    unittest.main()
