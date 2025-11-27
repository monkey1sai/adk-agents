import asyncio
import logging

# Google ADK 核心元件引用
# LiteLlm: 用於連接支援 OpenAI 協定的模型 (如透過 Proxy 的 Ollama)
from google.adk.models.lite_llm import LiteLlm
# Agent: 定義 AI 的人格、指令與能力 (Tools)
from google.adk.agents import Agent
# Runner: 執行單元，負責協調 Agent 與 Session 之間的互動
from google.adk.runners import Runner
# Session: 管理對話狀態與歷史紀錄 (InMemory 僅供測試用，生產環境應使用 Redis/DB)
from google.adk.sessions import InMemorySessionService
# Types: Google GenAI 的標準資料型別
from google.genai import types

# 設定 Log 格式，保持輸出乾淨
logging.basicConfig(level=logging.WARNING)

# ----------------------------------------------------------------
# 1. 工具定義 (Tools)
# ----------------------------------------------------------------
# Best Practice: 小模型 (7B) 容易搞混複雜的 JSON 結構。
# 建議使用扁平參數 (Flat Arguments) 並回傳簡單字串。
def get_weather(city: str) -> str:
    """
    查詢指定城市的天氣狀況。
    
    Args:
        city: 城市名稱 (例如: Taipei, New York)
    """
    print(f"🛠️  [Tool] 正在查詢 {city} 的天氣...")
    
    # 模擬資料庫
    mock_data = {
        "new york": "晴朗, 25°C",
        "taipei": "多雲, 28°C",
        "london": "下雨, 15°C"
    }
    
    result = mock_data.get(city.lower(), "未知天氣")
    return f"{city} 的天氣是: {result}"

# ----------------------------------------------------------------
# 2. 主程式邏輯
# ----------------------------------------------------------------
async def main():
    print("=== Google ADK Agent 啟動 (LiteLLM + Ollama) ===\n")

    # --- A. 模型設定 (Model Setup) ---
    # 使用 LiteLLM Proxy 連接本地 Ollama
    # model: 必須加上 "openai/" 前綴，強制 ADK 使用 OpenAI Client 協定
    # base_url: 指向 Docker 內的 LiteLLM Proxy (Port 4000)
    llm_model = LiteLlm(
        model="openai/ollama/qwen2.5",
        base_url="http://localhost:4000",
        api_key="fake-key" # Proxy 不驗證，但 Client 端必填
    )

    # --- B. Agent 設定 (Agent Setup) ---
    # 定義 Agent 的核心屬性
    agent = Agent(
        name="WeatherBot",
        model=llm_model,
        instruction="你是一個專業的氣象助理。請使用繁體中文回答用戶的問題。",
        tools=[get_weather] # 直接傳入 Python 函式，ADK 會自動生成 Schema
    )

    # --- C. 執行環境設定 (Runner & Session) ---
    # 初始化 Session 服務
    session_service = InMemorySessionService()
    
    # 定義 App 與 User 資訊 (用於區隔對話歷史)
    APP_NAME = "weather_app"
    USER_ID = "user_1"
    SESSION_ID = "session_001"

    # 建立 Runner
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    # 建立一個新的對話 Session
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # --- D. 執行對話 (Execution Loop) ---
    user_query = "先用20個字介紹你自己後, 再告訴我今天紐約的天氣如何？"
    print(f"👤 User: {user_query}")

    # 建構標準訊息物件
    user_msg = types.Content(role="user", parts=[types.Part(text=user_query)])

    # 關鍵概念：Event Stream (事件流)
    # runner.run_async 不會直接回傳結果，而是回傳一個 AsyncGenerator。
    # Agent 的思考、工具呼叫 (FunctionCall)、工具回應 (FunctionResponse)、最終答案
    # 都會以 "Event" 的形式依序產出。
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=user_msg
    ):
        # 這裡可以監聽所有事件，例如 log 工具呼叫
        # if event.function_call: ...
        
        # 我們只關心最終回應 (Final Response)
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                print(f"🤖 Agent: {response_text}")

if __name__ == "__main__":
    asyncio.run(main())