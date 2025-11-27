from src.config import AdkFramework
from src.core.factory import AgentFactory
from src.core.providers.microsoft import MicrosoftProvider
from src.tools.knowledge import RAGContainer

# 使用 try-except 避免環境缺少 google 套件時直接崩潰
try:
    from src.core.providers.google import GoogleProvider
except ImportError:
    GoogleProvider = None

def bootstrap_system():
    """
    系統啟動引導 (Bootstrap)。
    負責註冊 Providers 與預熱核心服務。
    """
    # 1. 註冊 Providers
    _register_providers()
    
    # 2. 預熱 RAG 子系統 (Warm-up)
    # 這會觸發 DB 連線與 Embedding 模型載入
    RAGContainer.get_instance()

def _register_providers():
    """
    註冊所有可用的 Agent Providers。
    """
    # 註冊 Microsoft Provider
    AgentFactory.register(AdkFramework.MICROSOFT, MicrosoftProvider)
    
    # 註冊 Google Provider (如果可用)
    if GoogleProvider:
        AgentFactory.register(AdkFramework.GOOGLE, GoogleProvider)
