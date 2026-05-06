import socket
import struct
import sqlite3
import base64
import time
from datetime import datetime

# --- 設備註冊表 ---
DEVICE_REGISTRY = {
    101: {"name": "A_Sensor_1", "decrypt": "XOR"},
    102: {"name": "A_Sensor_2", "decrypt": "XOR"},
    201: {"name": "B_Sensor_1", "decrypt": "B64"},
    202: {"name": "B_Sensor_2", "decrypt": "B64"},
    203: {"name": "B_Sensor_3", "decrypt": "B64"}
}

# 狀態追蹤器：紀錄各設備進入異常狀態的時間點，用於判定持續時間
UE_STATES = {}

def init_db():
    """初始化資料庫並建立包含新欄位的表"""
    conn = sqlite3.connect('iot_data.db')
    cur = conn.cursor()
    # 確保包含 hrv 與 risk_level 欄位
    cur.execute('''CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        device_name TEXT,
        temp REAL,
        heart REAL,
        hrv REAL,
        spo2 REAL,
        speed REAL,
        heading REAL,
        distance REAL,
        battery REAL,
        risk_level TEXT,
        event_code TEXT,
        server_received_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    return conn

def analyze_risk_logic(uid, hr, hrv, spo2, speed):
    """
    實作傳遞資訊(劇本一)的語義聯動邏輯
    """
    now = time.time()
    if uid not in UE_STATES:
        UE_STATES[uid] = {
            "l1_start": None, 
            "l2_start": None, 
            "static_start": now if speed < 0.5 else None
        }
    
    state = UE_STATES[uid]
    
    # 更新靜止狀態計時
    if speed < 0.5:
        if state["static_start"] is None: state["static_start"] = now
    else:
        state["static_start"] = None
    
    static_dur = (now - state["static_start"]) if state["static_start"] else 0

    # Level 4 (緊急): 心率極端異常 + 血氧下降 (直接啟動)
    if (hr > 140 or hr < 40) and spo2 < 90:
        return "Level 4", "E_URGENT"

    # Level 2 & 3 核心條件: 心率上升 + HRV 下降
    is_abnormal_cond = (hr > 100 and hrv < 30)
    
    if is_abnormal_cond:
        if state["l2_start"] is None: state["l2_start"] = now
        l2_dur = now - state["l2_start"]
        
        # Level 3 (高風險): Level 2 持續 + (血氧波動 或 長時間靜止 > 10分鐘)
        if l2_dur > 60 and (spo2 < 94 or static_dur > 600):
            return "Level 3", "E_HIGH_RISK"
        
        # Level 2 (異常): 條件持續超過 1 分鐘
        if l2_dur > 60:
            return "Level 2", "E_ABNORMAL"
    else:
        state["l2_start"] = None

    # Level 1 (徵兆): 靜止下心率偏高 + HRV 下降 (持續超過 15 秒)
    if hr > 90 and hrv < 40:
        if state["l1_start"] is None: state["l1_start"] = now
        if (now - state["l1_start"]) > 15:
            return "Level 1", "E_SIGN"
    else:
        state["l1_start"] = None

    return "Level 0", "N001"

def start_edge_server(host='0.0.0.0', port=12345):
    db_conn = init_db()
    cur = db_conn.cursor()
    
    # 封包格式: !idffffffff (10個元素: ID, Time, T, HR, HRV, SpO2, Spd, Head, Dist, Bat)
    PACKET_FORMAT = '!idffffffff' 
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Edge Server (劇本一：風險判定版) 啟動中...")
    print(f"模式: Linux DEMO | 監聽: {host}:{port}")
    print("-" * 90)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((host, port))
        
        while True:
            try:
                raw_packet, addr = s.recvfrom(1024)
                
                # 遍歷註冊表嘗試解密
                for d_id, cfg in DEVICE_REGISTRY.items():
                    try:
                        if cfg["decrypt"] == "XOR":
                            decrypted = bytes([b ^ 0xAA for b in raw_packet])
                        else:
                            decoded = base64.b64decode(raw_packet)
                            decrypted = bytes([(b - 3) % 256 for b in decoded])
                        
                        # 解析封包
                        unpacked = struct.unpack(PACKET_FORMAT, decrypted)
                        uid, ts, temp, hr, hrv, o2, spd, head, dist, bat = unpacked
                        
                        if uid == d_id:
                            # 執行劇本邏輯判定
                            lvl, code = analyze_risk_logic(uid, hr, hrv, o2, spd)
                            
                            # 寫入資料庫 (含錯誤攔截)
                            try:
                                cur.execute('''
                                    INSERT INTO telemetry (
                                        device_id, device_name, temp, heart, hrv, spo2, 
                                        speed, heading, distance, battery, risk_level, event_code
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    uid, cfg["name"], round(temp, 2), round(hr, 2), round(hrv, 2), 
                                    round(o2, 2), round(spd, 2), round(head, 2), round(dist, 2), 
                                    round(bat, 2), lvl, code
                                ))
                                db_conn.commit()
                            except sqlite3.OperationalError as db_err:
                                print(f"\n[DB ERROR] 寫入失敗: {db_err}")
                                print(">> 請執行 'rm iot_data.db' 刪除舊資料庫後重啟伺服器。")
                                continue

                            # 輸出彩色日誌
                            color = "\033[91m" if lvl != "Level 0" else "\033[92m"
                            reset = "\033[0m"
                            ts_str = datetime.now().strftime('%H:%M:%S')
                            print(f"[{ts_str}] ID:{uid:<3} | {color}{lvl:<8}{reset} | HR:{hr:>5.1f} | HRV:{hrv:>5.1f} | SpO2:{o2:>5.1f}% | Code:{code}")
                            break
                    except Exception:
                        # 解析失敗則嘗試下一個註冊設備
                        continue
                        
            except KeyboardInterrupt:
                print("\n[INFO] 伺服器關閉。")
                break
            except Exception as e:
                print(f"\n[FATAL ERROR] 系統異常: {e}")

    db_conn.close()

if __name__ == "__main__":
    start_edge_server()