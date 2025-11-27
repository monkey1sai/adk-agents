from typing import Protocol

class AgentRunner(Protocol):
    """
    Agent 執行器的標準介面 (Protocol)。
    所有 Provider (Google, Microsoft) 都必須實作此介面。
    """
    async def run(self, user_query: str, session_id: str = "default") -> str:
        """
        執行 Agent 對話。
        
        Args:
            user_query: 使用者的輸入文字。
            session_id: 對話 Session ID，用於維護上下文記憶。
            
        Returns:
            str: Agent 的回應文字。
        """
        ...
