import logging
import sys
from typing import Callable, Awaitable, Optional
from src.rag.services.retriever import RetrievalService
from src.rag.services.ingestor import IngestionService
from src.config import settings

logger = logging.getLogger(__name__)

# 定義 Tool 的型別別名
SearchTool = Callable[[str], Awaitable[str]]
# [Fix] 加回 IngestTool 定義，解決 ImportError
IngestTool = Callable[[Optional[str]], str]


def create_search_tool(retriever: RetrievalService, ingestor: IngestionService) -> SearchTool:
    
    async def search_knowledge_base(query: str) -> str:
        """
        Search the internal knowledge base (documents, PDFs) for relevant information.
        Use this tool when the user asks about specific documents or internal data.
        
        Args:
            query: The search query (e.g., "What is the refund policy?", "Summary of Project X").
        """
        # [DEBUG] 強制輸出，確認工具真的被呼叫
        print(f"\n[DEBUG] >>> 工具 'search_knowledge_base' 被呼叫! Query: {query}")
        logger.info(f"🛠️ Tool Called: search_knowledge_base with query='{query}'")

        try:
            # 1. 執行匯入 (快速檢查)
            print("[DEBUG] 步驟 1: 檢查新檔案匯入...")
            # 注意：如果這裡報錯，會被下面的 except 捕獲
            ingestor.run_pipeline(settings.rag.docs_folder)
            print("[DEBUG] 步驟 1: 匯入檢查完成。")
        except Exception as e:
            msg = f"自動匯入檢查失敗: {e}"
            print(f"[DEBUG] ⚠️ {msg}")
            logger.error(msg)
            # 匯入失敗不應阻止搜尋，繼續往下執行

        try:
            # 2. 執行檢索
            print(f"[DEBUG] 步驟 2: 呼叫 Retriever 進行搜尋...")
            result = await retriever.query(query)
            print(f"[DEBUG] 步驟 2: 搜尋完成。結果長度: {len(result)} 字元")
            
            # [DEBUG] 顯示檢索內容摘要，確認 Agent 到底看到了什麼
            preview = result[:500].replace('\n', ' ') + "..." if len(result) > 500 else result.replace('\n', ' ')
            print(f"[DEBUG] 檢索內容預覽: {preview}")

            if not result or "找不到" in result:
                print("[DEBUG] ⚠️ 警告: Retriever 回傳了空結果或找不到訊息")
            
            return result
        except Exception as e:
            msg = f"檢索執行失敗: {e}"
            print(f"[DEBUG] ❌ {msg}")
            logger.error(msg)
            return f"系統錯誤: {msg}"

    return search_knowledge_base

def create_ingest_tool(ingestor: IngestionService):
    # 為了避免 Agent 混淆，這裡只回傳簡單的實作
    def ingest_documents(folder: Optional[str] = None) -> str:
        return "請使用 search_knowledge_base 工具，它會自動處理匯入。"
    return ingest_documents
