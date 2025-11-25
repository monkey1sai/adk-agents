import asyncio
from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from agents.tracing import set_tracing_disabled

# 禁用 tracing 以避免在沒有設定追蹤後端時出現警告
set_tracing_disabled(True)

@function_tool
def get_weather(city: str) -> str:
    """
    取得指定城市天氣資訊的工具函式。
    
    Args:
        city (str): 城市名稱。
        
    Returns:
        str: 天氣狀況描述。
    """
    print(f"\n[DEBUG] 模型呼叫工具: {city}")
    
    # 模擬正常的工具回傳結果
    result = f"{city} 的天氣是晴天，溫度 25°C。"
    
    print(f"[DEBUG] 工具回傳: {result}\n")
    return result

# 設定 LLM 模型
# 使用 LiteLLM 連接本地運行的 Ollama 服務
# model: 指定模型名稱，這裡使用 openai/ 前綴是為了讓 LiteLLM 使用 OpenAI 兼容模式
# base_url: 指向本地 Ollama 的 API 端點 (OpenAI 兼容介面)
llm_model = LitellmModel(
    model="openai/llama3.1:8b", 
    api_key="ollama_api_key_here",  # Ollama 不需要真實 Key，但欄位不可為空
    base_url="http://localhost:11434/v1",
)

# 建立 Agent
# 定義 Agent 的名稱、指令 (System Prompt)、使用的模型以及可用的工具
agent = Agent(
    name="WeatherAssistant",
    instructions=(
        "You are a helpful weather assistant."
    ),
    model=llm_model,
    tools=[get_weather],
)

async def main():
    """
    主程式進入點。
    建立 Runner 並執行 Agent 進行對話。
    """
    runner = Runner()
    print("正在執行 Agent (Llama 3)...")
    
    try:
        # 執行 Agent，傳入使用者的查詢
        # run 方法會自動處理思考、工具呼叫與回應的迴圈
        result = await runner.run(agent, "台北的天氣如何？")
        
        print("--- 最終結果 ---")
        print("Agent 回覆：", result.final_output)
        
    except Exception as e:
        print(f"發生錯誤: {e}")


if __name__ == "__main__":
    # 使用 asyncio 執行非同步主程式
    asyncio.run(main())