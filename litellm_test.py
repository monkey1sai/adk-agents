from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from agents import set_tracing_disabled  # 禁用 tracing 以避免需 OpenAI Key
import asyncio

# 禁用 tracing（避免上傳到 OpenAI）
set_tracing_disabled(False)

# 定義一個簡單工具（Agent 可呼叫的函數）
@function_tool
def get_weather(city: str) -> str:
    """取得城市天氣的工具。"""
    # 模擬天氣查詢（實際可整合 API）
    return f"{city} 的天氣是晴天，溫度 25°C。"

# 建立 LLM Model：使用 LiteLLM Proxy 的端點
# model="llama3" 對應 config.yaml 中的 model_name；api_base 指向本地 Proxy
llm_model = LitellmModel(
    model="openai/ollama/qwen2.5",  # 或直接 "ollama/llama3" 如果未用 config
    api_key="sk-1234", # Proxy 需要任意非空字串
    base_url="http://localhost:4000/v1",  # LiteLLM Proxy 端點
    # 無需 api_key，因為是本地 Ollama
)

# 建立 Agent：配備指令、工具和 LLM Model
agent = Agent(
    name="WeatherAssistant",
    instructions="你是一個天氣助手。使用 get_weather 工具來回答用戶的天氣查詢，只回覆相關資訊。",
    model=llm_model,  # 使用自訂 LLM Model
    tools=[get_weather],  # 附加工具
)

async def main():
    print("Running Agent with Qwen 2.5...")
    try:
        # 執行 Agent
        result = await Runner.run(agent, "What is the weather in Taipei?")
        
        print("\n--- Final Response ---")
        print(result.final_output)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
    
    
