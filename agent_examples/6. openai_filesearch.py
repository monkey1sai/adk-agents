from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
import asyncio
from src.tools.knowledge import search_knowledge_base

llm_model = LitellmModel(
    model="openai/ollama/qwen2.5", 
    api_key="sk-1234", 
    base_url="http://localhost:4000", 
)

# 2. 建立 Agent 並加入工具
rag_agent = Agent(
    name="DocSearcher",
    model=llm_model,
    instructions="你是一個文件助手，請根據檢索到的內容回答使用者的問題。請盡可能以繁體中文回答。",
    tools=[function_tool(search_knowledge_base)],
)


async def main():
    response = await Runner.run(rag_agent, "請幫我找出關於人工智慧的最新研究進展。")
    print("Agent 回應：", response)

if __name__ == "__main__":
    import logging  # [Add] 1. 匯入 logging
    import sys

    # [Add] 2. 設定全域 Log 層級為 INFO
    #這必須在其他程式碼執行前設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )    
    asyncio.run(main())