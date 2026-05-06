
import sqlite3
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="IoT Data Demo API",
    description="提供提取 telemetry 與 events 數據的 Demo 接口"
)

def get_db_connection():
    # 連結到你的資料庫檔案
    conn = sqlite3.connect("iot_data.db")
    conn.row_factory = sqlite3.Row  # 讓結果可以像 dict 一樣被讀取
    return conn

@app.get("/")
def read_root():
    return {"message": "Welcome to IoT Data Demo API", "status": "online"}

@app.get("/telemetry")
def get_telemetry_data(limit: int = 10):
    """
    提取裝置的感測器數據 (Telemetry)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 簡單 print 訊息以符合 Demo 需求
        print(f"[Log] 客戶端正在提取前 {limit} 筆 Telemetry 數據...")
        
        # 查詢 telemetry 資料表
        cursor.execute("SELECT * FROM telemetry ORDER BY server_received_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        data = [dict(row) for row in rows]
        conn.close()
        
        return {
            "count": len(data),
            "results": data
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

@app.get("/events")
def get_events_data(limit: int = 10):
    """
    提取裝置的事件紀錄 (Events)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"[Log] 客戶端正在提取前 {limit} 筆 Events 數據...")
        
        # 查詢 events 資料表
        cursor.execute("SELECT * FROM events ORDER BY start_time DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        data = [dict(row) for row in rows]
        conn.close()
        
        return {
            "count": len(data),
            "results": data
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

if __name__ == "__main__":
    import uvicorn
    # 啟動 API Server
    uvicorn.run(app, host="0.0.0.0", port=8003)