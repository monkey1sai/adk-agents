import random
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

class WeatherInput(BaseModel):
    location: str = Field(..., description="The location name to get weather for, e.g. 'Taipei'. Do not use 'city'.")

# 2. 定義工具 (Tools)
# 使用 @tool 裝飾器，並務必寫清楚 docstring，因為模型會讀取這裡的說明
@tool(args_schema=WeatherInput, return_direct=True, description="取得指定地點的天氣資訊。當使用者詢問天氣時，必須使用此工具。")
def get_weather(location: str) -> str:
    """
    取得指定地點的天氣資訊。
    當使用者詢問天氣時，必須使用此工具。
    """
    # 直接使用 location 參數
    print(f"\n[DEBUG] LangChain 正在呼叫 get_weather，地點: {location}")
    
    weather_conditions = ["晴天", "多雲", "下雨", "颱風", "陰天"]
    temperature = random.randint(15, 35)
    condition = random.choice(weather_conditions)
    
    result = f"{location}的天氣是{condition}，溫度約為{temperature}°C。"
    print(f"[DEBUG] 工具回傳: {result}\n")
    return result

tools_map = {"get_weather": get_weather}

llm = ChatOllama(
    model= "granite4:latest",  # 請確保您已執行 ollama pull granite4:latest
    validate_model_on_init=True,
    temperature=0.7
).bind_tools([get_weather])


query = "今天台北天氣如何?"


messages = [
    SystemMessage(content="你是一個有用的天氣助理。"
          "當使用者詢問天氣時，請使用 `get_weather` 工具取得資訊。"
          "取得資訊後，請直接根據工具的回傳結果回答使用者，不要重複呼叫工具。"
        "**重要**：取得資料後請直接回答，絕對不要呼叫任何其他的工具。"
        ),
    HumanMessage(content=query),
]

print("--- 第一輪：詢問 LLM ---")
ai_msg = llm.invoke(messages)


if ai_msg.tool_calls:
    print(f"工具呼叫請求: {ai_msg.tool_calls}")
    # --- 關鍵修正：將 AI 的「呼叫請求」加入歷史紀錄 ---
    # 如果沒有這行，LLM 會不知道為什麼下一條訊息是 ToolMessage
    messages.append(ai_msg)
    # -----------------------------------------------

    # 5. 遍歷並執行工具
    for tool_call in ai_msg.tool_calls:
        selected_tool = tools_map[tool_call["name"].lower()]
        
        # 執行工具 (invoke 會自動處理參數驗證)
        tool_output = selected_tool.invoke(tool_call["args"])
        
        print(f"工具執行結果: {tool_output}")
        
        # 6. 建立 ToolMessage 並加入對話歷史
        # 這是關鍵：必須告訴 LLM 這個結果對應哪一個 tool_call_id
        messages.append(ToolMessage(
            content=str(tool_output),
            tool_call_id=tool_call["id"]
        ))

    # 7. 再次呼叫 LLM (讓它根據工具結果產生最終回答)
    print("\n--- 第二輪回應 (LLM 產生最終回答) ---")
    final_response = llm.invoke(messages)
    print(f"最終回答: {final_response.content}")

else:
    print(ai_msg.content)
