from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from pydantic import BaseModel, Field
import random
import os
import asyncio

# --- 設定 1: 開啟詳細除錯紀錄 ---
# 這會讓您在終端機看到送給 Ollama 的完整 JSON 以及 Ollama 的回應
os.environ['LITELLM_LOG'] = 'DEBUG'

# --- 設定 2: 使用正確的模型名稱 ---
# 建議先用 qwen2.5:7b 測試，確認流程跑通後再換大模型
# 如果您堅持要用 14b，請確保已執行 `ollama pull qwen2.5:14b`
ollama_model = LitellmModel(
    model="ollama/gemini-3-pro-preview:latest",  # 請確認此名稱與 `ollama list` 中的一致
    base_url="http://localhost:11434"
)

class WeatherInput(BaseModel):
    location: str = Field(..., description="The location name to get weather for, e.g. 'Taipei'. Do not use 'city'.")

@function_tool(description_override="取得指定地點的天氣資訊。", strict_mode=False)
def get_weather(input: WeatherInput) -> str:
    """取得指定地點的天氣資訊。"""
    print(f"\n[DEBUG] 正在執行 get_weather 工具，地點: {input.location}")
    
    weather_conditions = ["晴天", "多雲", "下雨", "颱風", "陰天"]
    temperature = random.randint(15, 35)
    condition = random.choice(weather_conditions)

    # Qwen 2.5 非常聰明，通常不需要太多額外的 Prompt，給它乾淨的資訊即可
    natural_language_result = f"{input.location}的天氣是{condition}，氣溫約為{temperature}度。"
    
    print(f"[DEBUG] 工具回傳結果: {natural_language_result}\n")
    return natural_language_result

agent = Agent(
    name="agent",
    model=ollama_model,
    tools=[get_weather],
    instructions=(
        "你是一個有用的天氣助理。"
        "當使用者詢問天氣時，請使用 `get_weather` 工具。"
        "取得資訊後，請用自然的中文回答使用者。"
    )    
)

async def main():
    print(f"正在呼叫 Agent (使用模型: {ollama_model.model})...")
    print("如果卡住太久，請檢查 Ollama 是否正在載入模型 (觀察 VRAM 使用量)...")
    
    try:
        # 加入 timeout 參數 (如果 Runner 支援) 或單純等待
        result = await Runner.run(agent, "今天台北天氣如何?")
        
        print("--- 執行結果 ---")
        print(f"Final Output: {result.final_output}")
        
    except Exception as e:
        print(f"發生錯誤: {e}")
        print("提示: 如果是 NotFoundError，請確認您已執行 `ollama pull <model_name>`")

if __name__ == "__main__":
    asyncio.run(main())