from src.config import settings

print(f"Loaded Framework: {settings.adk_framework}")
print(f"Loaded Model: {settings.llm.model_name}")
print(f"Loaded Base URL: {settings.llm.base_url}")
