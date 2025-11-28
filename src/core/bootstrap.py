from src.config import AdkFramework
from src.core.factory import AgentFactory
from src.core.providers.microsoft import MicrosoftProvider
from src.rag.bootstrap import bootstrap_rag

# 使用 try-except 避免環境缺少 google 套件時直接崩潰
try:
    from src.core.providers.google import GoogleProvider
except ImportError:
    GoogleProvider = None

def bootstrap_system():
    """
    系統啟動引導 (Bootstrap)。
    就像電腦開機一樣，負責把所有需要的服務都準備好，讓系統進入「隨時可戰鬥」的狀態。
    """
    # 1. 啟動 RAG 子系統並取得工具
    # 這裡不再依賴全域 Singleton，而是明確地取得工具實例
    search_tool, ingest_tool = bootstrap_rag()
    
    # 2. 註冊 Providers
    # 將 RAG 工具傳遞給註冊函式，以便注入到 Provider 中
    _register_providers(tools=[search_tool])

def _register_providers(tools: list):
    """
    註冊所有可用的 Agent Providers。
    
    Args:
        tools: 要注入到 Provider 的共用工具列表 (例如 RAG 搜尋工具)。
    """
    # 註冊 Microsoft Provider
    # 注意：這裡我們需要修改 Factory 的 register 方法來支援 tools 注入，
    # 或者更簡單地，我們將 tools 暫存於 Factory (雖然這也是一種 Global，但至少是顯式的 Registry)
    # 為了保持簡單且不大幅改動 Factory 介面，我們這裡先使用 Partial Application 
    # 或者讓 Factory.create_runner 負責注入。
    
    # [Refactor Plan] 
    # 理想上 Factory.register 應該只註冊 Class。
    # 而 Factory.create_runner 應該接收 tools 並傳給 Provider。
    # 這裡我們先將 tools 存入 Factory 的一個類別屬性中 (暫時解法)，
    # 等下一步修改 Factory 時再完善。
    AgentFactory.set_global_tools(tools)

    AgentFactory.register(AdkFramework.MICROSOFT, MicrosoftProvider)
    
    # 註冊 Google Provider (如果可用)
    if GoogleProvider:
        AgentFactory.register(AdkFramework.GOOGLE, GoogleProvider)
