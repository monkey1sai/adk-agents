"""
[Microsoft ADK Agents + LiteLLM Proxy 範例]
此檔案是本專案的核心測試範例。
它展示如何設定 Microsoft ADK Agent 透過 LiteLLM Proxy (Port 4000) 連接後端模型。
此範例包含了解決協定問題的關鍵設定 (如 `openai/` 前綴與簡化的工具定義)，
用以驗證 Proxy 轉發、Docker 網路通訊與 Tool Calling 的正確性。
"""
import asyncio
from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from agents import set_tracing_disabled
# 移除 Pydantic 的依賴，簡化結構
# from pydantic import BaseModel, Field 

# 禁用 tracing
set_tracing_disabled(True)

# [突破點 1] 簡化工具定義：
# 我們移除了 Pydantic BaseModel (WeatherInput)，直接在函式參數中定義。
# 原因：Qwen 2.5 等小模型在處理 Tool Calling 時，容易忽略 Pydantic 生成的巢狀 "input" 結構。
# 改用扁平參數後，生成的 Schema 變為 {"city": "..."}，模型能正確生成符合格式的 JSON。
@function_tool
def get_weather(city: str) -> str:
    """
    Get weather information.

    Args:
        city: The city name in English, e.g. 'Taipei'.
    """
    print(f"\n[Proxy Tool] Fetching weather for: {city}")
    return f"{city} is Sunny, 25°C."

# 建立 LLM Model (透過 Proxy)
llm_model = LitellmModel(
    # [突破點 2] 模型名稱設定：
    # 1. "openai/" 前綴：強制 Python SDK 使用 OpenAI 協定 (/chat/completions) 發送請求。
    #    這解決了 LiteLLM Proxy 預設走 Ollama 原生協定導致的路徑錯誤 (404/500)。
    # 2. "ollama/qwen2.5" 後綴：這必須與 litellm_config.yaml 中的 `model_name` 完全一致。
    #    Proxy 收到請求後，會根據這個名字去查找後端對應的真實模型 (qwen2.5:7b)。
    model="openai/ollama/qwen2.5", 
    
    # [突破點 3] 連線設定：
    # 指向 Docker 容器中的 LiteLLM Proxy (Port 4000)。
    # api_key 雖然 Proxy 不驗證內容，但 OpenAI 協定要求必填，否則會報 AuthenticationError。
    api_key="sk-1234", 
    base_url="http://localhost:4000", 
)

agent = Agent(
    name="WeatherBot",
    model=llm_model,
    tools=[get_weather],
    instructions=(
        "請用中文回答用戶的問題。"
    )
)

async def main():
    print("Running Agent via LiteLLM Proxy (Qwen 2.5)...")
    try:
        result = await Runner.run(agent, "先介紹你自己, 然後告訴我台北的天氣如何?")
        print("\n--- Final Response ---")
        print(result.final_output)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())