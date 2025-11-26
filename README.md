# ADK Agents with Local Ollama & LiteLLM Proxy

本專案展示如何使用 Microsoft ADK Agents 框架，透過 LiteLLM Proxy 連接本地運行的 Ollama 模型 (Qwen 2.5)，並成功實現 Tool Calling 功能。


## 系統架構

```mermaid
graph LR
    %% 定義樣式 (Styles)
    classDef client fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:black;
    classDef proxy fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:black;
    classDef ollama fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:black;
    
    %% 1. 客戶端區域 (Client Side)
    subgraph ClientEnv [Client Environment]
        direction TB
        App("🐍 Python App<br/>(litellm_test.py)"):::client
        Tool("🛠️ Local Tool<br/>(get_weather)"):::client
        
        App <-->|"6. Execute Tool &<br/>Loop Result"| Tool
    end

    %% 2. Docker 區域 (Proxy Side)
    subgraph DockerEnv [Docker Container (Port 4000)]
        direction TB
        ConfigFile("📄 Config<br/>(litellm_config.yaml)"):::proxy
        LiteLLM("🔄 LiteLLM Proxy<br/>(OpenAI Interface)"):::proxy
        
        ConfigFile -.->|"Load: openai/ prefix<br/>temp=0"| LiteLLM
    end

    %% 3. Host 區域 (Server Side)
    subgraph HostEnv [Host Machine (Port 11434)]
        direction TB
        OllamaServer("🦙 Ollama Server<br/>(/v1 Endpoint)"):::ollama
        LocalModel("🧠 Qwen 2.5:7b<br/>(Inference)"):::ollama
        
        OllamaServer <-->|"3. Inference"| LocalModel
    end

    %% 流程連接 (Flow)
    App -->|"1. Request<br/>model='openai/ollama/qwen2.5'<br/>tools=[schema]"| LiteLLM
    
    LiteLLM -->|"2. Forward (Force OpenAI Protocol)<br/>model='qwen2.5:7b'<br/>api_base='/v1'"| OllamaServer
    
    OllamaServer -.->|"4. Response<br/>tool_calls=[json]"| LiteLLM
    
    LiteLLM -.->|"5. Return JSON"| App
```

## 關鍵突破點 (Key Breakthroughs)

為了解決本地小模型 (Small Language Models) 在 Tool Calling 上的格式問題，我們實施了以下關鍵設定：

1.  **簡化工具定義 (Python)**：移除 Pydantic 巢狀結構，改用扁平參數，讓模型更容易生成正確 JSON。
2.  **強制 OpenAI 協定 (Proxy)**：在 LiteLLM 設定中使用 `openai/` 前綴與 `/v1` 路徑，避開 LiteLLM 原生 Ollama 轉換層的格式問題。
3.  **溫度控制 (Config)**：強制 `temperature: 0`，穩定模型輸出，避免幻覺。
4.  **偽造 API Key (Docker)**：提供 `OPENAI_API_KEY` 環境變數以通過 LiteLLM 的內部檢查。

## 執行流程與參數傳遞 (Call Flow)

當執行 `litellm_test.py` 的 `main()` 函式時，系統運作流程如下：

### 1. 初始化 (Initialization)
*   **Client**: 建立 `LitellmModel`，指定 `model="openai/ollama/qwen2.5"`。
*   **Client**: 定義 `get_weather(city: str)` 工具，生成 Schema `{"type": "function", "function": {"name": "get_weather", "parameters": {"properties": {"city": ...}}}}`。

### 2. 發送請求 (Request)
*   **Client -> Proxy**: Python SDK 發送 POST 請求至 `http://localhost:4000/chat/completions`。
    *   `model`: `"ollama/qwen2.5"` (對應 Config 中的 `model_name`)
    *   `messages`: `[{"role": "user", "content": "台北的天氣如何?"}]`
    *   `tools`: `[get_weather_schema]`

### 3. Proxy 轉發 (Forwarding)
*   **Proxy**: 接收請求，根據 `litellm_config.yaml` 查找 `ollama/qwen2.5`。
*   **Proxy -> Ollama**: 轉換並轉發請求至 `http://host.docker.internal:11434/v1/chat/completions`。
    *   `model`: `"qwen2.5:7b"` (真實模型名稱)
    *   `temperature`: `0` (強制設定)
    *   **關鍵**: 保持 OpenAI 格式的 `tools` 參數不變，直接傳給 Ollama。

