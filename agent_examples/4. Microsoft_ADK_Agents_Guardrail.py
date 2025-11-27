"""
[Microsoft ADK Agents - Input Guardrail 範例]

本檔案展示如何使用 Microsoft ADK Agents 的 Guardrail (護欄) 機制來過濾使用者輸入。
在此範例中，我們建立了一個 "Math Guardrail"，用來攔截使用者要求 AI 幫忙寫數學作業的請求。

### 專案範例總覽 (Agent Examples Overview)

| 檔案名稱 | 用途說明 |
|----------|----------|
| `1. lainchang_ollama.py` | **LangChain 對照組**：展示如何用 LangChain + Ollama 實作 Tool Calling。 |
| `2. openai_adk_ollama.py` | **ADK 直連模式**：不透過 Proxy，直接連接 Ollama (Port 11434)。 |
| `3. openai_adk_litellmProxy_ollama.py` | **(本檔案) Guardrail 範例**：展示如何實作輸入過濾器 (Input Guardrail)。 |
| `4. Microsoft_ADK_Agents_Guardrail.py` | **WeatherBot 範例**：(注意：目前內容為天氣機器人) 展示透過 LiteLLM Proxy 進行 Tool Calling。 |
| `5. google_adk_agent_ollama.py` | **參數調優範例**：展示如何調整 `ModelSettings` (如 `parallel_tool_calls=False`) 以穩定小模型。 |

### 本範例關鍵技術

1.  **Guardrail Agent**: 一個專門負責「檢查」的 Agent，它的輸出是一個結構化的 Pydantic 物件 (`MathHomeworkOutput`)。
2.  **@input_guardrail**: 裝飾器，用來定義攔截邏輯。如果 `tripwire_triggered` 為 True，則主 Agent 不會執行，直接拋出例外。
3.  **LiteLLM Proxy**: 使用 Port 4000 連接本地模型，確保輸出格式穩定。

"""
from agents.extensions.models.litellm_model import LitellmModel
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
    set_tracing_disabled
)

set_tracing_disabled(True)
# 1. 定義 Guardrail 的輸出結構
# 這是 Guardrail Agent 判斷後的結果，必須包含是否觸發 (bool) 與理由 (str)
class MathHomeworkOutput(BaseModel):
    is_math_homework: bool
    reasoning: str

# 2. 設定 LLM 模型 (透過 LiteLLM Proxy)
llm_model=LitellmModel(
    model="openai/ollama/qwen2.5",
    api_key="ollama-key",
    base_url="http://localhost:4000",
)

# 3. 建立 Guardrail 專用 Agent
# 它的任務只有一個：判斷輸入是否為數學作業
guardrail_agent = Agent( 
    name="護欄檢查",
    model=llm_model,
    instructions="檢查使用者是否要求你幫忙寫數學作業。",
    
    # Prompt 注入 / 參數設定：
    # SDK 會告訴 LLM：「請你輸出的內容必須符合這個 JSON Schema」。
    # 這通常是透過 OpenAI API 的 response_format 參數 
    # (如果模型支援 Structured Outputs)，或是透過 System Prompt 強制要求輸出 JSON 格式。
    output_type=MathHomeworkOutput, # 強制輸出結構化資料
)

# 4. 定義 Guardrail 函式
# 這個函式會在主 Agent 執行前被呼叫
@input_guardrail
async def math_guardrail( 
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    # 執行 Guardrail Agent 進行檢查
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    # 回傳檢查結果
    # tripwire_triggered=True 表示攔截成功，主流程將中斷
    return GuardrailFunctionOutput(
        output_info=result.final_output, 
        tripwire_triggered=result.final_output.is_math_homework,
    )

# 5. 建立主 Agent (Customer Support)
# 將 math_guardrail 加入 input_guardrails 列表
agent = Agent(  
    name="客戶支援代理",
    model=llm_model,    
    instructions="你是一位客戶支援代理。你負責協助客戶解決他們的問題。",
    input_guardrails=[math_guardrail],
)

async def main():
    print("--- 開始護欄測試 ---")
    print("使用者輸入: '你好，可以幫我解這個 x 嗎: 2x + 3 = 11?'")
    
    # This should trip the guardrail
    try:
        await Runner.run(agent, "你好，可以幫我解這個 x 嗎: 2x + 3 = 11?")
        print("護欄未觸發 - 這是非預期的結果")

    except InputGuardrailTripwireTriggered:
        print("\n[成功] 數學作業護欄已觸發！")
        print("代理拒絕回答數學問題。")
        
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())