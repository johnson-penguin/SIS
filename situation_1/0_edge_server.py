import socket
import struct
import sqlite3
import base64
import time
import json
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
# --- 設備註冊與配置 ---
DEVICE_REGISTRY = {
    101: {"name": "A_Sensor_1", "decrypt": "XOR"},
    201: {"name": "B_Sensor_1", "decrypt": "B64"}
}

# 根據要求設定各等級頻率
LEVEL_INTERVALS = {
    "Level 0": 10.0,
    "Level 1": 5.0,
    "Level 2": 3.0,
    "Level 3": 1.0,
    "Level 4": 1.0
}

# 全域狀態追蹤 (儲存在記憶體中)
UE_STATES = {}
LAST_PRINT_TIME = {}

def init_db():
    """初始化資料庫"""
    # check_same_thread=False 允許不同執行緒 (UDP Server 與 Flask) 讀寫 DB
    conn = sqlite3.connect('iot_data.db', check_same_thread=False)
    cur = conn.cursor()
    
    # 1. 原始遙測資料表 (新增 needs_ack 欄位供 UI 判斷是否要跳出視窗)
    cur.execute('''CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        device_name TEXT,
        temp REAL, heart REAL, hrv REAL, spo2 REAL,
        speed REAL, heading REAL, distance REAL, battery REAL,
        risk_level TEXT, event_code TEXT,
        needs_ack BOOLEAN DEFAULT 0,
        server_received_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 2. 新增：事件紀錄總表 (紀錄異常區間與歷史陣列)
    cur.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        start_time DATETIME,
        end_time DATETIME,
        from_level TEXT,
        to_level TEXT,
        reason TEXT,
        action_taken TEXT,
        duration_sec REAL,
        hr_trend TEXT,
        hrv_trend TEXT
    )''')
    conn.commit()
    return conn

db_conn = init_db()

def generate_report(uid, lvl, code, hr, hrv, spo2, dur):
    """根據狀態生成事件通報文字"""
    state = UE_STATES.get(uid, {})
    prev_lvl = state.get("last_lvl", "Level 0")
    
    if lvl == "Level 1":
        return f"事件報告：個人循環浮動\n1.原因：生理數據持續波動\n2.數據：HR:{hr:.1f}, HRV:{hrv:.1f}, 持續:{dur:.1f}s"
    elif lvl == "Level 2":
        return f"事件報告：個人循環異常\n1.前級：{prev_lvl}\n2.行動：已發送提醒\n3.數據：HR:{hr:.1f}, HRV:{hrv:.1f}"
    elif lvl == "Level 3":
        return f"事件報告：個人循環風險\n1.前級：{prev_lvl}\n2.結果：通報照護端\n3.數據：HR:{hr:.1f}, SpO2:{spo2:.1f}%"
    elif lvl == "Level 4":
        return f"事件報告：個人循環危害\n1.行動：緊急救援通報\n2.狀態：極端異常且血氧下降"
    return ""

def analyze_risk_logic(uid, hr, hrv, spo2, speed):
    now = time.time()
    state = UE_STATES.setdefault(uid, {
        "anomaly_start": None, "static_start": None,
        "last_lvl": "Level 0", "last_ack_time": 0,
        "needs_ack": False, "hr_history": [], "hrv_history": []
    })
    
    is_static = (speed < 0.1)
    if is_static:
        if state["static_start"] is None: state["static_start"] = now
    else: state["static_start"] = None

    static_elapsed = (now - state["static_start"]) if state["static_start"] else 0
    is_abnormal = (hr > 100 or hrv < 35 or spo2 < 94)
    
    if is_abnormal:
        if state["anomaly_start"] is None:
            state["anomaly_start"] = now
            state["hr_history"] = []
            state["hrv_history"] = []
            state["needs_ack"] = False
        
        anomaly_elapsed = now - state["anomaly_start"]
        state["hr_history"].append(hr)
        state["hrv_history"].append(hrv)
        
        # 核心邏輯修改：根據等級決定是否「立即發出警報」
        lvl = "Level 0"
        if (hr > 140 or hr < 40) or spo2 < 90:
            lvl = "Level 4"
            state["needs_ack"] = True  # L4 立即警報，無視 10 分鐘 ACK
        elif anomaly_elapsed > 30.0 and static_elapsed > 15.0:
            lvl = "Level 3"
            state["needs_ack"] = True  # L3 立即警報，無視 10 分鐘 ACK
        elif anomaly_elapsed > 60.0:
            lvl = "Level 2"
            # L2 仍維持 10 分鐘 ACK 延遲邏輯
            if not state["needs_ack"] and (now - state["last_ack_time"] > 600):
                state["needs_ack"] = True
        elif anomaly_elapsed > 15.0:
            lvl = "Level 1"
            
        return lvl, "E_LOGIC"
    else:
        # ... 恢復邏輯保持不變 ...
        state["anomaly_start"] = None
        state["static_start"] = None
        state["needs_ack"] = False
        return "Level 0", "N001"



# =====================================================================
# 輕量級 API Server (用於接收 Web UI 的 ACK 動作)
# =====================================================================
app = Flask(__name__)
CORS(app)