### 4. 模型推論 (Inference)
*   **Ollama**: 載入 Qwen 2.5 模型。
*   **Model**: 分析語意，決定呼叫工具。
*   **Ollama -> Proxy**: 回傳 JSON。
    *   `tool_calls`: `[{"function": {"name": "get_weather", "arguments": "{\"city\": \"Taipei\"}"}}]`

### 5. 工具執行 (Tool Execution)
*   **Proxy -> Client**: 將回應回傳給 Python Client。
*   **Client**: 解析 `tool_calls`。
*   **Client**: 執行本地 Python 函式 `get_weather("Taipei")`。
*   **Client**: 獲得結果 `"Taipei is Sunny, 25°C."`。

### 6. 最終回應 (Final Response)
*   **Client -> Proxy -> Ollama**: 將工具執行結果 (Tool Output) 再次送回模型。
*   **Model**: 根據工具結果生成自然語言回應。
*   **Client**: 顯示最終結果：「目前台北的天氣是晴朗，溫度約為25°C...」。

## 對話傳導與 Context 變化 (Chat Flow & Context Evolution)

在整個 Tool Calling 過程中，`messages` 陣列（Context）會隨著對話進展而不斷累積。以下是每個階段的 Context 狀態：

### 階段 1: 用戶提問 (Initial Request)
Client 發送給 LLM 的初始訊息：
```json
[
  {
    "role": "system", 
    "content": "你是一個專業可靠的天氣助手..."
  },
  {
    "role": "user", 
    "content": "台北的天氣如何?"
  }
]
```

### 階段 2: 模型決定呼叫工具 (Tool Call Decision)
LLM 回傳 `tool_calls`，Client 將其加入 Context：
```json
[
  ... (前述訊息),
  {
    "role": "assistant",
    "tool_calls": [
      {
        "id": "call_abc123",
        "type": "function",
        "function": {
          "name": "get_weather",
          "arguments": "{\"city\": \"Taipei\"}"
        }
      }
    ]
  }
]
```

### 階段 3: 工具執行結果回傳 (Tool Output Injection)
Client 執行 Python 函式後，將結果封裝為 `tool` 角色訊息，再次發送給 LLM：
```json
[
  ... (前述訊息),
  {
    "role": "tool",
    "tool_call_id": "call_abc123", // 必須對應階段 2 的 id
    "content": "Taipei is Sunny, 25°C."
  }
]
```

### 階段 4: 最終自然語言回應 (Final Answer)
LLM 根據工具結果生成最終回答：
```json
[
  ... (前述訊息),
  {
    "role": "assistant",
    "content": "目前台北的天氣是晴朗，溫度約為 25°C。"
  }
]
```

## 設定檔摘要

### docker-compose.yaml
```yaml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    ports: ["4000:4000"]
    environment:
      OLLAMA_API_BASE: "http://host.docker.internal:11434"
      OPENAI_API_KEY: "fake-key-for-ollama" # [突破點] 必填
```

### litellm_config.yaml
```yaml
model_list:
  - model_name: ollama/qwen2.5
    litellm_params:
      model: openai/qwen2.5:7b          # [突破點] openai/ 前綴
      api_base: http://host.docker.internal:11434/v1 # [突破點] /v1 路徑
      api_key: ollama
      temperature: 0                    # [突破點] 溫度 0
```

## 如何執行 (How to Run)

### 1. 準備 Ollama 模型
確保您的本機 Ollama 服務已啟動，並下載 Qwen 2.5 模型：
```bash
ollama pull qwen2.5:7b
```

### 2. 啟動 LiteLLM Proxy
使用 Docker Compose 啟動 Proxy 服務：
```bash
docker-compose up -d
```
確認容器 `litellm-proxy` 已成功啟動且無錯誤。

### 3. 執行 Python Client
進入虛擬環境後，執行測試腳本：
```bash
python agent_examples/litellm_test.py
```