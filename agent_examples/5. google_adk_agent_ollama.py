from google.adk.models.lite_llm import LiteLlm # 用于多模型支持
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types # 用于创建消息 Content/Parts
import asyncio

# @title 定义 get_weather 工具
def get_weather(city: str) -> dict:
    """获取指定城市的当前天气报告。

    Args:
        city (str): 城市名称（例如，"New York"、"London"、"Tokyo"）。

    Returns:
        dict: 包含天气信息的字典。
              包含一个 'status' 键（'success' 或 'error'）。
              如果是 'success'，包含 'report' 键与天气详情。
              如果是 'error'，包含 'error_message' 键。
    """
    print(f"--- 工具：get_weather 被调用，城市：{city} ---") # 记录工具执行
    city_normalized = city.lower().replace(" ", "") # 基本标准化

    # 模拟天气数据
    mock_weather_db = {
        "newyork": {"status": "success", "report": "纽约的天气是晴朗的，温度为 25°C。"},
        "london": {"status": "success", "report": "伦敦多云，温度为 15°C。"},
        "tokyo": {"status": "success", "report": "东京有小雨，温度为 18°C。"},
    }

    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized]
    else:
        return {"status": "error", "error_message": f"抱歉，我没有 '{city}' 的天气信息。"}


async def init_session(app_name:str,user_id:str,session_id:str) -> Session:
    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    print(f"会话已创建：App='{app_name}'，User='{user_id}'，Session='{session_id}'")
    return session


async def call_agent_async(query: str, runner, user_id, session_id):
  """向智能体发送查询并打印最终响应。"""
  print(f"\n>>> 用户查询：{query}")

  # 以 ADK 格式准备用户的消息
  content = types.Content(role='user', parts=[types.Part(text=query)])

  final_response_text = "智能体没有产生最终响应。" # 默认值

  # 关键概念：run_async 执行智能体逻辑并产生事件。
  # 我们遍历事件以找到最终答案。
  async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
      # 你可以取消注释下面的行以查看执行期间的*所有*事件
      print(f"  [事件] 作者：{event.author}，类型：{type(event).__name__}，最终：{event.is_final_response()}，内容：{event.content}")

      # 关键概念：is_final_response() 标记轮次的结束消息。
      if event.is_final_response():
          if event.content and event.content.parts:
             # 假设第一部分中的文本响应
             final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate: # 处理潜在错误/升级
             final_response_text = f"智能体升级：{event.error_message or '无特定消息。'}"
          # 如果需要，在这里添加更多检查（例如，特定错误代码）
          break # 找到最终响应后停止处理事件

  print(f"<<< 智能体响应：{final_response_text}")



if __name__ == "__main__":
    AGENT_MODEL = LiteLlm(model="openai/ollama/qwen2.5", base_url="http://localhost:4000/v1", api_key="your_api_key_here") # 替换为你的模型和端点


    weather_agent = Agent(
        name="weather_agent_v1",
        model=AGENT_MODEL, # 可以是 Gemini 的字符串或 LiteLlm 对象
        description="你是一个天气查询助手。",
        instruction="請用繁體中文回答用戶的問題。",
        tools=[get_weather]) # 直接传递函数
    
    session_service = InMemorySessionService()

    # 定义用于标识交互上下文的常量
    APP_NAME = "weather_tutorial_app"
    USER_ID = "user_1"
    SESSION_ID = "session_001" # 为简单起见使用固定 ID

    runner = Runner(
        agent=weather_agent, # 我们要运行的智能体
        app_name=APP_NAME,   # 将运行与我们的应用关联
        session_service=session_service # 使用我们的会话管理器
    )
    print(f"已为智能体 '{runner.agent.name}' 创建 Runner。")


    async def run_conversation():
        # 1. 確保 Session 存在
        await init_session(APP_NAME, USER_ID, SESSION_ID)

        user_questions = [
            "今天纽约的天气怎么样？",
            # "请告诉我伦敦的天气。",
            # "东京现在的天气如何？",
            # "巴黎的天气好吗？"
        ]

        for question in user_questions:
            print(f"\n用户提问: {question}")
            
            # [修正 2] 建構 Google ADK 規範的 Content 物件
            message_content = types.Content(role='user', parts=[types.Part(text=question)])

            # [修正 3] 使用正確的參數名稱與型別
            # Runner.run 通常是同步封裝或不存在，建議直接用 run_async 處理事件流
            # 這裡我們模擬一個簡單的 run 行為，或是使用你上面定義好的 call_agent_async
            
            # 方法 A: 使用你上面寫好的 helper (推薦，最穩健)
            await call_agent_async(question, runner, USER_ID, SESSION_ID)
            
            # 方法 B: 如果堅持要用 runner.run (假設 API 支援)，參數應為：
            # response = await runner.run(
            #     user_id=USER_ID,       # 是 user_id (str) 不是 user
            #     session_id=SESSION_ID, # 是 session_id (str) 不是 session 物件
            #     new_message=message_content # 是 new_message (Content) 不是 user_input
            # )

    asyncio.run(run_conversation())