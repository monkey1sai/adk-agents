import asyncio
import logging
from src.rag.domain.models import Chunk
from src.tools.knowledge import RAGContainer

# 設定 Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def ingest_data():
    """
    將範例資料寫入知識庫 (Ingestion)。
    """
    print("🚀 開始建立知識庫資料...")

    # 1. 取得 RAG 容器 (Singleton)
    # 這會自動初始化 ChromaDB 連線與 Embedding 模型
    rag = RAGContainer.get_instance()
    
    # 2. 準備要寫入的資料 (Chunks)
    # 在真實場景中，這裡通常會搭配 Document Loader (PDF, Web) 與 Text Splitter
    knowledge_base_data = [
        Chunk(
            content="Google DeepMind 發布了 Gemini 1.5 Pro，支援 100 萬 token 的 Context Window，能夠處理大量的文字、程式碼與影片資訊。",
            metadata={"source": "tech_news", "date": "2024-02-15", "topic": "AI"}
        ),
        Chunk(
            content="Microsoft Copilot 整合了 GPT-4 Turbo，並在 Windows 11 中提供系統級別的 AI 助理功能，可以協助使用者更改設定、整理視窗。",
            metadata={"source": "ms_blog", "date": "2024-03-01", "topic": "AI"}
        ),
        Chunk(
            content="Meta 推出了 Llama 3 開源模型，在推論速度與程式碼生成能力上有顯著提升，並採用了更有效率的訓練架構。",
            metadata={"source": "meta_ai", "date": "2024-04-10", "topic": "AI"}
        ),
        Chunk(
            content="NVIDIA GTC 2024 大會上，黃仁勳發表了 Blackwell 架構 GPU (B200)，專為兆級參數的 AI 模型訓練與推論設計。",
            metadata={"source": "nvidia_news", "date": "2024-03-18", "topic": "Hardware"}
        ),
        Chunk(
            content="Python 3.13 預計將移除 GIL (Global Interpreter Lock) 的限制，這將大幅提升 Python 在多執行緒運算上的效能。",
            metadata={"source": "python_org", "date": "2024-05-01", "topic": "Programming"}
        )
    ]

    # 3. 寫入資料庫
    # 透過 RAG Service 的 add_documents 方法 (它會呼叫 Repository 的 add_chunks)
    # 注意：RAGContainer 目前暴露的是 service 屬性
    print(f"📦 準備寫入 {len(knowledge_base_data)} 筆資料...")
    
    # 由於 RAGService 目前可能沒有直接暴露 add_chunks，我們直接操作 repository
    # 在正式架構中，應該透過 Service Layer 呼叫
    rag.repo.add_chunks(knowledge_base_data)
    
    print("✅ 資料寫入完成！")
    print("💡 現在你可以重新執行 Agent，問它關於 'Gemini 1.5' 或 'Llama 3' 的問題了。")

if __name__ == "__main__":
    asyncio.run(ingest_data())
