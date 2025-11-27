import logging
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.config import settings
from src.tools.weather import get_weather

logger = logging.getLogger(__name__)

class GoogleProvider:
    """
    Google ADK 實作
    """
    def __init__(self):
        # 1. 初始化 Session Service (用於管理對話狀態)
        self.session_service = InMemorySessionService()
        
        # 2. 建立 LLM
        # 直接使用 SDK 提供的 LiteLlm，不需要自定義 Adapter
        # 設定值會從 config.py 讀取 (包含 openai/ 前綴與 Proxy URL)
        self.model = self._create_llm()
        
        # 3. 建立 Agent
        self.agent = self._create_agent()
        
        # 4. 建立 Runner (綁定 Agent, App 與 Session Service)
        self.runner = Runner(
            agent=self.agent,
            app_name=settings.app_name,
            session_service=self.session_service
        )

    def _create_llm(self) -> LiteLlm:
        return LiteLlm(
            model=settings.model_name, # e.g. "openai/ollama/qwen2.5"
            base_url=settings.base_url, # e.g. "http://localhost:4000"
            api_key=settings.api_key
        )

    def _create_agent(self) -> Agent:
        return Agent(
            name="GoogleWeatherBot",
            model=self.model,
            instruction="你是一個使用 Google ADK 的氣象助理。請用繁體中文回答。",
            tools= [get_weather]
        )

    async def run(self, user_query: str):
        """執行 Agent 並回傳結果"""
        print(f"🚀 [Google ADK] Running agent with query: {user_query}")
        
        # 固定測試用的 User 與 Session ID
        user_id = "user_1"
        session_id = "session_1"
        
        # 確保 Session 存在
        try:
            await self.session_service.create_session(
                app_name=settings.app_name,
                user_id=user_id,
                session_id=session_id
            )
        except Exception:
            # 如果 Session 已存在可能會報錯，這裡選擇忽略或可做檢查
            pass

        # 建構 Google ADK 規範的訊息物件
        user_msg = types.Content(role="user", parts=[types.Part(text=user_query)])
        
        final_response = ""
        
        # 執行對話 (Event Stream)
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_msg
        ):
            # 處理事件流，抓取最終回應
            # 這裡簡化處理：假設最後一個含有 text 的 event 是最終回應
            if hasattr(event, 'content') and event.content and event.content.parts:
                 part = event.content.parts[0]
                 if hasattr(part, 'text') and part.text:
                    final_response = part.text
        
        return final_response