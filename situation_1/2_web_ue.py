from flask import Flask, render_template_string, jsonify, request
import sqlite3
import os
import requests

app = Flask(__name__)

# 資料庫路徑
DB_PATH = os.path.join(os.getcwd(), 'iot_data.db')
TARGET_UE_ID = 101 
FREQ_MAP = {"Level 0": 4.0, "Level 1": 2.0, "Level 2": 1.0, "Level 3": 0.5, "Level 4": 0.2}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>SIS 個人健康分析系統 - UE 終端介面</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', "Microsoft JhengHei", sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; overflow-x: hidden; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .kpi-card { background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; text-align: center; transition: 0.3s; }
        .kpi-label { font-size: 0.9em; color: #94a3b8; margin-bottom: 8px; }
        .kpi-val { font-size: 2em; font-weight: bold; color: #38bdf8; }
        .main-chart-box { background: #1e293b; padding: 20px; border-radius: 15px; border: 1px solid #334155; margin-bottom: 30px; height: 300px; position: relative; }
        .event-section { border-top: 2px solid #334155; padding-top: 20px; }
        .event-list { display: flex; flex-direction: column; gap: 15px; }
        .event-card { background: #1e293b; border-radius: 12px; padding: 15px; display: grid; grid-template-columns: 1.2fr 2.8fr; gap: 20px; border: 1px solid #334155; animation: slideIn 0.4s ease-out; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
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
        .border-success { border-left: 8px solid #10b981; }
        .snapshot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; height: 140px; }
        .snapshot-box { background: #0f172a; border-radius: 8px; padding: 8px; position: relative; border: 1px solid #1e293b; }
        .snapshot-label { position: absolute; top: 5px; left: 10px; font-size: 0.7em; color: #94a3b8; z-index: 10; }
        #alert-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
        .alert-box { background: #1e293b; padding: 40px; border-radius: 24px; border: 3px solid #ef4444; text-align: center; box-shadow: 0 0 50px rgba(239, 68, 68, 0.3); max-width: 500px; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.02); } 100% { transform: scale(1); } }
        .ack-btn { background: #ef4444; color: white; border: none; padding: 15px 40px; font-size: 1.2em; font-weight: bold; border-radius: 12px; cursor: pointer; margin-top: 20px; transition: 0.2s; }
        .ack-btn:hover { background: #dc2626; transform: scale(1.05); }
    </style>
</head>
<body>
    <div id="alert-overlay">
        <div class="alert-box">
            <h2 style="color: #ef4444; margin-bottom: 10px;">🚨 系統高風險警告</h2>
            <p style="font-size: 1.1em; color: #cbd5e1; line-height: 1.6;">偵測到您的生理指標持續異常已超過 60 秒。<br>請確認目前身體狀況，照護端已收到通知。</p>
            <button class="ack-btn" onclick="sendAck()">我已收到提醒</button>
        </div>
    </div>

    <div class="header">
        <h1>👤 終端分析: UE {{ uid }} <span id="sync-status" style="font-size: 0.4em; color: #10b981;">● 連線中</span></h1>
        <div id="clock" style="color: #94a3b8;">--:--:--</div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-label">心率 (BPM)</div><div class="kpi-val" id="v-hr">--</div></div>
        <div class="kpi-card"><div class="kpi-label">HRV (ms)</div><div class="kpi-val" id="v-hrv">--</div></div>
        <div class="kpi-card"><div class="kpi-label">當前風險</div><div class="kpi-val" id="v-lvl">--</div></div>
        <div class="kpi-card"><div class="kpi-label">回報頻率</div><div class="kpi-val" id="v-freq" style="color:#fbbf24">--</div></div>
    </div>

    <div class="main-chart-box"><canvas id="realtime-chart"></canvas></div>

    <div class="event-section" style="border-top: none; padding-top: 0; margin-bottom: 30px;">
        <h2 style="margin-bottom: 20px; color: #38bdf8;">🛡️ 我的保險專區</h2>
        <div style="background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <span style="font-size: 1.1em;">長期健康分析與保單服務</span>
                <button class="ack-btn" style="margin-top: 0; padding: 10px 20px; background: #10b981; font-size: 1em;" onclick="applyInsurance(this)">📊 匯出長期報告並申購</button>
            </div>
            <div id="policy-list" style="display: flex; flex-direction: column; gap: 10px;">
                <div style="color: #94a3b8; font-size: 0.9em;">尚未申購任何保單。</div>
            </div>
        </div>
    </div>

    <div class="event-section">
        <h2 style="margin-bottom: 20px;">📜 事件追溯紀錄 (Demo 專用展開)</h2>
        <div class="event-list" id="event-list"></div>
    </div>

    <script>
        const TARGET_UID = {{ uid }};
        const FREQ_MAP = {{ freq_map|tojson }};
        let lastLevel = "Level 0";
        let anomalyStartTime = null;
        let mainChart = null;
        let dataBuffer = []; 

        function init() {
            const ctx = document.getElementById('realtime-chart').getContext('2d');
            mainChart = new Chart(ctx, {
                type: 'line',
                data: { labels: [], datasets: [
                    { label: '心率', borderColor: '#38bdf8', data: [], tension: 0.3, pointRadius: 0, borderWidth: 3 },
                    { label: 'HRV', borderColor: '#a855f7', data: [], tension: 0.3, pointRadius: 0, borderWidth: 3 }
                ]},
                options: { maintainAspectRatio: false, animation: false, scales: { y: { min: 20, max: 160, grid: { color: '#334155' } }, x: { grid: { display: false } } }, plugins: { legend: { labels: { color: '#f8fafc' } } } }
            });
            update();
            fetchPolicies();
            fetchClaims();
            setInterval(update, 1000);
            setInterval(fetchPolicies, 3000);
            setInterval(fetchClaims, 3000);
            setInterval(() => { document.getElementById('clock').innerText = new Date().toLocaleTimeString(); }, 1000);
        }

        async function update() {
            try {
                const res = await fetch('/api/ue_status');
                const d = await res.json();
                
                // 防呆：如果尚未收到有效資料，略過本次更新，不報錯
                if (d.hr === undefined || d.hr === null) return;
                
                document.getElementById('sync-status').innerText = "● 連線中";
                document.getElementById('sync-status').style.color = "#10b981";

                const nowLabel = new Date().toLocaleTimeString();
                document.getElementById('v-hr').innerText = d.hr.toFixed(1);
                document.getElementById('v-hrv').innerText = d.hrv.toFixed(1);
                document.getElementById('v-lvl').innerText = d.lvl;
                document.getElementById('v-freq').innerText = (FREQ_MAP[d.lvl] || 4.0) + "s";

                if (d.needs_ack) {
                    document.getElementById('alert-overlay').style.display = 'flex';
                } else {
                    document.getElementById('alert-overlay').style.display = 'none';
                }

                dataBuffer.push({ time: nowLabel, hr: d.hr, hrv: d.hrv, lvl: d.lvl });
                if(dataBuffer.length > 600) dataBuffer.shift();

                mainChart.data.labels.push(nowLabel);
                mainChart.data.datasets[0].data.push(d.hr);
                mainChart.data.datasets[1].data.push(d.hrv);
                if(mainChart.data.labels.length > 40) {
                    mainChart.data.labels.shift();
                    mainChart.data.datasets.forEach(ds => ds.data.shift());
                }
                mainChart.update();

                if (d.lvl !== lastLevel) {
                    const from = lastLevel;
                    const to = d.lvl;
                    if (from === "Level 0" && to !== "Level 0") {
                        anomalyStartTime = nowLabel;
                        setTimeout(() => captureSnapshot(nowLabel, from, to, "start"), 3000);
                    } else if (to === "Level 0") {
                        setTimeout(() => captureSnapshot(nowLabel, from, to, "recovery", anomalyStartTime), 3000);
                        anomalyStartTime = null;
                    } else {
                        setTimeout(() => captureSnapshot(nowLabel, from, to, "change"), 3000);
                    }
                    lastLevel = to;
                }
            } catch(e) {
                document.getElementById('sync-status').innerText = "● 連線中斷";
                document.getElementById('sync-status').style.color = "#ef4444";
            }
        }

        async function sendAck() {
        try {
            await fetch(`http://${window.location.hostname}:5002/api/ack_event?uid=${TARGET_UID}`, { method: 'POST' });
            document.getElementById('alert-overlay').style.display = 'none';
            
            // 新增：按下按鈕後，立刻在 UI 列表插入一筆紫色紀錄
            const nowLabel = new Date().toLocaleTimeString();
            const html = `
                <div class="event-card border-ack">
                    <div class="event-info">
                        <div style="font-weight: bold; color: #a855f7; font-size: 1.2em; margin-bottom: 5px;">🙋 UE 已回覆</div>
                        <div style="font-size: 0.9em; color: #94a3b8; line-height: 1.6;">
                            <b>回覆時間：</b> ${nowLabel}<br>
                            <b>操作說明：</b> 使用者已點擊警告確認，提醒將於 10 分鐘後重啟。<br>
                            <span style="color: #64748b;">[互動紀錄：手動 ACK]</span>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: center; color: #a855f7; font-size: 3em;">
                        💬
                    </div>
                </div>
            `;
            document.getElementById('event-list').insertAdjacentHTML('afterbegin', html);
            
        } catch (e) {
            alert("無法連線至 Edge Server API (5002)");
            }
        }

        function captureSnapshot(targetTime, fromLvl, toLvl, mode, startTime = null) {
            const idx = dataBuffer.findIndex(item => item.time === targetTime);
            if (idx === -1) return;

            let snapshotData = [];
            let tTitle = "", tIcon = "", bClass = "", tColor = "", desc = "";

            if (toLvl === "Level 0") {
                tTitle = "生理狀態恢復"; tIcon = "✅"; bClass = "border-success"; tColor = "#10b981"; 
                desc = "自動分析：完整異常週期數據回溯";
                const sIdx = dataBuffer.findIndex(item => item.time === startTime);
                const startPos = sIdx !== -1 ? Math.max(0, sIdx - 5) : Math.max(0, idx - 20);
                snapshotData = dataBuffer.slice(startPos, idx + 5);
            } else {
                // 根據 Level 細分視覺與說明
                if (toLvl === "Level 1") {
                    bClass = "border-info"; tColor = "#38bdf8"; tTitle = "偵測到異常徵兆"; tIcon = "ℹ️";
                    desc = "關鍵點：偵測到數據波動 > 15 秒";
                } else if (toLvl === "Level 2") {
                    bClass = "border-warning"; tColor = "#fbbf24"; tTitle = "異常狀態惡化"; tIcon = "⚠️";
                    desc = "關鍵點：異常持續達 60 秒";
                } else if (toLvl === "Level 3") {
                    bClass = "border-danger-dark"; tColor = "#b91c1c"; tTitle = "高風險狀態 (活動喪失)"; tIcon = "🚨";
                    desc = "關鍵點：異常持續且完全靜止超過 15 秒";
                } else if (toLvl === "Level 4") {
                    bClass = "border-danger-bright"; tColor = "#ef4444"; tTitle = "緊急危害觸發"; tIcon = "💥";
                    desc = "關鍵點：極端生理數值 (休克或嚴重缺氧邊緣)";
                }
                
                snapshotData = dataBuffer.slice(Math.max(0, idx - 10), idx + 10);
            }

            const cardId = Date.now();
            const html = `
                <div class="event-card ${bClass}">
                    <div class="event-info">
                        <div style="font-weight: bold; color: ${tColor}; font-size: 1.2em; margin-bottom: 5px;">${tIcon} ${tTitle}</div>
                        <div style="font-size: 0.9em; color: #94a3b8; line-height: 1.6;">
                            <b>狀態轉換：</b> ${fromLvl} → ${toLvl}<br>
                            <b>記錄時間：</b> ${targetTime}<br>
                            <b>判定說明：</b> ${desc}<br>
                            <span style="color: #64748b;">[劇本一：生理與動態連續監控]</span>
                        </div>
                    </div>
                    <div class="snapshot-grid">
                        <div class="snapshot-box"><span class="snapshot-label">心率趨勢</span><canvas id="hr-${cardId}"></canvas></div>
                        <div class="snapshot-box"><span class="snapshot-label">HRV趨勢</span><canvas id="hrv-${cardId}"></canvas></div>
                    </div>
                </div>
            `;
            document.getElementById('event-list').insertAdjacentHTML('afterbegin', html);
            renderSmallChart(`hr-${cardId}`, snapshotData.map(s => s.hr), tColor, 40, 160); // 顏色與主標題同步
            renderSmallChart(`hrv-${cardId}`, snapshotData.map(s => s.hrv), '#a855f7', 0, 80);
        }
        function renderSmallChart(id, data, color, min, max) {
            new Chart(document.getElementById(id), { type: 'line', data: { labels: new Array(data.length).fill(''), datasets: [{ borderColor: color, data: data, pointRadius: 2, fill: false, tension: 0.2, borderWidth: 2 }] }, options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { min: min, max: max, ticks: { display: false }, grid: { display: false } } } } });
        }
        
        async function applyInsurance(btn) {
            btn.disabled = true;
            btn.innerText = "申請中...";
            try {
                let recentData = dataBuffer.slice(-50);
                let avgHr = dataBuffer.length ? (dataBuffer.reduce((acc, v) => acc + v.hr, 0) / dataBuffer.length).toFixed(1) : "N/A";
                let reportObj = {
                    text: `長期健康分析報告\n總採樣數：${dataBuffer.length}\n平均心率：${avgHr} BPM\n近期活動：正常\n(由系統自動匯出)`,
                    labels: recentData.map(d => d.time),
                    hr: recentData.map(d => d.hr),
                    hrv: recentData.map(d => d.hrv)
                };
                
                await fetch(`http://${window.location.hostname}:5002/api/insurance/apply`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({uid: TARGET_UID, report_content: JSON.stringify(reportObj)})
                });
                btn.innerText = "✅ 申請已送出";
                btn.style.background = "#475569";
                fetchPolicies();
            } catch(e) {
                alert("申請失敗");
                btn.disabled = false;
                btn.innerText = "📊 匯出長期報告並申購";
            }
        }

        let seenSettledClaims = new Set();
        async function fetchClaims() {
            try {
                const res = await fetch(`http://${window.location.hostname}:5002/api/insurance/claims`);
                const claims = await res.json();
                const myClaims = claims.filter(c => c.uid === TARGET_UID && c.status === 'SETTLED');
                
                myClaims.forEach(c => {
                    if (!seenSettledClaims.has(c.id)) {
                        seenSettledClaims.add(c.id);
                        
                        const html = `
                            <div class="event-card border-success" style="border-left-color: #10b981;">
                                <div class="event-info" style="grid-column: 1 / span 2;">
                                    <div style="font-weight: bold; color: #10b981; font-size: 1.2em; margin-bottom: 5px;">✅ 理賠結算明細 (來自保險中心)</div>
                                    <div style="font-size: 0.9em; color: #94a3b8; line-height: 1.6; background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 8px; margin-top: 10px;">
                                        <div style="display: flex; justify-content: space-between;"><span>理賠單號：</span><b>#CLM-${c.id}</b></div>
                                        <div style="display: flex; justify-content: space-between;"><span>險種類別：</span><b>${c.type}</b></div>
                                        <div style="display: flex; justify-content: space-between;"><span>結算時間：</span><b>${c.d_at}</b></div>
                                        <hr style="border: 0; border-top: 1px solid #334155; margin: 10px 0;">
                                        <div style="display: flex; justify-content: space-between;"><span>實際住院天數：</span><b>${c.days} 天</b></div>
                                        <div style="display: flex; justify-content: space-between; font-size: 1.2em; color: #10b981; margin-top: 5px;">
                                            <span>核准理賠總額：</span><b>$ ${c.amount.toLocaleString()}</b>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                        document.getElementById('event-list').insertAdjacentHTML('afterbegin', html);
                    }
                });
            } catch(e) {}
        }

        async function fetchPolicies() {
            try {
                const res = await fetch(`http://${window.location.hostname}:5002/api/insurance/policies`);
                const policies = await res.json();
                const myPolicies = policies.filter(p => p.uid === TARGET_UID);
                const listDiv = document.getElementById('policy-list');
                
                if (myPolicies.length === 0) return;
                
                let html = '';
                myPolicies.forEach(p => {
                    let statusColor = p.status === 'PENDING' ? '#f59e0b' : '#10b981';
                    let statusText = p.status === 'PENDING' ? '審核中' : '生效中';
                    html += `
                        <div style="background: #0f172a; padding: 15px; border-radius: 8px; border-left: 4px solid ${statusColor};">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <b>${p.type}</b>
                                <span style="color: ${statusColor}; font-size: 0.9em; font-weight: bold;">${statusText}</span>
                            </div>
                            <div style="font-size: 0.9em; color: #cbd5e1;">申請時間：${p.created_at}</div>
                            ${p.feedback ? `<div style="margin-top: 10px; padding: 10px; background: rgba(56, 189, 248, 0.1); border-radius: 6px; color: #38bdf8; font-size: 0.9em; white-space: pre-wrap;"><b>💌 保險公司定期回饋：</b><br>${p.feedback}</div>` : ''}
                        </div>
                    `;
                });
                listDiv.innerHTML = html;
            } catch(e) {}
        }
        
        init();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, uid=TARGET_UE_ID, freq_map=FREQ_MAP)

@app.route('/api/ue_status')
def get_ue_status():
    # 預設回傳值，確保前端永遠能拿到格式正確的 JSON，不會崩潰
    res = {"lvl": "Level 0", "hr": 0, "hrv": 0, "o2": 0, "needs_ack": False}
    
    if not os.path.exists(DB_PATH): 
        return jsonify(res)
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('''
            SELECT risk_level, heart, hrv, spo2, needs_ack 
            FROM telemetry 
            WHERE device_id = ? 
            ORDER BY id DESC LIMIT 1
        ''', (TARGET_UE_ID,))
        r = cur.fetchone()
        if r:
            res = {"lvl": r[0], "hr": r[1], "hrv": r[2], "o2": r[3], "needs_ack": bool(r[4])}
        conn.close()
    except Exception as e:
        # 若發生 SQL 錯誤 (如舊版資料庫欄位不符)，仍回傳預設值
        pass 
        
    return jsonify(res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)