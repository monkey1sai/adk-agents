# 最優方法
1. 安裝 pipx
    ```python -m pip install --user pipx```
    ```python -m pipx ensurepath ```

2. pipx安裝uv
    ```pipx install uv```

# 執行步驟
1. uv init
    ```來看一下 uv 幫我們生成的專案架構```
2. uv run main.py

    ```Using CPython 3.9.23```
        ```Creating virtual environment at: .venv```
        ```Hello from agent-brain!```

3. 更改 .python_version 成 3.13
    ```echo 3.13 > .python-version ```

4. 推送到 github
    ```git add .```
    ```git commit -m "init commit"```
    ```git push origin master```
