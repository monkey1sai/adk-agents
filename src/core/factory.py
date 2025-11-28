from typing import Dict, Type
from src.config import settings, AdkFramework
from src.core.interfaces import AgentRunner

class AgentFactory:
    """
    Agent Runner 工廠類別。
    負責生產 Agent Runner。就像一個自動販賣機，根據設定檔決定要給你 Google 還是 Microsoft 的服務。
    """
    _registry: Dict[AdkFramework, Type[AgentRunner]] = {}

    @classmethod
    def register(cls, framework: AdkFramework, provider_cls: Type[AgentRunner]):
        """
        註冊 Provider (供應商)。
        
        這裡的 Type[AgentRunner] 就像是「警察」或「模具」：
        它會檢查傳進來的 provider_cls 是否乖乖遵守了 AgentRunner 的規定 (Protocol)。
        如果不符合規定 (例如少寫了 run 方法)，程式碼檢查工具 (Pylance) 就會亮紅燈警告。
        """
        cls._registry[framework] = provider_cls

    @classmethod
    def create_runner(cls) -> AgentRunner:
        """根據設定檔建立對應的 Runner 實例"""
        framework = settings.adk_framework
        
        provider_cls = cls._registry.get(framework)
        
        if not provider_cls:
            # 如果找不到對應的服務商，直接報錯。
            # 就像去餐廳點了菜單上沒有的菜，廚房做不出來。
            raise ValueError(f"不支援的框架: {framework}. 請確認該 Provider 是否已註冊。")
        
        # [依賴注入] 把設定檔 (settings) 當作參數傳進去。
        # 這樣做的好處是：Provider 不需要自己去讀全域變數，
        # 就像我們把「工具箱」直接交給工人，而不是讓工人自己回家拿。
        # 這讓測試變得很容易 (我們可以給他一個假的工具箱來測試)。
        return provider_cls(settings=settings)