# 關閉 Flask 預設的日誌洗畫面
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/api/ack_event', methods=['POST'])
def ack_event():
    uid = int(request.args.get('uid', 0))
    if uid in UE_STATES:
        now = time.time()
        UE_STATES[uid]["needs_ack"] = False
        UE_STATES[uid]["last_ack_time"] = now # 更新最後按按鈕時間
        
        # 新增：在事件表中紀錄「UE 已回覆」
        try:
            cur = db_conn.cursor()
            cur.execute('''INSERT INTO events 
                (device_id, start_time, end_time, from_level, to_level, reason, action_taken, duration_sec) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (uid, datetime.now(), datetime.now(), 
                 UE_STATES[uid]["last_lvl"], "ACK", "UE已回覆", "使用者手動確認提醒", 0))
            db_conn.commit()
        except Exception as e:
            print(f"DB Error: {e}")

        print(f"\n>>> [UI 互動] 設備 ID:{uid} 已回覆。提醒功能將暫停 1 分鐘。\n")
        return jsonify({"status": "success", "message": "ACK recorded"})
    return jsonify({"status": "error", "message": "UE not found"}), 404

def start_api_server():
    # 運行在 5002 port，避免與前端 Web 的 5000 / 5001 衝突
    app.run(host='0.0.0.0', port=5002, use_reloader=False)


# =====================================================================
# UDP 邊緣伺服器主程式
# =====================================================================
def start_edge_server(host='0.0.0.0', port=12345):
    # 啟動 API 執行緒
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    cur = db_conn.cursor()
    RECV_FORMAT = '!idffffffff10s' 
    CMD_FORMAT = '!10sf256s'
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Edge Server (時間序列追蹤版) 已啟動")
    print(" - UDP 監聽 Port : 12345 (接收終端數據)")
    print(" - API 監聽 Port : 5002  (接收前端 ACK)")
    print("-" * 110)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((host, port))
        
        while True:
            try:
                raw_packet, addr = s.recvfrom(1024)
                now_ts = time.time()
                
                for d_id, cfg in DEVICE_REGISTRY.items():
                    try:
                        # 解密
                        if cfg["decrypt"] == "XOR":
                            decrypted = bytes([b ^ 0xAA for b in raw_packet])
                        else:
                            decrypted = bytes([(b - 3) % 256 for b in base64.b64decode(raw_packet)])
                        
                        # 解析數據
                        uid, ts, temp, hr, hrv, o2, spd, head, dist, bat, ue_ack_bytes = struct.unpack(RECV_FORMAT, decrypted)
                        ue_ack_lvl = ue_ack_bytes.decode('utf-8').strip('\x00')
                        
                        if uid == d_id:
                            # 1. 邏輯判定
                            lvl, code = analyze_risk_logic(uid, hr, hrv, o2, spd)
                            needs_ack = UE_STATES[uid].get("needs_ack", False)
                            
                            # 2. 狀態變更通知
                            prev_lvl = UE_STATES[uid].get("last_lvl", "Level 0")
                            if lvl != prev_lvl:
                                reason_map = {
                                    "E_SIGN_PERSIST": "偵測到異常持續 > 15秒",
                                    "E_ABNORMAL_LONG": "異常狀態惡化持續 > 60秒",
                                    "E_URGENT": "緊急：觸發極端數值",
                                    "N001": "生理數據恢復正常"
                                }
                                print(f"\n>>> [通知] ID:{uid} 狀態變更: {prev_lvl} -> {lvl} ({reason_map.get(code, '')})\n")
                                UE_STATES[uid]["last_lvl"] = lvl

                            # 3. 資料庫寫入 (Telemetry)
                            cur.execute('''INSERT INTO telemetry 
                                (device_id, device_name, temp, heart, hrv, spo2, speed, heading, distance, battery, risk_level, event_code, needs_ack) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                       (uid, cfg["name"], temp, hr, hrv, o2, spd, head, dist, bat, lvl, code, needs_ack))
                            db_conn.commit()
                            
                            # 4. 指令與 ACK 同步機制 (回傳給 UE)
                            interval = LEVEL_INTERVALS.get(lvl, 4.0)
                            dur = (now_ts - UE_STATES[uid]["anomaly_start"]) if UE_STATES[uid]["anomaly_start"] else 0
                            report_msg = generate_report(uid, lvl, code, hr, hrv, o2, dur)
                            
                            cmd_packet = struct.pack(CMD_FORMAT, lvl.encode('utf-8'), interval, report_msg.encode('utf-8'))
                            s.sendto(cmd_packet, addr)

                            # 5. 螢幕 Log
                            if now_ts - LAST_PRINT_TIME.get(uid, 0) >= 1:
                                color_map = {
                                    "Level 0": "\033[92m", # 綠色
                                    "Level 1": "\033[36m", # 淺藍色
                                    "Level 2": "\033[93m", # 黃色
                                    "Level 3": "\033[31m", # 深紅色
                                    "Level 4": "\033[91m", # 亮紅色
                                }
                                color = color_map.get(lvl, "\033[0m")
                                reset = "\033[0m"
                                ack_str = "\033[91m[!!!立即警告!!!]\033[0m" if (needs_ack and lvl in ["Level 3", "Level 4"]) else ("\033[93m[待確認]\033[0m" if needs_ack else "")
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] ID:{uid} | {color}{lvl:<8}{reset} | Spd:{spd:>4.2f} | HR:{hr:>5.1f} | {ack_str}")
                                LAST_PRINT_TIME[uid] = now_ts
                            break
                    except Exception as inner_e: 
                        continue
                        
            except KeyboardInterrupt: 
                break
            except Exception as e: 
                print(f"Error: {e}")

    db_conn.close()

if __name__ == "__main__":
    start_edge_server()