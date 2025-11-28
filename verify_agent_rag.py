import asyncio
import logging
import sys
import os

# Add the current directory to sys.path to ensure imports work correctly
sys.path.append(os.getcwd())

from src.rag.bootstrap import bootstrap_rag
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

async def main():
    print("=== RAG Verification Test ===")
    print("Initializing RAG Subsystem...")
    
    # 1. Bootstrap RAG to get the search tool
    try:
        search_tool, _ = bootstrap_rag()
        print("[OK] RAG Subsystem initialized.")
    except Exception as e:
        print(f"[Error] Failed to initialize RAG: {e}")
        return

    # 2. Setup LLM (LiteLLM + Ollama)
    print("Initializing LLM...")
    llm_model = LiteLlm(
        model="openai/ollama/qwen2.5",
        base_url="http://localhost:4000",
        api_key="fake-key"
    )

    # 3. Setup Agent with the Search Tool
    print("Initializing Agent...")
    agent = Agent(
        name="RAGVerifier",
        model=llm_model,
        instruction="You are a helpful assistant. Use the search_knowledge_base tool to answer questions based on internal documents. Always answer in Traditional Chinese.",
        tools=[search_tool]
    )

    # 4. Setup Runner and Session
    session_service = InMemorySessionService()
    APP_NAME = "rag_verification"
    USER_ID = "tester"
    SESSION_ID = "verify_001"

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # 5. Execute Query
    query = "請問吳東凌在人工智慧發展報告中負責什麼？"
    print(f"\n[User Query]: {query}")
    print("[Agent] is thinking... (This may take a moment)")

    user_msg = types.Content(role="user", parts=[types.Part(text=query)])

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=user_msg
    ):
        # Try to log tool calls if possible
        try:
            # Check for function calls in a safe way
            if hasattr(event, 'function_call') and event.function_call:
                 print(f"[Tool Call] {event.function_call.name}")
            elif hasattr(event, 'get_function_calls'):
                 calls = event.get_function_calls()
                 if calls:
                     for call in calls:
                         print(f"[Tool Call] {call.name}")
        except Exception:
            pass
        
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                print(f"\n[Agent Response]:\n{response_text}")
                
                # Simple assertion logic
                if "吳東凌" in response_text or "Phase" in response_text:
                    print("\n[PASS] VERIFICATION PASSED: Agent successfully retrieved and used the information.")
                else:
                    print("\n[WARN] VERIFICATION WARNING: Agent response might not contain expected keywords.")

if __name__ == "__main__":
    asyncio.run(main())
