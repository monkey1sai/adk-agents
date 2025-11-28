import asyncio
import logging
from src.core.factory import AgentFactory
from src.core.bootstrap import bootstrap_system
from src.config import settings

# 設定 Log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    print(f"=== Agent System Starting ({settings.adk_framework.value.upper()} Mode) ===")
    
    # [Bootstrap] 系統啟動引導 (註冊 + 預熱)
    bootstrap_system()
    
    try:
        # 1. 透過工廠取得 Runner (Strategy Pattern)
        runner = AgentFactory.create_runner()
        
        # 2. 執行查詢
        #query = "人工智慧最新研究進展 google在 2024 在最新發展"
        query = "請問吳東凌在人工智慧發展報告中負責什麼？"
        session_id = "session_demo_001" # 模擬 Session ID
        print(f"\n[User]: {query} (Session: {session_id})")
        
        response = await runner.run(query, session_id=session_id)
        
        print(f"\n[Agent]: {response}")
        
    except ImportError as e:
        print(f"\n[Config Error]: {e}")
        print("Tip: Check your .env file or install missing packages.")
    except Exception as e:
        print(f"\n[Error]: {e}")
        logging.exception("Full traceback:")

if __name__ == "__main__":
    asyncio.run(main())
