import asyncio
import logging
from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from src.config import Settings
from src.tools.weather import get_weather

logger = logging.getLogger(__name__)

class MicrosoftProvider:
    """
    Microsoft ADK (agents package) 實作
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = self._create_llm()
        self.agent = self._create_agent()

    def _create_llm(self) -> LitellmModel:
        """建立符合 LiteLLM Proxy 規範的模型實例"""
        return LitellmModel(
            model=self.settings.model_name,
            api_key=self.settings.api_key,
            base_url=self.settings.base_url
        )

    def _create_agent(self) -> Agent:
        return Agent(
            name="MicrosoftWeatherBot",
            model=self.model,
            instructions="你是一個使用 Microsoft ADK 的氣象助理。請用繁體中文回答。",
            tools=[function_tool(get_weather)] # 直接使用工具函式
        )

    async def run(self, user_query: str, session_id: str = "default") -> str:
        """執行 Agent 並回傳結果"""
        logger.info(f"[Microsoft ADK] Running agent with query: {user_query} (Session: {session_id})")
        
        # [TODO] Microsoft ADK 的 Runner 目前是 Stateless 的。
        # 若要支援多輪對話，需要在此處整合外部記憶體 (如 Redis) 或自行維護 History。
        # 目前實作僅支援單輪對話 (Single-turn)，session_id 僅用於 Log 追蹤。
        
        result = await Runner.run(self.agent, user_query)
        return result.final_output
