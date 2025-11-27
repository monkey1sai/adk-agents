# Copilot Instructions for ADK Agents Project

## 專案概述
此專案展示如何使用 **Microsoft ADK Agents** 與 **LangChain** 框架，透過 **LiteLLM Proxy** 連接本地 **Ollama** 模型 (Qwen 2.5)，實現 Tool Calling 功能。

## 系統架構

```
Python Client → LiteLLM Proxy (Port 4000) → Ollama Server (Port 11434) → Local LLM
```

- **LiteLLM Proxy**: Docker 容器內運行，負責協定轉換與請求轉發
- **Ollama**: 可在 Docker 內或 Host 機器運行，提供 OpenAI 相容 API (`/v1`)
- **Client**: 使用 `agents` 或 `langchain` SDK 發送請求

## 關鍵開發模式

### 1. 工具定義 - 必須使用扁平參數
小模型容易忽略 Pydantic 巢狀結構，請使用簡單參數：
```python
# ✅ 正確 - 扁平參數
@function_tool
def get_weather(city: str) -> str:
    """Get weather. Args: city: City name like 'Taipei'."""
    return f"{city} is Sunny, 25°C."

# ❌ 避免 - Pydantic BaseModel 巢狀結構
```

### 2. LitellmModel 設定 - 強制 OpenAI 協定
```python
from agents.extensions.models.litellm_model import LitellmModel

llm_model = LitellmModel(
    model="openai/ollama/qwen2.5",  # "openai/" 前綴強制使用 OpenAI 協定
    api_key="sk-1234",              # 必填，即使 Proxy 不驗證
    base_url="http://localhost:4000",
)
```

### 3. Agent 建立模式
```python
from agents import Agent, Runner, set_tracing_disabled

set_tracing_disabled(True)  # 避免追蹤警告

agent = Agent(
    name="AgentName",
    model=llm_model,
    tools=[your_tool],
    instructions="請用中文回答用戶的問題。"
)

# 執行 Agent
result = await Runner.run(agent, "使用者問題")
```

## 環境啟動流程

```bash
# 1. 啟動 Docker 服務 (LiteLLM + Ollama)
docker-compose up -d

# 2. 確認 Ollama 模型已下載
docker exec ollama-server ollama pull qwen2.5:7b

# 3. 執行範例
python agent_examples/3. openai_adk_litellmProxy_ollama.py
```

## 設定檔重點

### `config/litellm_config.yaml`
- `model: openai/qwen2.5:7b` - 使用 `openai/` 前綴
- `temperature: 0` - 穩定小模型輸出
- `api_base: os.environ/OLLAMA_API_BASE` - 從環境變數讀取

### `docker-compose.yaml`
- `OPENAI_API_KEY: "fake-key-for-ollama"` - 必須提供偽造 Key
- `shm_size: '32gb'` - Ollama 需要足夠的共享記憶體
- GPU 支援透過 `deploy.resources.reservations.devices` 設定

## 範例檔案說明

| 檔案 | 用途 |
|------|------|
| `agent_examples/1. lainchang_ollama.py` | LangChain + Ollama 對照組 |
| `agent_examples/2. openai_adk_ollama.py` | ADK 直連 Ollama (無 Proxy) |
| `agent_examples/3. openai_adk_litellmProxy_ollama.py` | **核心範例** - ADK + LiteLLM Proxy |
| `RgbAgent/rgb.py` | LangChain RAG Pipeline 範例 |

## 常見問題排除

1. **Tool Calling 失敗 (Max turns exceeded)**: 確認使用 `openai/` 前綴與扁平工具參數
2. **AuthenticationError**: 確認 `api_key` 欄位有值 (即使是假的)
3. **Ollama 載入卡住**: 檢查 Docker `shm_size` 設定是否足夠
4. **404/500 錯誤**: 確認 `model` 名稱與 `litellm_config.yaml` 中的 `model_name` 一致
