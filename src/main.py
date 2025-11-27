import asyncio
import logging
from src.core.factory import AgentFactory
from src.config import settings

# 設定 Log
logging.basicConfig(level=logging.ERROR)

async def main():
    print(f"=== Agent System Starting ({settings.adk_framework.value.upper()} Mode) ===")
    
    try:
        # 1. 透過工廠取得 Runner (Strategy Pattern)
        runner = AgentFactory.create_runner()
        
        # 2. 執行查詢
        query = "台北的天氣如何？"
        print(f"\n👤 User: {query}")
        
        response = await runner.run(query)
        
        print(f"\n🤖 Agent: {response}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
