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
    就像電腦開機一樣，負責把所有需要的服務都準備好，讓系統進入「隨時可戰鬥」的狀態。
    """
    # 1. 註冊 Providers
    # 告訴工廠：「我們現在有這些廠商 (Google, Microsoft) 可以提供服務喔！」
    _register_providers()
    
    # 2. 預熱 RAG 子系統 (Warm-up)
    # 因為載入 AI 模型 (Embedding Model) 和連線資料庫通常很慢 (可能要好幾秒)，
    # 我們在系統剛啟動時就先偷偷做完這些重工 (Heavy Lifting)。
    # 這樣當使用者第一次問問題時，才不會覺得系統卡卡的 (避免 Cold Start Latency)。
    RAGContainer.get_instance()

def _register_providers():
    """
    註冊所有可用的 Agent Providers。
    """
    # 註冊 Microsoft Provider
    AgentFactory.register(AdkFramework.MICROSOFT, MicrosoftProvider)
    
    # 註冊 Google Provider (如果可用)
    # 有些環境可能沒安裝 Google 套件，所以要檢查一下，避免程式直接掛掉。
    if GoogleProvider:
        AgentFactory.register(AdkFramework.GOOGLE, GoogleProvider)
