from flask import Flask, render_template_string, jsonify
import sqlite3
import os

app = Flask(__name__)

# 資料庫路徑與配置
DB_PATH = os.path.join(os.getcwd(), 'iot_data.db')
AREA_MAP = { "區域 A": [101, 102], "區域 B": [201, 202] }
FREQ_MAP = {"Level 0": 4.0, "Level 1": 2.0, "Level 2": 1.0, "Level 3": 0.5, "Level 4": 0.2}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>SIS 邊緣監控中樞 - 全域狀態與事件回溯</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', "Microsoft JhengHei", sans-serif; background: #0b0e14; color: #cfd8dc; margin: 0; padding: 20px; overflow-x: hidden; }
        .header { border-bottom: 2px solid #263238; padding-bottom: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .nav { display: flex; gap: 10px; }
        .btn { padding: 8px 18px; background: #1c2331; border: 1px solid #37474f; color: #fff; cursor: pointer; border-radius: 6px; border: none; transition: 0.3s; }
        .btn:hover { background: #263238; }
        .btn.active { background: #0081cb; font-weight: bold; }
        
        /* KPI 卡片 */
        .kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 20px; }
        .kpi-card { background: #161c27; padding: 15px; border-radius: 12px; border: 1px solid #263238; text-align: center; }
        .kpi-label { font-size: 0.85em; color: #90a4ae; margin-bottom: 5px; }
        .kpi-val { font-size: 1.8em; font-weight: bold; color: #00d4ff; }

        .main-chart-container { background: #161c27; border-radius: 12px; padding: 20px; border: 1px solid #263238; height: 280px; margin-bottom: 30px; }

        /* 歷史日誌排版 */
        .event-section { border-top: 2px solid #37474f; padding-top: 20px; }
        .event-list { display: flex; flex-direction: column; gap: 15px; }
        
        .event-card { 
            background: #1e293b; border-radius: 12px; padding: 15px; 
            display: grid; grid-template-columns: 1.2fr 2.8fr; gap: 20px;
            border: 1px solid #334155; animation: slideIn 0.4s ease-out;
            position: relative;
        }
        
        .border-info { border-left: 8px solid #38bdf8; }    /* Level 1 */
        .border-danger { border-left: 8px solid #ef4444; }  /* Level 2 */
        .border-success { border-left: 8px solid #10b981; } /* 恢復 */
        
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .event-info { display: flex; flex-direction: column; justify-content: center; }
        .ue-tag { background: #0081cb; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.8em; font-weight: bold; width: fit-content; margin-bottom: 10px; }
        .event-title { font-weight: bold; font-size: 1.2em; margin-bottom: 8px; }
        .event-meta { font-size: 0.9em; color: #94a3b8; line-height: 1.6; }
        
        .snapshot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; height: 140px; }
        .snapshot-box { background: #0b0e14; border-radius: 8px; padding: 8px; position: relative; border: 1px solid #1e293b; }
        .snapshot-label { position: absolute; top: 5px; left: 10px; font-size: 0.7em; color: #94a3b8; z-index: 10; }

        /* 全域警告彈窗 */
        #alert-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(11, 14, 20, 0.9); display: none; flex-direction: column;
            align-items: center; justify-content: center; z-index: 9999;
        }
        .alert-box {
            background: #1e293b; padding: 40px; border-radius: 20px;
            border: 3px solid #ef4444; text-align: center; max-width: 500px;
            box-shadow: 0 0 50px rgba(239, 68, 68, 0.2); animation: pulse 2s infinite;
        }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.02); } 100% { transform: scale(1); } }
        
        .ack-btn {
            background: #ef4444; color: white; border: none; padding: 15px 40px;
            font-size: 1.2em; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 25px; transition: 0.2s;
        }
        .ack-btn:hover { background: #dc2626; transform: scale(1.05); }
        .border-ack { border-left: 8px solid #a855f7; }
    </style>
</head>
<body>
    <div id="alert-overlay">
        <div class="alert-box">
            <h2 style="color: #ef4444; font-size: 2em; margin-bottom: 10px;">🚨 高風險設備警告</h2>
            <p id="alert-msg" style="font-size: 1.2em; color: #cbd5e1; line-height: 1.5;">--</p>
            <button class="ack-btn" onclick="acknowledgeLevel2()">管理員確認已處置</button>
        </div>
    </div>

    <div class="header">
        <div>
            <h1 style="margin:0;">📡 邊緣監控中樞 <span style="font-size: 0.5em; color: #10b981;">● 即時連線</span></h1>
            <div style="font-size: 0.85em; color: #90a4ae; margin-top: 5px;" id="global-clock">--:--:--</div>
        </div>
        <div class="nav" id="ue-selector"></div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-label">設備心率</div><div class="kpi-val" id="v-hr">--</div></div>
        <div class="kpi-card"><div class="kpi-label">設備HRV</div><div class="kpi-val" id="v-hrv">--</div></div>
        <div class="kpi-card"><div class="kpi-label">設備血氧</div><div class="kpi-val" id="v-o2">--</div></div>
        <div class="kpi-card"><div class="kpi-label">當前風險等級</div><div class="kpi-val" id="v-lvl">--</div></div>
        <div class="kpi-card"><div class="kpi-label">更新頻率</div><div class="kpi-val" id="v-freq" style="color:#fbbf24">--</div></div>
    </div>

    <div class="main-chart-container"><canvas id="main-canvas"></canvas></div>

    <div class="event-section">
        <h2 style="margin-bottom: 15px;">📜 全域設備狀態變更歷史 (動態回溯)</h2>
        <div class="event-list" id="global-event-list"></div>
    </div>

    <script>
        const AREA_MAP = {{ area_map|tojson }};
        const FREQ_MAP = {{ freq_map|tojson }};
        let currentUE = 101;
        let lastLevels = {};
        let anomalyStartTimes = {}; 
        let mainChart = null;
        let ueDataBuffers = {};
        let currentAlertUid = null; // 記錄當前觸發警報的設備 ID

        function init() {
            renderNav();
            const ctx = document.getElementById('main-canvas').getContext('2d');
            mainChart = new Chart(ctx, {
                type: 'line',
                data: { labels: [], datasets: [
                    { label: '心率', borderColor: '#ef4444', data: [], tension: 0.3, pointRadius: 0, borderWidth: 2 },
                    { label: 'HRV', borderColor: '#a855f7', data: [], tension: 0.3, pointRadius: 0, borderWidth: 2 }
                ]},
                options: { 
                    maintainAspectRatio: false, animation: false, 
                    scales: { y: { min: 20, max: 160, grid: { color: '#263238' } }, x: { grid: { display: false } } },
                    plugins: { legend: { labels: { color: '#cfd8dc' } } }
                }
            });
            update();
            fetchSettledClaims();
            setInterval(update, 1000);
            setInterval(fetchSettledClaims, 3000);
            setInterval(() => { document.getElementById('global-clock').innerText = new Date().toLocaleTimeString(); }, 1000);
        }

        function renderNav() {
            const nav = document.getElementById('ue-selector');
            nav.innerHTML = Object.values(AREA_MAP).flat().map(id => 
                `<button class="btn ${id==currentUE?'active':''}" onclick="switchUE(${id})">UE ${id}</button>`
            ).join('');
        }

        function switchUE(id) {
            currentUE = id;
            renderNav();
            mainChart.data.labels = [];
            mainChart.data.datasets.forEach(d => d.data = []);
        }

        async function update() {
            try {
                const res = await fetch('/api/all_data');
                const allData = await res.json();
                let hasAlert = false;
                
                allData.forEach(d => {
                    const uid = d.id;
                    const nowLabel = new Date().toLocaleTimeString();

                    // 檢查全域警報 (只要有設備需要 ACK 就觸發)
                    if (d.needs_ack && !hasAlert) {
                        hasAlert = true;
                        currentAlertUid = uid;
                        document.getElementById('alert-overlay').style.display = 'flex';
                        document.getElementById('alert-msg').innerHTML = `設備 <b>UE ${uid}</b> 生理指標異常已持續超過 60 秒！<br>請立即介入處理。`;
                    }

                    // 緩衝區資料處理
                    if (!ueDataBuffers[uid]) ueDataBuffers[uid] = [];
                    ueDataBuffers[uid].push({ time: nowLabel, hr: d.heart, hrv: d.hrv, lvl: d.lvl });
                    if (ueDataBuffers[uid].length > 600) ueDataBuffers[uid].shift();

                    // 更新當前選定設備的 UI
                    if (uid === currentUE) {
                        document.getElementById('v-hr').innerText = d.heart.toFixed(1);
                        document.getElementById('v-hrv').innerText = d.hrv.toFixed(1);
                        document.getElementById('v-o2').innerText = d.spo2.toFixed(1);
                        document.getElementById('v-lvl').innerText = d.lvl;
                        document.getElementById('v-freq').innerText = (FREQ_MAP[d.lvl] || 4.0) + "s";

                        mainChart.data.labels.push(nowLabel);
                        mainChart.data.datasets[0].data.push(d.heart);
                        mainChart.data.datasets[1].data.push(d.hrv);
                        if (mainChart.data.labels.length > 40) {
                            mainChart.data.labels.shift();
                            mainChart.data.datasets.forEach(ds => ds.data.shift());
                        }
                        mainChart.update();
                    }

                    // 狀態變更歷史擷取 (全域設備)
                    const prevLvl = lastLevels[uid] || "Level 0";
                    if (d.lvl !== prevLvl) {
                        if (prevLvl === "Level 0" && d.lvl !== "Level 0") {
                            anomalyStartTimes[uid] = nowLabel;
                            setTimeout(() => captureSnapshot(uid, nowLabel, prevLvl, d.lvl, "start"), 3000);
                        } else if (d.lvl === "Level 0") {
                            const start = anomalyStartTimes[uid] || nowLabel;
                            setTimeout(() => captureSnapshot(uid, nowLabel, prevLvl, d.lvl, "recovery", start), 3000);
                        } else {
                            setTimeout(() => captureSnapshot(uid, nowLabel, prevLvl, d.lvl, "start"), 3000);
                        }
                        lastLevels[uid] = d.lvl;
                    }
                });

                // 若無設備需要警告，確保關閉視窗
                if (!hasAlert) {
                    document.getElementById('alert-overlay').style.display = 'none';
                }

            } catch(e) { console.error("Update failed:", e); }
        }

        async function acknowledgeLevel2() {
            if (!currentAlertUid) return;
            try {
                // 將 localhost 改為動態抓取當前網域的 window.location.hostname
                await fetch(`http://${window.location.hostname}:5002/api/ack_event?uid=${currentAlertUid}`, { method: 'POST' });
                document.getElementById('alert-overlay').style.display = 'none';
                currentAlertUid = null;
            } catch(e) {
                alert("無法連線至後端 API，請確認伺服器運作狀態。");
            }
        }

        function captureSnapshot(uid, eventTime, fromLvl, toLvl, mode, startTime = null) {
                    const buffer = ueDataBuffers[uid];
                    if (!buffer) return;
                    const eventIdx = buffer.findIndex(item => item.time === eventTime);
                    if (eventIdx === -1) return;

                    let snapshotData = [];
                    let tTitle = "", tIcon = "", bClass = "", tColor = "", desc = "";

                    if (toLvl === "Level 0") {
                        tTitle = "狀態恢復正常"; tIcon = "✅"; bClass = "border-success"; tColor = "#10b981";
                        desc = "系統自動歸檔：完整異常週期數據回溯";
                        const sIdx = buffer.findIndex(item => item.time === startTime);
                        const safeStart = sIdx !== -1 ? Math.max(0, sIdx - 5) : Math.max(0, eventIdx - 20);
                        snapshotData = buffer.slice(safeStart, Math.min(buffer.length, eventIdx + 5));
                    } else {
                        // 根據 Level 細分視覺與說明
                        if (toLvl === "Level 1") {
                            bClass = "border-info"; tColor = "#38bdf8"; tTitle = "異常徵兆持續"; tIcon = "ℹ️";
                            desc = "觸發條件：數據異常狀態已持續 15 秒";
                        } else if (toLvl === "Level 2") {
                            bClass = "border-warning"; tColor = "#fbbf24"; tTitle = "異常狀態惡化"; tIcon = "⚠️";
                            desc = "觸發條件：數據異常狀態已持續 60 秒";
                        } else if (toLvl === "Level 3") {
                            bClass = "border-danger-dark"; tColor = "#b91c1c"; tTitle = "高風險狀態 (活動喪失)"; tIcon = "🚨";
                            desc = "觸發條件：異常持續且完全靜止超過 15 秒";
                        } else if (toLvl === "Level 4") {
                            bClass = "border-danger-bright"; tColor = "#ef4444"; tTitle = "緊急危害觸發"; tIcon = "💥";
                            desc = "觸發條件：極端生理數值 (休克或缺氧邊緣)";
                        }

                        snapshotData = buffer.slice(Math.max(0, eventIdx - 10), Math.min(buffer.length, eventIdx + 10));
                    }

                    const cardId = `snap-${uid}-${Date.now()}`;
                    const html = `
                        <div class="event-card ${bClass}">
                            <div class="event-info">
                                <div class="ue-tag">設備 ID: ${uid}</div>
                                <div class="event-title" style="color: ${tColor}">${tIcon} ${tTitle} (Level ${fromLvl} → Level ${toLvl})</div>
                                <div class="event-meta" style="margin-bottom: 10px;">
                                    <b>發生時間：</b> ${eventTime}<br>
                                    <b>判讀依據：</b> ${desc}<br>
                                </div>
                                ${ (toLvl === 'Level 3' || toLvl === 'Level 4') ? `
                                <div style="display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap;">
                                    <button class="btn" style="background: #0081cb; font-size: 0.8em;" onclick="notifyInsurance(${uid}, '住院通知', '意外險', this)">📝 發布住院通知</button>
                                    <button class="btn" style="background: #10b981; font-size: 0.8em; display: none;" id="btn-diag-${cardId}" onclick="uploadReport(${uid}, 'DIAGNOSIS', '意外傷害診療報告', this)">📄 上傳診療報告</button>
                                    <button class="btn" style="background: #f59e0b; font-size: 0.8em; display: none;" id="btn-follow-${cardId}" onclick="uploadReport(${uid}, 'FOLLOWUP', '預計三個月復健計畫', this)">📅 上傳複診計畫</button>
                                </div>
                                ` : '' }
                            </div>
                            <div class="snapshot-grid">
                                <div class="snapshot-box"><span class="snapshot-label">心率歷史軌跡</span><canvas id="hr-${cardId}"></canvas></div>
                                <div class="snapshot-box"><span class="snapshot-label">HRV歷史軌跡</span><canvas id="hrv-${cardId}"></canvas></div>
                            </div>
                        </div>
                    `;
                    
                    document.getElementById('global-event-list').insertAdjacentHTML('afterbegin', html);
                    renderSmallChart(`hr-${cardId}`, snapshotData.map(s => s.hr), tColor, 40, 160); // 顏色與主標題同步
                    renderSmallChart(`hrv-${cardId}`, snapshotData.map(s => s.hrv), '#a855f7', 0, 80);
                }

        function renderSmallChart(id, data, color, min, max) {
            const ctx = document.getElementById(id);
            if (!ctx) return;
            new Chart(ctx, {
                type: 'line',
                data: { labels: new Array(data.length).fill(''), datasets: [{ borderColor: color, data: data, pointRadius: 2, fill: false, tension: 0.2 }] },
                options: { 
                    maintainAspectRatio: false, plugins: { legend: { display: false } },
                    scales: { x: { display: false }, y: { min: min, max: max, ticks: { display: false }, grid: { display: false } } }
                }
            });
        }
        
        let seenSettledClaims = new Set();
        async function fetchSettledClaims() {
            try {
                const res = await fetch(`http://${window.location.hostname}:5002/api/insurance/claims`);
                const claims = await res.json();
                const settledClaims = claims.filter(c => c.status === 'SETTLED');
                
                settledClaims.forEach(c => {
                    if (!seenSettledClaims.has(c.id)) {
                        seenSettledClaims.add(c.id);
                        
                        const html = `
                            <div class="event-card border-success" style="border-left-color: #10b981;">
                                <div class="event-info" style="grid-column: 1 / span 2;">
                                    <div class="ue-tag" style="background: #10b981;">設備 ID: ${c.uid}</div>
                                    <div style="font-weight: bold; color: #10b981; font-size: 1.2em; margin-bottom: 5px;">✅ 理賠結算完成 (保險中心)</div>
                                    <div style="font-size: 0.9em; color: #94a3b8; line-height: 1.6; background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 8px; margin-top: 10px;">
                                        <div style="display: flex; justify-content: space-between;"><span>理賠單號：</span><b>#CLM-${c.id}</b></div>
                                        <div style="display: flex; justify-content: space-between;"><span>險種類別：</span><b>${c.type}</b></div>
                                        <div style="display: flex; justify-content: space-between;"><span>結算時間：</span><b>${c.d_at}</b></div>
                                        <hr style="border: 0; border-top: 1px solid #334155; margin: 10px 0;">
                                        <div style="display: flex; justify-content: space-between;"><span>核准住院天數：</span><b>${c.days} 天</b></div>
                                        <div style="display: flex; justify-content: space-between; font-size: 1.2em; color: #10b981; margin-top: 5px;">
                                            <span>理賠總撥款：</span><b>$ ${c.amount.toLocaleString()}</b>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                        document.getElementById('global-event-list').insertAdjacentHTML('afterbegin', html);
                    }
                });
            } catch(e) {}
        }

        async function notifyInsurance(uid, noticeType, insType, btnElement) {
            btnElement.disabled = true;
            btnElement.innerText = "處理中...";
            try {
                const res = await fetch(`http://${window.location.hostname}:5002/api/insurance/hospitalize`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({uid: uid, type: insType})
                });
                const data = await res.json();
                if (data.status === 'success') {
                    btnElement.innerText = "✅ 已發布住院通知";
                    btnElement.style.background = "#475569";
                    
                    // 顯示上傳報告按鈕
                    const parent = btnElement.parentElement;
                    const diagBtn = parent.children[1];
                    const followBtn = parent.children[2];
                    diagBtn.style.display = "inline-block";
                    diagBtn.setAttribute("data-claim-id", data.claim_id);
                    followBtn.style.display = "inline-block";
                    followBtn.setAttribute("data-claim-id", data.claim_id);
                }
            } catch(e) {
                alert("通知保險端失敗：" + e);
                btnElement.disabled = false;
                btnElement.innerText = "📝 發布住院通知";
            }
        }

        async function uploadReport(uid, rtype, content, btnElement) {
            const claimId = btnElement.getAttribute("data-claim-id");
            btnElement.disabled = true;
            btnElement.innerText = "上傳中...";
            try {
                const res = await fetch(`http://${window.location.hostname}:5002/api/insurance/report`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({uid: uid, claim_id: claimId, report_type: rtype, content: content})
                });
                const data = await res.json();
                if (data.status === 'success') {
                    btnElement.innerText = `✅ 已上傳報告`;
                    btnElement.style.background = "#475569";
                }
            } catch(e) {
                alert("上傳報告失敗：" + e);
                btnElement.disabled = false;
                btnElement.innerText = "重新上傳";
            }
        }
        
        init();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, area_map=AREA_MAP, freq_map=FREQ_MAP)

@app.route('/api/all_data')
def get_all_data():
    if not os.path.exists(DB_PATH): return jsonify([])
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        # 新增抓取 needs_ack 欄位
        cur.execute('''
            SELECT device_id, risk_level, heart, hrv, spo2, temp, battery, needs_ack 
            FROM telemetry WHERE id IN (SELECT MAX(id) FROM telemetry GROUP BY device_id)
        ''')
        res = [{"id":r[0], "lvl":r[1], "heart":r[2], "hrv":r[3], "spo2":r[4], "temp":r[5], "bat":r[6], "needs_ack":bool(r[7])} for r in cur.fetchall()]
    except Exception as e:
        res = []
    finally:
        conn.close()
    return jsonify(res)

if __name__ == '__main__':
    # 監控中樞跑在 5000 port
    app.run(host='0.0.0.0', port=5000)