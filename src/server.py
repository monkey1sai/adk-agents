from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import Any, Dict

from src.core.factory import AgentFactory
from src.core.bootstrap import bootstrap_system
from src.config import settings

# 設定 Log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- DTOs (Data Transfer Objects) ---
class AgentRequest(BaseModel):
    query: str = Field(..., description="使用者的查詢內容", json_schema_extra={"example": "人工智慧最新研究進展"})
    session_id: str = Field(default="default_session", description="工作階段 ID", json_schema_extra={"example": "session_001"})

class AgentResponse(BaseModel):
    response: str = Field(..., description="Agent 的回應")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外的執行資訊")

# --- Lifecycle Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式生命週期管理
    Startup: 初始化系統 (RAG, Vector DB 連線等)
    Shutdown: 清理資源 (如果有)
    """
    logger.info(f"=== Agent 服務啟動中 ({settings.adk_framework.value.upper()} 模式) ===")
    try:
        # [Fix] 使用 run_in_executor 避免阻塞主執行緒 (Event Loop)
        # [Bootstrap] 系統啟動引導 (註冊 + 預熱)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, bootstrap_system)
        # bootstrap_system()
        logger.info("系統初始化完成")
    except Exception as e:
        logger.error(f"系統初始化失敗: {e}")
        raise e
    
    yield
    
    logger.info("=== Agent 服務關閉中 ===")
    # 這裡可以加入關閉 DB 連線等邏輯

# --- FastAPI App ---
app = FastAPI(
    title="ADK Agent Service",
    description="基於 Microsoft ADK 與 LangChain 的 Agent 服務",
    version="1.0.0",
    lifespan=lifespan
)

# --- Dependency Injection ---
async def get_agent_runner():
    """
    取得 Agent Runner 實例。
    這裡可以實作快取或 Pool 機制，目前簡單透過 Factory 建立。
    """
    try:
        return AgentFactory.create_runner()
    except Exception as e:
        logger.error(f"無法建立 Agent Runner: {e}")
        raise HTTPException(status_code=500, detail="Agent 系統內部錯誤")

# --- Endpoints ---
@app.post("/agent/chat", response_model=AgentResponse, summary="與 Agent 對話")
async def chat_endpoint(
    request: AgentRequest,
    runner = Depends(get_agent_runner)
):
    """
    接收使用者查詢，執行 Agent 流程並回傳結果。
    """
    logger.info(f"收到請求: {request.query} (Session: {request.session_id})")
    
    try:
        # 執行 Agent
        response_text = await runner.run(request.query, session_id=request.session_id)
        
        return AgentResponse(
            response=response_text,
            metadata={
                "framework": settings.adk_framework.value,
                "session_id": request.session_id
            }
        )
        
    except Exception as e:
        logger.exception("Agent 執行期間發生錯誤")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", summary="健康檢查")
async def health_check():
    return {"status": "ok", "framework": settings.adk_framework.value}

if __name__ == "__main__":
    import uvicorn
    # 開發模式啟動
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)
