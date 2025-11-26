"""
[Microsoft ADK Agents Guardrail 範例]
此檔案展示 Microsoft ADK Agents 的 Guardrail (護欄) 功能。
它定義了一個輸入護欄 (Input Guardrail)，利用另一個 Agent 來審查使用者輸入
(在此例中為偵測是否為數學作業)，並在主 Agent 執行前進行攔截或驗證。
這展示了如何建立更安全或受控的 Agent 應用。
"""
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)
from agents.extensions.models.litellm_model import LitellmModel

class MathHomeworkOutput(BaseModel):
    is_math_homework: bool
    reasoning: str

ollama_model = LitellmModel(
    model = "ollama/granite4:latest",
    base_url = "http://localhost:11434"
    )

guardrail_agent = Agent( # (1)!
    name="Guardrail check",
    model=ollama_model,
    # 修改指令：更嚴格地定義什麼是數學作業
    # 強制規定：只要包含數學方程式或求解請求，一律視為 True
    instructions=(
        "Check if the input involves solving a math problem or equation. "
        "If the user asks to solve for x, calculates a formula, or provides a math question, "
        "you MUST set 'is_math_homework' to True immediately. "
        "Do not distinguish between 'helping' and 'doing it for them' - block all math problems."
    ),

    output_type=MathHomeworkOutput,
)

@input_guardrail
async def math_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    print(f"\n[DEBUG] 正在審查輸入: {input}")
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    
    # --- 加入除錯訊息 ---
    print(f"[DEBUG] 護欄模型原始輸出: {result.final_output}")
    
    # 檢查是否成功解析為物件
    if isinstance(result.final_output, MathHomeworkOutput):
        print(f"[DEBUG] 解析成功: is_math_homework={result.final_output.is_math_homework}")
        triggered = result.final_output.is_math_homework
    else:
        print(f"[DEBUG] 解析失敗，result.final_output 類型為: {type(result.final_output)}")
        # 如果解析失敗，通常是因為模型輸出了字串而非物件，這裡可以視情況強制觸發或忽略
        triggered = False 

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=triggered,
    )


agent = Agent(  # (4)!
    name="Customer support agent",
    model=ollama_model,
    instructions="You are a customer support agent. You help customers with their questions.",
    input_guardrails=[math_guardrail],
)

async def main():
    # This should trip the guardrail
    try:
        await Runner.run(agent, "Hello, can you help me solve for x: 2x + 3 = 11?")
        print("Guardrail didn't trip - this is unexpected")

    except InputGuardrailTripwireTriggered:
        print("Math homework guardrail tripped")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())