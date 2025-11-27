from src.config import settings, AdkFramework
from src.core.providers.microsoft import MicrosoftProvider
# 使用 try-except 避免環境缺少 google 套件時直接崩潰
try:
    from src.core.providers.google import GoogleProvider
except ImportError:
    GoogleProvider = None

class AgentFactory:
    @staticmethod
    def create_runner():
        framework = settings.adk_framework
        
        if framework == AdkFramework.MICROSOFT:
            return MicrosoftProvider()
        
        elif framework == AdkFramework.GOOGLE:
            if GoogleProvider is None:
                raise ImportError("Google ADK package not found. Please install it or switch to 'microsoft' framework.")
            return GoogleProvider()
            
        else:
            raise ValueError(f"Unsupported framework: {framework}")
