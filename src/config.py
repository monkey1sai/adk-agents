from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 定義常數，但不公開到全域
_LITELLM_OPENAI_PREFIX = "openai/"

class AdkFramework(str, Enum):
    MICROSOFT = "microsoft"
    GOOGLE = "google"

class LLMConfig(BaseSettings):
    """LLM 連線相關設定"""
    model_name: str = Field(default="ollama/qwen2.5", description="模型名稱 (e.g. ollama/qwen2.5)", validation_alias="MODEL_NAME")
    api_key: SecretStr = Field(default=SecretStr("fake-key"), description="API Key (敏感資料)", validation_alias="API_KEY")
    base_url: str = Field(default="http://localhost:4000", description="LiteLLM Proxy URL", validation_alias="BASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @computed_field
    @property
    def full_model_name(self) -> str:
        """
        自動封裝 LiteLLM 所需的 openai/ 前綴邏輯。
        這是一個 Computed Field，不會被序列化到 JSON 中，但在程式碼中可直接存取。
        """
        if not self.model_name.startswith(_LITELLM_OPENAI_PREFIX):
            return f"{_LITELLM_OPENAI_PREFIX}{self.model_name}"
        return self.model_name

class RAGConfig(BaseSettings):
    """RAG 知識庫相關設定"""
    db_path: str = Field(default="vector_db", validation_alias="RAG_DB_PATH")
    embed_model: str = Field(default="nomic-embed-text:latest", validation_alias="RAG_EMBED_MODEL")
    docs_folder: str = Field(default="src/docs", validation_alias="RAG_DOCS_FOLDER")

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

class Settings(BaseSettings):
    """
    全域應用程式設定
    採用 Composition (組合) 模式，將設定分組。
    """
    # 框架選擇
    adk_framework: AdkFramework = AdkFramework.GOOGLE
    
    # 應用設定
    app_name: str = "weather_app"

    # 子設定群組
    llm: LLMConfig = Field(default_factory=LLMConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore",
        # 允許從環境變數讀取巢狀設定，例如 LLM__MODEL_NAME
        env_nested_delimiter="__"
    )

# 初始化全域設定
settings = Settings()