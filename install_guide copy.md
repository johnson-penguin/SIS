- 安裝專案
```bash
git clone https://github.com/johnson-penguin/SIS.git
```

- 進入專案目錄
```bash
cd SIS
```

- 建立 venv
```bash
python -m venv venv
```


- 解除安全性限制
```bash=
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

- 啟動 venv
```bash
.\venv\Scripts\Activate.ps1
```

- 更新 pip
```bash
python -m pip install --upgrade pip
```

- 安裝套件
```bash
pip install -r requirements.txt
```

- 退出 venv
```bash
deactivate
```