import sqlite3
import time
import os

def monitor_db():
    db_path = 'iot_data.db'
    while True:
        try:
            if not os.path.exists(db_path):
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"[{time.strftime('%H:%M:%S')}] 正在等待資料庫檔案生成...")
                time.sleep(2)
                continue

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 清除畫面
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 110)
            print(f"       📡 SIS IoT 邊緣監控系統 - 文字儀表板 (更新時間: {time.strftime('%H:%M:%S')})")
            print("=" * 110)

            # 1. 顯示設備統計
            try:
                cursor.execute('SELECT DISTINCT device_id, device_name FROM telemetry')
                devices = cursor.fetchall()
                for dev_id, dev_name in devices:
                    cursor.execute('''
                        SELECT COUNT(*), AVG(temp), AVG(heart), AVG(battery) 
                        FROM telemetry WHERE device_id = ?
                    ''', (dev_id,))
                    count, avg_t, avg_h, avg_b = cursor.fetchone()
                    print(f" 📱 {dev_name:<12} (ID:{dev_id:<3}) | 總筆數: {count:>5} | 平均體溫: {avg_t or 0:.2f} | 平均電量: {avg_b or 0:.2f}%")
            except sqlite3.OperationalError:
                print(" >> 欄位讀取中，請稍候...")

            print("-" * 110)
            print("最新 5 筆系統動態 (Real-time Raw Log):")
            print(f"{'狀態':<4} | {'ID':<4} | {'名稱':<12} | {'體溫':<6} | {'心跳':<5} | {'電量':<10} | {'速度':<10} | {'代碼':<6}")
            print("-" * 110)

            # 2. 顯示最新 5 筆
            try:
                cursor.execute('''
                    SELECT event_code, device_id, device_name, temp, heart, battery, speed, event_code 
                    FROM telemetry ORDER BY id DESC LIMIT 5
                ''')
                rows = cursor.fetchall()
                if not rows:
                    print(" >> 尚無數據傳入...")
                for r in rows:
                    icon = "✅" if r[0] == "N001" else "🚨"
                    bat_str = f"{r[5]:.2f}%" + (" ⚠️" if "B" in r[7] else "  ")
                    print(f" {icon:<2} | {r[1]:<4} | {r[2]:<12} | {r[3]:.2f} | {r[4]:.0f} | {bat_str:<10} | {r[6]:.2f} m/s | {r[7]:<6}")
            except Exception as e:
                print(f" >> 數據解析錯誤: {e}")

            conn.close()
        except KeyboardInterrupt:
            print("\n監控停止")
            break
        except Exception as e:
            print(f"系統錯誤: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    monitor_db()