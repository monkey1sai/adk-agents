from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class AdkFramework(str, Enum):
    MICROSOFT = "microsoft"
    GOOGLE = "google"

class Settings(BaseSettings):
    # 框架選擇
    adk_framework: AdkFramework = AdkFramework.GOOGLE
    
    # LLM 設定
    model_name: str = "openai/ollama/qwen2.5" # 強制 openai/ 前綴
    api_key: str = "fake-key"
    base_url: str = "http://localhost:4000"   # 指向 LiteLLM Proxy
    
    # 應用設定
    app_name: str = "weather_app"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()