import asyncio
import shutil
import os
import sys
import logging
import gc

# [Fix] Add project root to sys.path to resolve 'src' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.rag.adapters.chroma_repository import ChromaRepository
from src.rag.services.retriever import RetrievalService
from src.rag.domain.models import Chunk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_DB_PATH = "test_vector_db_e2e"

async def main():
    logger.info("開始執行 E2E RAG 測試...")
    
    # Clean up previous test run
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)
        
    try:
        # 1. Initialize Repository
        # Note: This requires a running Ollama instance with 'embeddinggemma:latest' or similar model
        # If not available, this will fail.
        repo = ChromaRepository(
            persist_directory=TEST_DB_PATH,
            embedding_model="embeddinggemma:latest" 
        )
        
        # 2. Ingest Data
        logger.info("正在匯入測試資料...")
        chunks = [
            Chunk(content="The capital of France is Paris.", metadata={"source": "geography.txt"}),
            Chunk(content="Python is a programming language.", metadata={"source": "tech.txt"}),
            Chunk(content="The sky is blue.", metadata={"source": "nature.txt"})
        ]
        repo.add_chunks(chunks)
        
        # 3. Initialize Service
        service = RetrievalService(repo=repo)
        
        # 4. Test Retrieval
        query = "What is the capital of France?"
        logger.info(f"正在查詢: {query}")
        result = await service.query(query)
        
        logger.info("--- 結果 ---")
        logger.info(result)
        
        # 5. Verification
        if "Paris" in result:
            logger.info("✅ E2E 測試通過: 在結果中找到 'Paris'。")
        else:
            logger.error("❌ E2E 測試失敗: 未找到 'Paris'。")
            
    except Exception as e:
        logger.error(f"❌ E2E 測試失敗，錯誤: {e}")
    finally:
        # Cleanup
        logger.info("正在清理資源...")
        
        # [Fix] Windows File Lock Issue
        # 1. 明確刪除 repo 物件，斷開與 DB 的連結
        if 'repo' in locals():
            del repo
            
        # 2. 強制執行垃圾回收，確保 ChromaDB 釋放檔案鎖定
        gc.collect()
        
        # 3. 等待一小段時間讓 OS 釋放鎖定 (非必須，但保險)
        await asyncio.sleep(0.1)

        if os.path.exists(TEST_DB_PATH):
            try:
                shutil.rmtree(TEST_DB_PATH)
                logger.info("已清理測試資料庫。")
            except PermissionError:
                logger.warning("⚠️ 由於檔案鎖定，無法立即刪除測試資料庫。您可能需要手動刪除。")

if __name__ == "__main__":
    asyncio.run(main())
