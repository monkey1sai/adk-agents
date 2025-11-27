from src.config import AdkFramework
from src.core.factory import AgentFactory
from src.core.providers.microsoft import MicrosoftProvider

# 使用 try-except 避免環境缺少 google 套件時直接崩潰
try:
    from src.core.providers.google import GoogleProvider
except ImportError:
    GoogleProvider = None

def register_providers():
    """
    註冊所有可用的 Agent Providers。
    此函式應在應用程式啟動時呼叫。
    """
    # 註冊 Microsoft Provider
    AgentFactory.register(AdkFramework.MICROSOFT, MicrosoftProvider)
    
    # 註冊 Google Provider (如果可用)
    if GoogleProvider:
        AgentFactory.register(AdkFramework.GOOGLE, GoogleProvider)
