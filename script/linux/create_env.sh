#!/usr/bin/env bash

# 顏色定義
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}==================================================${NC}"
echo -e "${CYAN}       開始設定 Python 虛擬環境 (Linux)           ${NC}"
echo -e "${CYAN}==================================================${NC}"

# 1. 檢查系統中是否有 python3 或 python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}[錯誤] 找不到 python 或 python3 指令，請確認已安裝 Python。${NC}"
    exit 1
fi

VENV_DIR="venv"

# 2. 建立虛擬環境
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo -e "${YELLOW}[步驟 1/3] 正在建立 Python 虛擬環境 ($VENV_DIR)...${NC}"
    $PYTHON_CMD -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo -e "${RED}[錯誤] 虛擬環境建立失敗！請確認是否已安裝 python3-venv 套件。${NC}"
        echo -e "例如 Ubuntu/Debian 可執行: sudo apt install python3-venv"
        exit 1
    fi
    echo -e "${GREEN}虛擬環境建立成功。${NC}"
else
    echo -e "${GREEN}[步驟 1/3] 虛擬環境 ($VENV_DIR) 已存在，跳過建立。${NC}"
fi

# 3. 啟動虛擬環境
# 提示：Linux 環境下沒有像 Windows PowerShell 的 Execution Policy 限制，但需透過 source 啟動
echo -e "${YELLOW}[步驟 2/3] 正在載入虛擬環境...${NC}"
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}虛擬環境已成功載入。${NC}"
else
    echo -e "${RED}[錯誤] 找不到啟動腳本：$VENV_DIR/bin/activate${NC}"
    exit 1
fi

# 4. 自動執行基本更新
echo -e "${YELLOW}[步驟 3/3] 正在執行基本套件更新 (pip, setuptools, wheel)...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}基本套件更新完成。${NC}"

echo -e "${CYAN}==================================================${NC}"
echo -e "${GREEN}  設定與更新完畢！${NC}"
echo -e "${YELLOW}  重要提示：若要讓當前終端機視窗保持在虛擬環境中，${NC}"
echo -e "${YELLOW}  請使用 source 指令來執行此腳本：${NC}"
echo -e "      source ./create_env.sh"
echo -e "${CYAN}==================================================${NC}"