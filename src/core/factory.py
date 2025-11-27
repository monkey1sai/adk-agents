from typing import Dict, Type
from src.config import settings, AdkFramework
from src.core.interfaces import AgentRunner

class AgentFactory:
    """
    Agent Runner 工廠類別。
    使用註冊表模式 (Registry Pattern) 管理 Provider，避免硬編碼依賴。
    """
    _registry: Dict[AdkFramework, Type[AgentRunner]] = {}

    @classmethod
    def register(cls, framework: AdkFramework, provider_cls: Type[AgentRunner]):
        """註冊 Provider"""
        cls._registry[framework] = provider_cls

    @classmethod
    def create_runner(cls) -> AgentRunner:
        """根據設定檔建立對應的 Runner 實例"""
        framework = settings.adk_framework
        
        provider_cls = cls._registry.get(framework)
        
        if not provider_cls:
            # [Refactor] 移除 Fallback 邏輯，強制所有 Provider 必須註冊
            # 這符合單一職責原則 (SRP)，Factory 只負責查表與實例化，不負責處理未註冊的例外情況
            raise ValueError(f"Unsupported framework: {framework}. Please ensure the provider is registered.")
        
        # [Refactor] 引入簡單的依賴注入 (DI)
        # 將全域設定 (settings) 注入到 Provider 中，而不是讓 Provider 自己 import
        # 這提升了可測試性，允許在測試時注入 Mock Settings
        return provider_cls(settings=settings)
