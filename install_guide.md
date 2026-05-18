# SIS 專案安裝與環境建置指南

歡迎使用 **SIS** 專案！本指南將帶領您一步步完成專案原始碼下載、獨立虛擬環境建置，以及相關相依套件的安裝與啟動設定。

---

## 📋 事前準備 (Prerequisites)

在開始之前，請確保您的系統已具備以下環境與工具：
- **Git**: 用於複製遠端專案原始碼。
- **Python** (建議使用 3.8 以上版本): 用於執行專案及建立虛擬環境。
- **作業系統**: 本指南的終端機操作主要針對 **Windows PowerShell** 設計。

---

## 🚀 安裝與設定步驟 (Installation Steps)

### 1. 安裝專案
透過 `git clone` 指令將 GitHub 上的專案原始碼下載至本機端：

```bash
git clone https://github.com/johnson-penguin/SIS.git
```

### 2. 進入專案目錄
下載完成後，切換至專案根目錄中：

```bash
cd SIS
```

### 3. 建立虛擬環境 (venv)
為了避免套件版本衝突，強烈建議為本專案建立專屬的 Python 虛擬環境：

```bash
python -m venv venv
```
> **說明**：執行後，目錄下將會自動生成一個名為 `venv` 的資料夾，用來存放獨立的 Python 執行環境。

### 4. 解除安全性限制 (僅限 Windows PowerShell)
Windows PowerShell 預設可能會阻擋外部指令碼的執行。請執行以下指令，暫時允許當前視窗執行本機的虛擬環境啟動指令碼：

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 5. 啟動虛擬環境
執行啟動指令碼以進入虛擬環境：

```bash
.\venv\Scripts\Activate.ps1
```
> **提示**：成功啟動後，終端機的輸入列前方通常會出現 `(venv)` 標籤，代表目前已處於虛擬環境中。

### 6. 更新 pip
確保您的 `pip` 套件管理工具為最新版本，以獲得最佳的套件下載相容性與安裝穩定度：

```bash
python -m pip install --upgrade pip
```

### 7. 安裝套件
透過專案提供的 `requirements.txt` 一次性安裝所有必需的第三方套件：

```bash
pip install -r requirements.txt
```

---

## 🛑 結束使用 (Deactivation)

### 關閉虛擬環境
當您完成開發或測試，想要退出當前的虛擬環境時，只需執行以下指令即可恢復到系統原本的全域環境：

```bash
deactivate
```
