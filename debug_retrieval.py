import asyncio
import logging
import sys
from src.rag.adapters.chroma_repository import ChromaRepository
from src.config import settings

# 設定 Log 顯示
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose():
    print("=== 🔍 RAG 檢索層診斷工具 ===")
    
    # 1. 初始化 Repository
    print(f"1. 連線至資料庫: {settings.rag.db_path}")
    print(f"   使用模型: {settings.rag.embed_model}")
    
    try:
        repo = ChromaRepository(
            persist_directory=settings.rag.db_path,
            embedding_model=settings.rag.embed_model
        )
        # 強制觸發初始化
        db = repo.db
        print("   ✅ 資料庫連線成功")
    except Exception as e:
        print(f"   ❌ 資料庫連線失敗: {e}")
        return

    # 2. 檢查資料庫存量
    try:
        count = db._collection.count()
        print(f"2. 資料庫現有區塊數: {count}")
        if count == 0:
            print("   ❌ 警告: 資料庫是空的！請確認 Ingestion 是否真的成功。")
        else:
            print("   ✅ 資料庫內有資料。")
            # 列出前幾筆資料的 metadata 以確認來源
            peek = db._collection.peek(limit=3)
            print(f"   樣本 Metadata: {peek['metadatas']}")
    except Exception as e:
        print(f"   ❌ 無法讀取資料庫狀態: {e}")

    # 3. 執行實際搜尋
    query = "人工智慧"
    print(f"\n3. 執行測試搜尋: '{query}'")
    try:
        # 搜尋前 5 筆
        results = await repo.search(query, k=5)
        
        if not results:
            print("   ❌ 搜尋結果: [空] (找不到任何匹配)")
        else:
            print(f"   ✅ 搜尋結果: 找到 {len(results)} 筆")
            for i, res in enumerate(results):
                print(f"   --- 結果 {i+1} (分數: {res.score:.4f}) ---")
                print(f"   來源: {res.chunk.metadata.get('source', 'unknown')}")
                print(f"   內容: {res.chunk.content[:50]}...") # 只顯示前50字
    except Exception as e:
        print(f"   ❌ 搜尋執行失敗: {e}")

if __name__ == "__main__":
    # Windows 下的 asyncio 策略調整
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(diagnose())