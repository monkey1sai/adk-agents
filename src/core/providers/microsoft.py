import asyncio
from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from src.config import settings
from src.tools.weather import get_weather

class MicrosoftProvider:
    """
    Microsoft ADK (agents package) 實作
    """
    def __init__(self):
        self.model = self._create_llm()
        self.agent = self._create_agent()

    def _create_llm(self) -> LitellmModel:
        """建立符合 LiteLLM Proxy 規範的模型實例"""
        return LitellmModel(
            model=settings.model_name,
            api_key=settings.api_key,
            base_url=settings.base_url
        )

    def _create_agent(self) -> Agent:
        return Agent(
            name="MicrosoftWeatherBot",
            model=self.model,
            instructions="你是一個使用 Microsoft ADK 的氣象助理。請用繁體中文回答。",
            tools=[function_tool(get_weather)] # 直接使用工具函式
        )

    async def run(self, user_query: str):
        """執行 Agent 並回傳結果"""
        print(f"🚀 [Microsoft ADK] Running agent with query: {user_query}")
        result = await Runner.run(self.agent, user_query)
        return result.final_output
