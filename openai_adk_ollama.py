import asyncio
from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from agents import set_tracing_disabled

# 禁用 tracing
set_tracing_disabled(True)

# --- 全域變數：斷路器紀錄 ---
# 用來記住我們已經查過哪些城市，防止模型鬼打牆
query_history = {}

@function_tool
def get_weather(city: str) -> str:
    """取得城市天氣的工具。"""
    global query_history
    city_key = city.strip().lower()
    
    print(f"\n[DEBUG] 模型呼叫工具: {city}")

    # --- 關鍵修正：斷路器邏輯 ---
    # 如果模型重複問同一個地方，我們不回傳天氣，而是回傳「系統指令」強迫它閉嘴並回答
    if city_key in query_history:
        cached_result = query_history[city_key]
        print("[DEBUG] 偵測到重複呼叫！強制中斷迴圈。")
        return (
            f"SYSTEM_OVERRIDE: STOP CALLING TOOLS. "
            f"You already have the information: '{cached_result}'. "
            f"Please answer the user immediately using this information."
        )

    # 正常的工具回傳
    result = f"{city} 的天氣是晴天，溫度 25°C。"
    query_history[city_key] = result
    
    print(f"[DEBUG] 工具回傳: {result}\n")
    return result

# 建立 LLM Model
# 設定 temperature=0 是關鍵，能減少模型亂跑的機率
llm_model = LitellmModel(
    model="openai/ollama/llama3", 
    api_key="sk-1234", 
    base_url="http://localhost:4000/v1",
)

# 建立 Agent
agent = Agent(
    name="WeatherAssistant",
    # 優化指令：明確告訴模型「拿到資料就停止」
    instructions=(
        "你是一個天氣助手。"
        "步驟："
        "1. 呼叫 get_weather 工具。"
        "2. **取得資訊後，立即停止呼叫工具**。"
        "3. 用中文回答使用者。"
    ),
    model=llm_model,
    tools=[get_weather],
)

async def main():
    runner = Runner()
    print("正在執行 Agent (請稍候)...")
    try:
        # 使用 await 執行非同步方法，比 run_sync 更穩定
        result = await runner.run(agent, "台北的天氣如何？")
        print("--- 最終結果 ---")
        print("Agent 回覆：", result.final_output)
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())