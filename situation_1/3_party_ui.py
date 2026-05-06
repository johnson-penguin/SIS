from flask import Flask, render_template_string, jsonify
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.getcwd(), 'iot_data.db')
TARGET_UE_ID = 101 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>SIS 多方通報戰情看板</title>
    <style>
        body { font-family: 'Segoe UI', "Microsoft JhengHei", sans-serif; background: #0b0e14; color: #cfd8dc; margin: 0; padding: 20px; overflow-x: hidden; }
        .header { border-bottom: 2px solid #263238; padding-bottom: 15px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { margin: 0; font-size: 1.8em; }
        
        .sys-status { padding: 8px 16px; border-radius: 8px; font-weight: bold; background: #1c2331; border: 1px solid #37474f; transition: 0.3s; }
        .status-l3 { background: rgba(245, 158, 11, 0.2); border-color: #f59e0b; color: #fbbf24; }
        .status-l4 { background: rgba(239, 68, 68, 0.2); border-color: #ef4444; color: #f87171; box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }

        .dashboard-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
        
        /* 基礎面板樣式 */
        .panel { 
            background: #161c27; border-radius: 16px; border: 2px solid #263238; 
            padding: 20px; display: flex; flex-direction: column; gap: 15px;
            transition: all 0.4s ease; min-height: 450px; position: relative;
        }
        .panel-header { font-size: 1.2em; font-weight: bold; border-bottom: 1px solid #263238; padding-bottom: 10px; display: flex; align-items: center; justify-content: space-between; }
        
        /* 狀態遮罩 (未啟動時) */
        .overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(11, 14, 20, 0.85); border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.5em; color: #475569; z-index: 10; font-weight: bold; transition: opacity 0.3s; }
        .panel.active .overlay { opacity: 0; pointer-events: none; }

        /* Level 3 樣式 (警告) */
        .panel.warn { border-color: #f59e0b; box-shadow: inset 0 0 20px rgba(245, 158, 11, 0.1); }
        .panel.warn .panel-header { color: #fbbf24; border-bottom-color: #f59e0b; }
        
        /* Level 4 樣式 (危急) */
        .panel.danger { border-color: #ef4444; box-shadow: inset 0 0 30px rgba(239, 68, 68, 0.2); animation: pulse-border 1.5s infinite; }
        .panel.danger .panel-header { color: #f87171; border-bottom-color: #ef4444; }
        @keyframes pulse-border { 0% { box-shadow: inset 0 0 20px rgba(239, 68, 68, 0.2); } 50% { box-shadow: inset 0 0 40px rgba(239, 68, 68, 0.5); } 100% { box-shadow: inset 0 0 20px rgba(239, 68, 68, 0.2); } }

        /* 面板內容小元件 */
        .data-row { display: flex; justify-content: space-between; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; font-family: monospace; font-size: 1.1em; }
        .msg-bubble { background: #1e293b; padding: 15px; border-radius: 12px; border-left: 4px solid #3b82f6; line-height: 1.5; font-size: 0.95em; }
        .map-box { height: 150px; background: #0f172a; border-radius: 8px; border: 1px dashed #475569; display: flex; align-items: center; justify-content: center; color: #64748b; font-family: monospace; flex-direction: column; }
        /* Level 1: 徵兆 (淺藍) */
        .border-info { border-left: 8px solid #38bdf8; }
        .text-l1 { color: #38bdf8; }
        /* Level 2: 警告 (黃色) */
        .border-warning { border-left: 8px solid #fbbf24; }
        .text-l2 { color: #fbbf24; }
        /* Level 3: 風險 (深紅色) */
        .border-danger-dark { border-left: 8px solid #b91c1c; }
        .text-l3 { color: #b91c1c; }
        /* Level 4: 危害 (亮紅色) */
        .border-danger-bright { border-left: 8px solid #ef4444; }
        .text-l4 { color: #ef4444; }
        /* ACK: 已回覆 (紫色) */
        .border-ack { border-left: 8px solid #a855f7; }
        .blink-text { animation: blink 1s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>

    <div class="header">
        <h1>🚨 SIS 多方通報戰情看板 <span style="font-size: 0.5em; color: #10b981; font-weight: normal;">● API 監聽中</span></h1>
        <div id="sys-status" class="sys-status">系統待命中 (Level 0-2)</div>
    </div>

    <div class="dashboard-grid">
        <div class="panel" id="panel-family">
            <div class="overlay" id="overlay-family">待命中</div>
            <div class="panel-header">📱 關係人通知 (Family) <span id="time-family" style="font-size: 0.7em; color: #94a3b8;"></span></div>
            <div class="msg-bubble" id="msg-family">
                <b>系統自動簡訊</b><br><br>
                尚無異常通知。
            </div>
            <div class="data-row"><span>最後已知座標</span><span>25.0330, 121.5654</span></div>
        </div>

        <div class="panel" id="panel-nurse">
            <div class="overlay" id="overlay-nurse">待命中</div>
            <div class="panel-header">🏥 照護工作站 (Caregiver) <span class="blink-text" id="status-nurse" style="font-size: 0.7em;"></span></div>
            <div style="color: #94a3b8; font-size: 0.9em;">病患 ID: UE 101 | 狀態監控</div>
            <div class="data-row"><span>心率 (HR)</span><span id="v-hr" style="font-weight: bold;">--</span></div>
            <div class="data-row"><span>血氧 (SpO2)</span><span id="v-o2" style="font-weight: bold;">--</span></div>
            <div class="data-row"><span>活動速率 (Spd)</span><span id="v-spd" style="font-weight: bold;">--</span></div>
            <div class="msg-bubble" id="msg-nurse" style="border-left-color: #f59e0b; margin-top: auto;">
                等待醫療介入指示...
            </div>
        </div>

        <div class="panel" id="panel-ems">
            <div class="overlay" id="overlay-ems">未達通報標準 (Locked)</div>
            <div class="panel-header">🚑 119 救援派遣 (EMS) <span style="font-size: 0.7em; background: #ef4444; color: white; padding: 2px 6px; border-radius: 4px;">最高優先級</span></div>
            <div class="map-box">
                <span style="font-size: 2em; margin-bottom: 5px;">📍</span>
                <span>鎖定患者座標中...</span>
                <span style="color: #ef4444; margin-top: 5px; font-weight: bold;">預估抵達 (ETA): 4 mins</span>
            </div>
            <div class="data-row" style="color: #ef4444; border: 1px solid #ef4444;"><span>極端心率警戒</span><span id="ems-hr">--</span></div>
            <div class="data-row" style="color: #ef4444; border: 1px solid #ef4444;"><span>血氧嚴重低下</span><span id="ems-o2">--</span></div>
        </div>
    </div>

    <script>
        const UID = {{ uid }};
        
        function updateUI(d) {
            const sysStatus = document.getElementById('sys-status');
            const pFamily = document.getElementById('panel-family');
            const pNurse = document.getElementById('panel-nurse');
            const pEms = document.getElementById('panel-ems');

            // 更新共用數據
            document.getElementById('time-family').innerText = new Date().toLocaleTimeString();
            document.getElementById('v-hr').innerText = d.hr.toFixed(1) + ' BPM';
            document.getElementById('v-o2').innerText = d.o2.toFixed(1) + ' %';
            document.getElementById('v-spd').innerText = d.spd.toFixed(2) + ' m/s';
            document.getElementById('ems-hr').innerText = d.hr.toFixed(1);
            document.getElementById('ems-o2').innerText = d.o2.toFixed(1) + '%';

            // 狀態機邏輯：漸進式通報
            if (d.lvl === "Level 3") {
                sysStatus.className = "sys-status status-l3";
                sysStatus.innerText = "高風險異常 (Level 3) - 已通知照護端";
                
                // 啟動 Family & Nurse 面板，改為警告樣式
                pFamily.className = "panel warn active";
                pNurse.className = "panel warn active";
                pEms.className = "panel"; // EMS 保持待命

                document.getElementById('msg-family').innerHTML = `<b>系統自動簡訊</b><br><br>⚠️ 異常提醒：<br>偵測到 UE ${UID} 生理指標異常且活動力喪失 (靜止)。<br>已同步通知照護中心處理。`;
                document.getElementById('msg-family').style.borderLeftColor = "#f59e0b";
                
                document.getElementById('status-nurse').innerText = "需要人工介入";
                document.getElementById('status-nurse').style.color = "#fbbf24";
                document.getElementById('msg-nurse').innerHTML = "<b>系統建議：</b><br>病患已靜止超過 15 秒且伴隨心率異常，請立即派員前往現場確認是否有跌倒或昏迷狀況。";
                
            } else if (d.lvl === "Level 4") {
                sysStatus.className = "sys-status status-l4";
                sysStatus.innerText = "緊急救援通報 (Level 4) - 全面啟動";
                
                // 啟動所有面板，改為危急樣式
                pFamily.className = "panel danger active";
                pNurse.className = "panel danger active";
                pEms.className = "panel danger active";

                document.getElementById('msg-family').innerHTML = `<b>系統自動簡訊</b><br><br>🚨 緊急通知：<br>UE ${UID} 生理指標出現極端危險數值 (SpO2 < 90%)。<br>系統已自動通報 119 派遣救護車。`;
                document.getElementById('msg-family').style.borderLeftColor = "#ef4444";
                
                document.getElementById('status-nurse').innerText = "CODE BLUE";
                document.getElementById('status-nurse').style.color = "#ef4444";
                document.getElementById('msg-nurse').innerHTML = "<b>🚨 急救指示：</b><br>病患可能發生休克或嚴重缺氧！請立即攜帶急救設備 (AED/氧氣) 前往現場，救護車已在途中。";
                document.getElementById('msg-nurse').style.borderLeftColor = "#ef4444";

            } else {
                // Level 0, 1, 2：第三方看板保持休眠 (因 L1/L2 僅通知當事人 UE)
                sysStatus.className = "sys-status";
                sysStatus.innerText = `系統待命中 (${d.lvl})`;
                
                pFamily.className = "panel";
                pNurse.className = "panel";
                pEms.className = "panel";
                
                document.getElementById('msg-family').style.borderLeftColor = "#3b82f6";
                document.getElementById('msg-nurse').style.borderLeftColor = "#f59e0b";
            }
        }

        async function pollData() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                if (data.lvl) updateUI(data);
            } catch(e) {}
        }

        setInterval(pollData, 1000);
        pollData();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, uid=TARGET_UE_ID)

@app.route('/api/status')
def get_status():
    if not os.path.exists(DB_PATH): return jsonify({})
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('''
            SELECT risk_level, heart, spo2, speed 
            FROM telemetry WHERE device_id = ? ORDER BY id DESC LIMIT 1
        ''', (TARGET_UE_ID,))
        r = cur.fetchone()
        conn.close()
        if r:
            return jsonify({"lvl": r[0], "hr": r[1], "o2": r[2], "spd": r[3]})
    except: pass
    return jsonify({"lvl": "Level 0", "hr": 0, "o2": 0, "spd": 0})

if __name__ == '__main__':
    # 運行在 5003 端口，避免與其他網頁衝突
    app.run(host='0.0.0.0', port=5003)