from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>保險業務與理賠管理中心</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; border-bottom: 2px solid #334155; padding-bottom: 15px; margin-bottom: 20px; }
        .panel { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; margin-bottom: 20px; }
        .card { background: #0f172a; border-radius: 8px; padding: 15px; margin-top: 10px; border-left: 4px solid #3b82f6; }
        .card.active-claim { border-left-color: #ef4444; }
        .card.settled-claim { border-left-color: #10b981; }
        .card.pending-policy { border-left-color: #f59e0b; }
        .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-weight: bold; color: white; transition: 0.2s; }
        .btn-green { background: #10b981; } .btn-green:hover { background: #059669; }
        .btn-blue { background: #3b82f6; } .btn-blue:hover { background: #2563eb; }
        .btn-red { background: #ef4444; } .btn-red:hover { background: #dc2626; }
        .tag { padding: 3px 8px; border-radius: 4px; font-size: 0.8em; margin-right: 5px; }
        .tag-notice { background: rgba(56,189,248,0.2); color: #38bdf8; }
        .tag-diag { background: rgba(16,185,129,0.2); color: #10b981; }
        .tag-follow { background: rgba(245,158,11,0.2); color: #f59e0b; }
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin:0;">🏦 SIS 保險業務與理賠核心系統</h1>
        <div style="font-size: 0.9em; color: #94a3b8;">Edge API 連線狀態: <span style="color:#10b981;">● 正常</span></div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <!-- 理賠處置區 -->
        <div class="panel">
            <h2 style="margin-top:0; color: #38bdf8;">🏥 住院理賠與事故處置</h2>
            <div id="claims-list">載入中...</div>
        </div>

        <!-- 保單核發與品質回饋區 -->
        <div class="panel">
            <h2 style="margin-top:0; color: #f59e0b;">🛡️ 申購核險與保單管理</h2>
            <div id="policies-list">載入中...</div>
        </div>
    </div>

    <!-- 電子核算單彈窗 (隱藏) -->
    <div id="receipt-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); align-items:center; justify-content:center; z-index:100;">
        <div style="background: white; color: black; padding: 30px; border-radius: 12px; width: 400px; box-shadow: 0 0 20px rgba(0,0,0,0.5);">
            <h2 style="text-align: center; border-bottom: 2px dashed #ccc; padding-bottom: 10px;">📋 電子理賠核算單</h2>
            <div id="receipt-content" style="line-height: 1.8; margin-top: 20px;"></div>
            <button class="btn btn-blue" style="width: 100%; margin-top: 20px;" onclick="document.getElementById('receipt-overlay').style.display='none'">確認並關閉</button>
        </div>
    </div>

    <script>
        const API_BASE = `http://${window.location.hostname}:5002/api/insurance`;
        
        let claimsData = [];
        let hospitalTimers = {}; // Record simulated hospital days

        async function fetchAll() {
            try {
                const [claimsRes, policiesRes] = await Promise.all([
                    fetch(`${API_BASE}/claims`), fetch(`${API_BASE}/policies`)
                ]);
                claimsData = await claimsRes.json();
                const policies = await policiesRes.json();
                renderClaims(claimsData);
                renderPolicies(policies);
            } catch(e) { console.error("API error", e); }
        }

        function renderClaims(claims) {
            const list = document.getElementById('claims-list');
            if(claims.length === 0) return list.innerHTML = "<div style='color:#94a3b8;'>目前無待處理理賠案件。</div>";
            
            let html = '';
            claims.forEach(c => {
                let statusClass = c.status === 'HOSPITALIZED' ? 'active-claim' : 'settled-claim';
                
                // Demo住院天數模擬：從收到住院通知開始算，每5秒算一天
                if (c.status === 'HOSPITALIZED') {
                    if (!hospitalTimers[c.id]) {
                        const start = new Date(c.h_at).getTime();
                        hospitalTimers[c.id] = { start: start, currentDays: 0 };
                    }
                    hospitalTimers[c.id].currentDays += 1; // 每次刷新+1天展示用
                }

                let daysStr = c.status === 'HOSPITALIZED' ? hospitalTimers[c.id].currentDays : c.days;
                let dailyRate = c.type === '意外險' ? 2000 : 1000; // 假設意外險日額
                let currentAmount = daysStr * dailyRate;

                // 收集已上傳的醫療報告
                let reportsHtml = '';
                let hasNotice = false, hasDiag = false, hasFollow = false;
                if(c.reports) {
                    c.reports.forEach(r => {
                        let tClass = 'tag-notice'; let tName = '通知';
                        if(r.type === 'DIAGNOSIS') { tClass = 'tag-diag'; tName = '診療報告'; hasDiag = true; }
                        if(r.type === 'FOLLOWUP') { tClass = 'tag-follow'; tName = '複診計畫'; hasFollow = true; }
                        if(r.type === 'NOTICE') hasNotice = true;
                        reportsHtml += `<div style="margin-top: 5px; font-size: 0.9em; color: #cbd5e1;"><span class="tag ${tClass}">${tName}</span> ${r.content}</div>`;
                    });
                }
                
                let actionHtml = '';
                if (c.status === 'HOSPITALIZED') {
                    const canSettle = hasDiag && hasFollow;
                    actionHtml = `
                        <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #334155; padding-top: 10px;">
                            <span style="color: #cbd5e1;">模擬住院天數: <b style="color: #ef4444; font-size: 1.2em;">${daysStr}</b> 天 (日額: $${dailyRate})</span>
                            <button class="btn btn-red" ${!canSettle ? 'title="需等待醫院上傳診療與複診報告" style="opacity: 0.5;"' : ''} 
                                onclick="${canSettle ? `dischargeClaim(${c.id}, ${c.uid}, ${daysStr}, ${currentAmount}, '${c.type}')` : 'alert(\\'尚未收到完整的醫療報告，無法進行出院結算核險。\\')'}">
                                ${canSettle ? '✅ 核准並出院結算' : '⏳ 等待醫療報告...'}
                            </button>
                        </div>
                    `;
                } else {
                    actionHtml = `
                        <div style="margin-top: 10px; color: #10b981; font-weight: bold;">
                            已結案。理賠天數: ${c.days} 天，總理賠金: $${c.amount.toLocaleString()}
                        </div>
                    `;
                }

                html += `
                    <div class="card ${statusClass}">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <b style="font-size: 1.1em;">UE ${c.uid} - ${c.type} (#${c.id})</b>
                            <span style="color: ${c.status === 'HOSPITALIZED' ? '#ef4444' : '#10b981'}; font-weight: bold;">
                                ${c.status === 'HOSPITALIZED' ? '住院中 (理賠累計中)' : '已出險結帳'}
                            </span>
                        </div>
                        <div style="font-size: 0.9em; color: #94a3b8;">立案時間: ${c.h_at}</div>
                        <div style="margin-top: 10px; background: #1e293b; padding: 10px; border-radius: 6px;">
                            <div style="font-weight: bold; margin-bottom: 5px;">📜 收件紀錄：</div>
                            ${reportsHtml || '<span style="color: #64748b;">無紀錄</span>'}
                        </div>
                        ${actionHtml}
                    </div>
                `;
            });
            list.innerHTML = html;
        }

        function renderPolicies(policies) {
            const list = document.getElementById('policies-list');
            if(policies.length === 0) return list.innerHTML = "<div style='color:#94a3b8;'>目前無保單申請。</div>";
            
            let html = '';
            policies.forEach(p => {
                let statusClass = p.status === 'PENDING' ? 'pending-policy' : 'settled-claim';
                
                let actionHtml = '';
                if (p.status === 'PENDING') {
                    actionHtml = `<button class="btn btn-green" style="margin-top: 10px;" onclick="approvePolicy(${p.id})">✅ 核准保單</button>`;
                } else {
                    actionHtml = `<button class="btn btn-blue" style="margin-top: 10px;" onclick="sendFeedback(${p.id})">💡 發送次年費率調整與建議</button>`;
                }

                let reportHtml = '';
                if (p.report) {
                    try {
                        let repObj = JSON.parse(p.report);
                        let chartId = 'chart-policy-' + p.id;
                        reportHtml = `
                            <div style="margin-top: 10px; background: #1e293b; padding: 10px; border-radius: 6px;">
                                <div style="color: #cbd5e1; font-size: 0.9em; white-space: pre-wrap;">${repObj.text}</div>
                                <div style="height: 120px; margin-top: 10px;">
                                    <canvas id="${chartId}"></canvas>
                                </div>
                            </div>
                        `;
                        setTimeout(() => {
                            let ctx = document.getElementById(chartId);
                            if (ctx) {
                                new Chart(ctx, {
                                    type: 'line',
                                    data: {
                                        labels: repObj.labels,
                                        datasets: [
                                            { label: 'HR', borderColor: '#ef4444', data: repObj.hr, pointRadius: 0, tension: 0.3, borderWidth: 2 },
                                            { label: 'HRV', borderColor: '#a855f7', data: repObj.hrv, pointRadius: 0, tension: 0.3, borderWidth: 2 }
                                        ]
                                    },
                                    options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { min: 20, max: 160, display: false } } }
                                });
                            }
                        }, 200);
                    } catch(e) {
                        reportHtml = `<div style="margin-top: 10px; color: #cbd5e1; font-size: 0.9em; white-space: pre-wrap;">${p.report}</div>`;
                    }
                }

                html += `
                    <div class="card ${statusClass}">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <b style="font-size: 1.1em;">UE ${p.uid} - ${p.type} (#${p.id})</b>
                            <span style="color: ${p.status === 'PENDING' ? '#f59e0b' : '#10b981'}; font-weight: bold;">
                                ${p.status === 'PENDING' ? '審核中' : '生效中'}
                            </span>
                        </div>
                        <div style="font-size: 0.9em; color: #94a3b8;">申請時間: ${p.created_at}</div>
                        ${reportHtml}
                        ${actionHtml}
                    </div>
                `;
            });
            list.innerHTML = html;
        }

        async function dischargeClaim(claimId, uid, days, amount, type) {
            try {
                await fetch(`${API_BASE}/discharge`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({claim_id: claimId, days: days, amount: amount})
                });
                
                // Show Receipt Overlay
                const d = new Date().toLocaleString();
                document.getElementById('receipt-content').innerHTML = `
                    <div style="display: flex; justify-content: space-between;"><span>理賠單號：</span><b>#CLM-${claimId}</b></div>
                    <div style="display: flex; justify-content: space-between;"><span>受保人編號：</span><b>UE ${uid}</b></div>
                    <div style="display: flex; justify-content: space-between;"><span>險種類別：</span><b>${type}</b></div>
                    <div style="display: flex; justify-content: space-between;"><span>結算時間：</span><b>${d}</b></div>
                    <hr>
                    <div style="display: flex; justify-content: space-between;"><span>實際住院天數：</span><b>${days} 天</b></div>
                    <div style="display: flex; justify-content: space-between; font-size: 1.2em; color: #ef4444; margin-top: 10px;">
                        <span>核算理賠總額：</span><b>$ ${amount.toLocaleString()}</b>
                    </div>
                `;
                document.getElementById('receipt-overlay').style.display = 'flex';
                
                fetchAll();
            } catch(e) { alert("結算失敗"); }
        }

        async function approvePolicy(policyId) {
            try {
                await fetch(`${API_BASE}/quality`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({policy_id: policyId, status: 'ACTIVE', feedback: '您好，您的長期健康險已核保通過。'})
                });
                fetchAll();
            } catch(e) { alert("核准失敗"); }
        }

        async function sendFeedback(policyId) {
            let feedback = prompt("請輸入給客戶的定期品質報告與費率建議：", "根據您的長期數據，您的生理狀況優良！次年保費將給予 5% 費率折扣。");
            if (!feedback) return;
            try {
                await fetch(`${API_BASE}/quality`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({policy_id: policyId, status: 'ACTIVE', feedback: feedback})
                });
                alert("已發送回饋！");
                fetchAll();
            } catch(e) { alert("發送失敗"); }
        }

        setInterval(fetchAll, 3000);
        fetchAll();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)
