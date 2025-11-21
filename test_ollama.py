from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.voice import (
    AudioInput,
    SingleAgentVoiceWorkflow,
    SingleAgentWorkflowCallbacks,
    VoicePipeline,
)

import random

ollama_model = LitellmModel(
    model = "ollama/granite3.2:2b",
    base_url = "http://localhost:11434")

@function_tool
def get_weather(location: str) -> str:
    """
    取得指定地點的天氣資訊。
    
    Args:
        location: 地點名稱，例如 "台北" 或 "Tokyo"
    """
    # --- 除錯關鍵：印出訊息確認工具真的有被執行 ---
    print(f"\n[DEBUG] 正在執行 get_weather 工具，地點: {location}")
    
    weather_conditions = ["晴天", "多雲", "下雨", "颱風", "陰天"]
    temperature = random.randint(15, 35)
    condition = random.choice(weather_conditions)
    result = f"{location}的天氣是{condition}，溫度約為{temperature}°C。"
    
    print(f"[DEBUG] 工具回傳結果: {result}\n")
    return result


agent = Agent(
    name="agent",
    model=ollama_model,
    tools=[get_weather],
    instructions=(
        "你是一個有用的天氣助理。"
        "當使用者詢問天氣時，請使用 `get_weather` 工具取得資訊。"
        "取得資訊後，請直接根據工具的回傳結果回答使用者，不要重複呼叫工具。"
    )    
)

async def main():
    print("正在呼叫 Agent...")
    try:
        # 加入 verbose=True (如果 Runner 支援) 或單純印出結果物件
        result = await Runner.run(agent, "今天台北天氣如何?")
        
        print("--- 執行結果 ---")
        print(f"Final Output: '{result.final_output}'")
        
        # 檢查是否有中間步驟的訊息 (Chat History)
        if hasattr(result, 'chat_history'):
            print("\n--- 對話紀錄 ---")
            for msg in result.chat_history:
                print(f"[{msg.role}]: {msg.content}")
        
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

    # print("Starting voice agent...")
    # voice_workflow = SingleAgentVoiceWorkflow(
    #     agent=chiness_agent,
    #     voice_pipeline=VoicePipeline(),
    #     callbacks=SingleAgentWorkflowCallbacks(),
    # )

    # voice_workflow.run(AudioInput())