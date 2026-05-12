# 建立 Python 虛擬環境
python -m venv venv

# 預設的安全性限制（稱為 Execution Policy），它不允許執行未經簽署的指令碼（例如虛擬環境的啟用腳本），需要手動解除
# -Scope Process 代表這個權限只對目前的視窗有效，關閉後就會恢復，這在安全性上最為平衡。
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 啟動虛擬環境
.\venv\Scripts\Activate.ps1

# 更新
python -m pip install --upgrade pip