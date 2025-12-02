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
    print(f"=== Agent 系統啟動中 ({settings.adk_framework.value.upper()} 模式) ===")
    
    # [Bootstrap] 系統啟動引導 (註冊 + 預熱)
    bootstrap_system()
    
    try:
        # 1. 透過工廠取得 Runner (Strategy Pattern)
        runner = AgentFactory.create_runner()
        
        # 2. 執行查詢
        #query = "人工智慧最新的研究進展是什麼？"
        query = "請問吳東凌在人工智慧發展報告中負責什麼？"
        session_id = "session_demo_001" # 模擬 Session ID
        print(f"\n[使用者]: {query} (工作階段: {session_id})")
        response = await runner.run(query, session_id=session_id)
        print(f"\n[Agent]: {response}")
        
    except ImportError as e:
        print(f"\n[設定錯誤]: {e}")
        print("提示: 請檢查您的 .env 檔案或安裝缺少的套件。")
    except Exception as e:
        print(f"\n[錯誤]: {e}")
        logging.exception("完整追蹤:")

if __name__ == "__main__":
    asyncio.run(main())
