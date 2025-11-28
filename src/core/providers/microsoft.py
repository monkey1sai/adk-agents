import asyncio
import logging
from pathlib import Path
from typing import List, Any
from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from src.config import Settings
from src.tools.weather import get_weather
from agents import set_tracing_disabled
# [Refactor] 不再直接 import search_knowledge_base，改由 DI 注入
# from src.tools.knowledge import search_knowledge_base

set_tracing_disabled(True)
logger = logging.getLogger(__name__)

class MicrosoftProvider:
    """
    Microsoft ADK (agents package) 實作
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.tools = [get_weather] # 預設工具
        self.model = self._create_llm()
        self.agent = self._create_agent()

    def set_tools(self, tools: List[Any]):
        """
        [DI] 接收外部注入的工具列表。
        """
        logger.info(f"Injecting {len(tools)} tools into MicrosoftProvider...")
        self.tools = [get_weather] + tools
        # 重建 Agent 以套用新工具
        self.agent = self._create_agent()

    def _create_llm(self) -> LitellmModel:
        """建立符合 LiteLLM Proxy 規範的模型實例"""
        return LitellmModel(
            model=self.settings.model_name,
            api_key=self.settings.api_key,
            base_url=self.settings.base_url
        )

    def _load_instructions(self) -> str:
        """從外部檔案載入 System Prompt"""
        try:
            # 取得目前檔案 (microsoft.py) 的目錄
            current_dir = Path(__file__).parent
            # 往上兩層找到 src，再進入 prompts
            prompt_path = current_dir.parent.parent / "prompts" / "microsoft_agent.md"
            
            if not prompt_path.exists():
                logger.warning(f"Prompt file not found at {prompt_path}, using default instructions.")
                return "你是一個使用 Microsoft ADK 的氣象助理。請用繁體中文回答。"
                
            return prompt_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error loading instructions: {e}")
            return "你是一個使用 Microsoft ADK 的氣象助理。請用繁體中文回答。"

    def _create_agent(self) -> Agent:
        # Microsoft ADK 需要用 function_tool 包裝
        # 這裡我們假設注入進來的 tools 已經是 Callable，需要被包裝
        # 或者如果注入的是已經包裝好的 Tool 物件，則需要判斷
        
        wrapped_tools = []
        for tool in self.tools:
            # 簡單判斷：如果是函式就包裝，不然就直接用
            if callable(tool):
                wrapped_tools.append(function_tool(tool))
            else:
                wrapped_tools.append(tool)

        return Agent(
            name="MicrosoftWeatherBot",
            model=self.model,
            instructions=self._load_instructions(),
            tools=wrapped_tools 
        )

    async def run(self, user_query: str, session_id: str = "default") -> str:
        """執行 Agent 並回傳結果"""
        logger.info(f"[Microsoft ADK] Running agent with query: {user_query} (Session: {session_id})")
        
        # [TODO] Microsoft ADK 的 Runner 目前是 Stateless 的。
        # 若要支援多輪對話，需要在此處整合外部記憶體 (如 Redis) 或自行維護 History。
        # 目前實作僅支援單輪對話 (Single-turn)，session_id 僅用於 Log 追蹤。
        
        result = await Runner.run(self.agent, user_query)
        return result.final_output
