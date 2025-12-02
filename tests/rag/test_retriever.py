import unittest
from unittest.mock import AsyncMock, MagicMock
from src.rag.services.retriever import RetrievalService
from src.rag.domain.models import Chunk, SearchResult

class TestRetrievalService(unittest.IsolatedAsyncioTestCase):
    async def test_query_success(self):
        # Arrange
        mock_repo = AsyncMock()
        
        # Mock search results
        mock_chunk = Chunk(content="測試內容", metadata={"source": "測試文件.txt"})
        mock_result = SearchResult(chunk=mock_chunk, score=0.9)
        mock_repo.search.return_value = [mock_result]
        
        service = RetrievalService(repo=mock_repo)
        
        # Act
        result = await service.query("測試查詢")
        
        # Assert
        self.assertIn("測試內容", result)
        self.assertIn("測試文件.txt", result)
        mock_repo.search.assert_called_once_with("測試查詢", k=4)

    async def test_query_no_results(self):
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.search.return_value = []
        
        service = RetrievalService(repo=mock_repo)
        
        # Act
        result = await service.query("測試查詢")
        
        # Assert
        self.assertEqual(result, "在知識庫中找不到相關資訊。")

    async def test_query_error_handling(self):
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.search.side_effect = Exception("資料庫錯誤")
        
        service = RetrievalService(repo=mock_repo)
        
        # Act
        # [Fix] 使用 assertLogs 捕捉預期的錯誤日誌，避免汙染測試輸出
        with self.assertLogs(level='ERROR') as cm:
            result = await service.query("測試查詢")
        
        # Assert
        self.assertIn("錯誤: 目前無法存取知識庫", result)
        # 驗證確實有記錄錯誤日誌
        self.assertTrue(any("RAG Retrieval failed" in output for output in cm.output))

    async def test_query_custom_k(self):
        # [Test] 驗證參數傳遞 (k值)
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.search.return_value = []
        
        service = RetrievalService(repo=mock_repo)
        
        # Act
        await service.query("測試查詢", k=10)
        
        # Assert
        mock_repo.search.assert_called_once_with("測試查詢", k=10)

if __name__ == '__main__':
    unittest.main()
