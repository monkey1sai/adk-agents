from typing import List, Any
import logging
from pathlib import Path
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.config import Settings
from src.tools.weather import get_weather
# [Refactor] 不再直接 import search_knowledge_base，改由 DI 注入
# from src.tools.knowledge import search_knowledge_base 

logger = logging.getLogger(__name__)

class GoogleProvider:
    """
    Google ADK 實作
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.tools = [get_weather] # 預設工具
        
        # 1. 初始化 Session Service (用於管理對話狀態)
        self.session_service = InMemorySessionService()
        
        # 2. 建立 LLM
        self.model = self._create_llm()
        
        # 3. 建立 Agent (稍後在 set_tools 中可能會重建，或這裡先建立一個基本的)
        self.agent = self._create_agent()
        
        # 4. 建立 Runner
        self.runner = Runner(
            agent=self.agent,
            app_name=self.settings.app_name,
            session_service=self.session_service
        )

    def set_tools(self, tools: List[Any]):
        """
        [DI] 接收外部注入的工具列表。
        當 Factory 呼叫此方法時，我們會更新 Agent 的工具配置。
        """
        logger.info(f"Injecting {len(tools)} tools into GoogleProvider...")
        # 合併預設工具與注入工具
        self.tools = [get_weather] + tools
        
        # 重新建立 Agent 以套用新工具
        # 注意：Google ADK 的 Agent 物件一旦建立可能無法動態修改 tools，所以這裡重建一個
        self.agent = self._create_agent()
        
        # 更新 Runner 中的 Agent 參考
        self.runner = Runner(
            agent=self.agent,
            app_name=self.settings.app_name,
            session_service=self.session_service
        )

    def _create_llm(self) -> LiteLlm:
        return LiteLlm(
            model=self.settings.model_name, # e.g. "openai/ollama/qwen2.5"
            base_url=self.settings.base_url, # e.g. "http://localhost:4000"
            api_key=self.settings.api_key
        )

    def _load_instructions(self) -> str:
        """從外部檔案載入 System Prompt"""
        try:
            # 取得目前檔案 (google.py) 的目錄
            current_dir = Path(__file__).parent
            # 往上兩層找到 src，再進入 prompts
            prompt_path = current_dir.parent.parent / "prompts" / "google_agent.md"
            
            if not prompt_path.exists():
                logger.warning(f"Prompt file not found at {prompt_path}, using default instructions.")
                return "你是一個使用 Google ADK 知識助理。請用繁體中文回答。"
                
            return prompt_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error loading instructions: {e}")
            return "你是一個使用 Google ADK 知識助理。請用繁體中文回答。"

    def _create_agent(self) -> Agent:
        return Agent(
            name="GoogleWeatherBot",
            model=self.model,
            instruction=self._load_instructions(),
            # [修正] 使用 self.tools (包含注入的工具)
            tools=self.tools 
        )

    async def run(self, user_query: str, session_id: str = "default") -> str:
        """執行 Agent 並回傳結果"""
        logger.info(f"[Google ADK] Running agent with query: {user_query} (Session: {session_id})")
        
        # 使用傳入的 session_id，並固定 user_id (或從外部傳入)
        user_id = "user_1"
        
        # 檢查 Session 是否存在，若不存在則建立
        # 注意：InMemorySessionService 的實作可能不支援 get_session，
        # 這裡為了確保 Session 存在，我們使用 create_session 並忽略 "已存在" 的錯誤。
        # 在生產環境中，應使用 RedisSessionService 並實作正確的 exists/get 邏輯。
        try:
            await self.session_service.create_session(
                app_name=self.settings.app_name,
                user_id=user_id,
                session_id=session_id
            )
        except Exception:
            # 假設錯誤是因為 Session 已存在。
            # TODO: 應檢查具體的 Exception Type (如 SessionAlreadyExistsError)
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
            # [Debug] Log Tool Calls (Safe Access)
            try:
                # 嘗試存取 function_call，如果屬性不存在會被 except 捕獲
                # 注意：Pylance 可能會警告 Event 沒有 function_call 屬性，這是因為 ADK 的型別定義可能不完整
                # 但在執行時期，Tool Call Event 確實會有此屬性
                if hasattr(event, 'function_call') and event.function_call:
                     # 使用 getattr 避免靜態檢查錯誤
                     fc = getattr(event, 'function_call')
                     logger.info(f"🛠️  [Tool Call] {fc.name}({fc.args})")
            except Exception:
                pass

            # 處理事件流，抓取最終回應
            # 這裡簡化處理：假設最後一個含有 text 的 event 是最終回應
            if hasattr(event, 'content') and event.content and event.content.parts:
                 part = event.content.parts[0]
                 if hasattr(part, 'text') and part.text:
                    final_response = part.text
        
        return final_response