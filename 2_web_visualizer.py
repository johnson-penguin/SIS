from flask import Flask, render_template_string, jsonify
import sqlite3
import os

app = Flask(__name__)

# 資料庫路徑設定
DB_PATH = os.path.join(os.getcwd(), 'iot_data.db')

# HTML/JavaScript 儀表板模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>SIS 智能監測控制台</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', "Microsoft JhengHei", sans-serif; background: #0b0e14; color: #cfd8dc; margin: 0; padding: 20px; }
        
        /* 導覽列 */
        .header { border-bottom: 1px solid #263238; padding-bottom: 15px; margin-bottom: 20px; }
        .nav { display: flex; gap: 10px; margin-bottom: 15px; }
        .btn { padding: 8px 18px; background: #1c2331; border: 1px solid #37474f; color: #fff; cursor: pointer; border-radius: 4px; transition: 0.3s; }
        .btn:hover { background: #263238; }
        .btn.active { background: #0081cb; border-color: #0081cb; font-weight: bold; }

        /* 主佈局：左側詳解圖表，右側歷史紀錄 */
        .detail-view { display: grid; grid-template-columns: 1.6fr 1fr; gap: 20px; }
        .card { background: #161c27; border-radius: 12px; padding: 20px; border: 1px solid #263238; }

        /* 中間動態資訊格 (中文顯示) */
        .info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .data-box { background: #1c2331; padding: 15px; border-radius: 8px; text-align: center; border-bottom: 4px solid #00d4ff; }
        .data-box .label { font-size: 0.9em; color: #90a4ae; margin-bottom: 5px; }
        .data-box .val { font-size: 1.5em; font-weight: bold; color: #fff; }
        
        .bat-low { color: #ff5252 !important; animation: blink 1s infinite; }
        @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

        /* 異常歷史清單：左側數值，右側標籤 */
        .hist-list { height: 480px; overflow-y: auto; font-family: sans-serif; }
        .item { 
            padding: 12px; 
            border-bottom: 1px solid #263238; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .item-left { display: flex; flex-direction: column; gap: 4px; }
        .item-left .time { color: #90a4ae; font-size: 0.75em; font-family: monospace; }
        .item-left .data-values { color: #00d4ff; font-size: 0.95em; font-weight: 500; }
        
        .tag { 
            padding: 4px 12px; 
            border-radius: 6px; 
            font-weight: bold; 
            color: white; 
            font-size: 0.85em; 
            min-width: 90px;
            text-align: center;
        }
        .tag-warning { background: #f57c00; } /* 橘色：一般異常 */
        .tag-danger { background: #c62828; }  /* 紅色：嚴重或低電量 */

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #37474f; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 SIS 智能監測控制台</h1>
        <div class="nav">
            <button class="btn active" id="btn-Area_A" onclick="switchArea('Area_A')">📍 區域 A</button>
            <button class="btn" id="btn-Area_B" onclick="switchArea('Area_B')">📍 區域 B</button>
        </div>
        <div class="nav" id="ue-btns"></div>
    </div>

    <div class="detail-view">
        <div class="card">
            <h2 id="ue-title">UE 即時詳解</h2>
            <div class="info-grid">
                <div class="data-box"><div class="label">運動速度</div><div class="val" id="v-speed">0.00</div> m/s</div>
                <div class="data-box"><div class="label">位移方向</div><div class="val" id="v-head">0.00</div> °</div>
                <div class="data-box"><div class="label">累計距離</div><div class="val" id="v-dist">0.00</div> m</div>
                <div class="data-box"><div class="label">電池電量</div><div class="val" id="v-bat">100.00</div> %</div>
            </div>
            <canvas id="main-chart"></canvas>
        </div>

        <div class="card">
            <h2>⚠️ 異常事件歷史</h2>
            <div class="hist-list" id="hist-list">等待數據傳入...</div>
        </div>
    </div>

    <script>
        const AREA_MAP = { "Area_A": [101, 102], "Area_B": [201, 202, 203] };
        const SEMANTIC_INFO = {
            'T': { name: '體溫異常', level: 'warning' },
            'H': { name: '心跳過快', level: 'warning' },
            'S': { name: '血氧不足', level: 'warning' },
            'V': { name: '速度過快', level: 'warning' },
            'B': { name: '電量偏低', level: 'danger' }
        };

        let currentArea = 'Area_A', currentUE = 101, mainChart = null;

        // 語義代碼轉換與 UI 判斷
        function getEventUI(code) {
            if (code === "N001") return null;
            let raw = code.replace("E_", "");
            let names = [];
            let isDanger = false;
            for (let char of raw) {
                if (SEMANTIC_INFO[char]) {
                    names.push(SEMANTIC_INFO[char].name);
                    if (SEMANTIC_INFO[char].level === 'danger') isDanger = true;
                }
            }
            return {
                text: names.join(" + "),
                css: isDanger ? 'tag-danger' : 'tag-warning'
            };
        }

        function switchArea(a) {
            currentArea = a;
            document.querySelectorAll('.btn').forEach(b => {
                if(b.id === `btn-${a}`) b.classList.add('active');
                else if(b.id.startsWith('btn-Area')) b.classList.remove('active');
            });
            renderUEButtons();
            switchUE(AREA_MAP[a][0]);
        }

        function renderUEButtons() {
            const container = document.getElementById('ue-btns');
            container.innerHTML = AREA_MAP[currentArea].map(id => 
                `<button class="btn ${id==currentUE?'active':''}" onclick="switchUE(${id})">UE ${id}</button>`
            ).join('');
        }

        function switchUE(id) {
            currentUE = id;
            document.getElementById('ue-title').innerText = `UE ${id} 物理與生理監控數據`;
            renderUEButtons();
            initChart();
            updateHistory();
        }

        function initChart() {
            if(mainChart) mainChart.destroy();
            const ctx = document.getElementById('main-chart').getContext('2d');
            mainChart = new Chart(ctx, {
                type: 'line',
                data: { labels: [], datasets: [
                    { label: '體溫 (°C)', data: [], borderColor: '#ff5252', tension: 0.3, pointRadius: 0 },
                    { label: '心跳 (bpm)', data: [], borderColor: '#448aff', tension: 0.3, pointRadius: 0 },
                    { label: '血氧 (%)', data: [], borderColor: '#00e676', tension: 0.3, pointRadius: 0 }
                ]},
                options: { animation: false, scales: { y: { min: 30, max: 130 } }, responsive: true }
            });
        }

        async function tick() {
            if(!currentUE) return;
            try {
                const res = await fetch('/api/data');
                const data = await res.json();
                const d = data.find(x => x.id == currentUE);
                if(d) {
                    document.getElementById('v-speed').innerText = d.speed.toFixed(2);
                    document.getElementById('v-head').innerText = d.heading.toFixed(2);
                    document.getElementById('v-dist').innerText = d.distance.toFixed(2);
                    const batEl = document.getElementById('v-bat');
                    batEl.innerText = d.battery.toFixed(2);
                    batEl.className = d.battery < 50.0 ? 'val bat-low' : 'val';

                    const now = new Date().toLocaleTimeString();
                    mainChart.data.labels.push(now);
                    mainChart.data.datasets[0].data.push(d.temp);
                    mainChart.data.datasets[1].data.push(d.heart);
                    mainChart.data.datasets[2].data.push(d.spo2);
                    if(mainChart.data.labels.length > 25) {
                        mainChart.data.labels.shift();
                        mainChart.data.datasets.forEach(ds => ds.data.shift());
                    }
                    mainChart.update();
                }
            } catch(e) {}
        }

        async function updateHistory() {
            if(!currentUE) return;
            try {
                const res = await fetch(`/api/history/${currentUE}`);
                const logs = await res.json();
                document.getElementById('hist-list').innerHTML = logs.map(l => {
                    const ui = getEventUI(l.code);
                    if(!ui) return '';
                    return `
                        <div class="item">
                            <div class="item-left">
                                <span class="time">${l.time}</span>
                                <span class="data-values">T: ${l.temp.toFixed(2)}°C | Bat: ${l.bat.toFixed(2)}%</span>
                            </div>
                            <div class="item-right">
                                <span class="tag ${ui.css}">${ui.text}</span>
                            </div>
                        </div>
                    `;
                }).join('');
            } catch(e) {}
        }

        switchArea('Area_A');
        setInterval(tick, 1000);
        setInterval(updateHistory, 3000);
    </script>
</body>
</html>
"""

# --- Flask 後端路由 ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def get_data():
    if not os.path.exists(DB_PATH): return jsonify([])
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        # 獲取所有設備最新的一筆資料
        cur.execute('''
            SELECT device_id, temp, heart, spo2, speed, heading, distance, battery, event_code 
            FROM telemetry WHERE id IN (SELECT MAX(id) FROM telemetry GROUP BY device_id)
        ''')
        res = [{"id":r[0], "temp":r[1], "heart":r[2], "spo2":r[3], "speed":r[4], "heading":r[5], "distance":r[6], "battery":r[7], "event":r[8]} for r in cur.fetchall()]
    except: res = []
    finally: conn.close()
    return jsonify(res)

@app.route('/api/history/<int:uid>')
def get_history(uid):
    if not os.path.exists(DB_PATH): return jsonify([])
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        # 獲取異常紀錄 (排除正常 N001)
        cur.execute('''
            SELECT server_received_at, event_code, temp, battery 
            FROM telemetry WHERE device_id=? AND event_code != "N001" 
            ORDER BY id DESC LIMIT 25
        ''', (uid,))
        res = [{"time":r[0].split()[1], "code":r[1], "temp":r[2], "bat":r[3]} for r in cur.fetchall()]
    except: res = []
    finally: conn.close()
    return jsonify(res)

if __name__ == '__main__':
    # 啟動網頁伺服器
    app.run(host='0.0.0.0', port=5000)