import asyncio
import logging
import json
import re
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
        logger.info(f"正在注入 {len(tools)} 個工具到 MicrosoftProvider...")
        self.tools = [get_weather] + tools
        # 重建 Agent 以套用新工具
        self.agent = self._create_agent()

    def _create_llm(self) -> LitellmModel:
        """建立符合 LiteLLM Proxy 規範的模型實例"""
        return LitellmModel(
            model=self.settings.llm.full_model_name,
            api_key=self.settings.llm.api_key.get_secret_value(),
            base_url=self.settings.llm.base_url
        )

    def _load_instructions(self) -> str:
        """從外部檔案載入 System Prompt"""
        try:
            # 取得目前檔案 (microsoft.py) 的目錄
            current_dir = Path(__file__).parent
            # 往上兩層找到 src，再進入 prompts
            prompt_path = current_dir.parent.parent / "prompts" / "microsoft_agent.md"
            
            if not prompt_path.exists():
                logger.warning(f"在 {prompt_path} 找不到提示詞檔案，使用預設指令。")
                return "你是一個使用 Microsoft ADK 的氣象助理。請用繁體中文回答。"
                
            return prompt_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"載入指令時發生錯誤: {e}")
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
        logger.info(f"[Microsoft ADK] 正在執行 Agent，查詢: {user_query} (工作階段: {session_id})")
        
        result = await Runner.run(self.agent, user_query)
        final_output = str(result.final_output)

        # [SRE Fix] Robustness Pattern: Manual Tool Execution Recovery
        # 針對小模型 (7B) 容易將 Tool Call 輸出為純文字 JSON 的問題，進行手動救援。
        if '{"name":' in final_output and "arguments" in final_output:
            logger.warning("⚠️ 偵測到輸出中有原始 JSON 工具呼叫。正在嘗試手動復原...")
            return await self._manual_tool_execution_recovery(final_output, user_query)
        
        return final_output

    async def _manual_tool_execution_recovery(self, raw_output: str, original_query: str) -> str:
        """
        當模型輸出 Raw JSON 而非正確的 Tool Call Signal 時，手動解析並執行。
        """
        try:
            # 1. 嘗試提取 JSON
            # 尋找最外層的 {}
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if not json_match:
                return raw_output
            
            tool_call_data = json.loads(json_match.group(0))
            tool_name = tool_call_data.get("name")
            tool_args = tool_call_data.get("arguments", {})
            
            logger.info(f"🔄 手動執行: {tool_name}({tool_args})")
            
            # 2. 尋找對應的工具
            target_tool = None
            # self.agent.tools 裡面的工具可能被 function_tool 包裝過
            # 我們需要遍歷並檢查名稱
            for tool in self.agent.tools:
                # Microsoft ADK 的 Tool 物件通常有 name 屬性
                if hasattr(tool, "name") and tool.name == tool_name:
                    target_tool = tool
                    break
                # 或者如果是原始函式
                elif hasattr(tool, "__name__") and getattr(tool, "__name__") == tool_name:
                    target_tool = tool
                    break
            
            if not target_tool:
                logger.error(f"在 Agent 工具中找不到工具 {tool_name}。")
                return raw_output

            # 3. 執行工具
            # 注意：Microsoft ADK 的 Tool 執行方式可能不同
            # 如果是 function_tool 包裝的，通常有 run 或類似方法，或者它是 Callable
            tool_result = ""
            if callable(target_tool):
                if asyncio.iscoroutinefunction(target_tool):
                    tool_result = await target_tool(**tool_args)
                else:
                    tool_result = target_tool(**tool_args)
            elif hasattr(target_tool, "run"):
                 # 假設有 run 方法
                 run_method = getattr(target_tool, "run")
                 if asyncio.iscoroutinefunction(run_method):
                     tool_result = await run_method(**tool_args)
                 else:
                     tool_result = run_method(**tool_args)
            
            logger.info(f"✅ 工具執行結果: {str(tool_result)[:100]}...")
            
            # 4. 將結果回傳給 Agent 進行總結 (Recursive Call)
            # 我們構造一個新的 Prompt，包含工具執行結果
            recovery_prompt = (
                f"使用者問題: {original_query}\n"
                f"系統: 我已為您手動執行了工具 '{tool_name}'。\n"
                f"工具輸出: {tool_result}\n"
                f"指令: 請僅使用上方的工具輸出來回答使用者的問題。如果工具輸出中沒有答案，請說明您沒有相關資訊。切勿編造資訊或列出不相關的主題。"
            )
            
            recovery_result = await Runner.run(self.agent, recovery_prompt)
            return str(recovery_result.final_output)

        except Exception as e:
            logger.error(f"手動復原失敗: {e}")
            return raw_output
