import socket
import time
import struct
import random
import sys
import select
import termios
import tty
from datetime import datetime

# --- Linux 非阻塞按鍵偵測 ---
def get_key(fd):
    rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
    if rlist:
        return sys.stdin.read(1)
    return None

def get_feedback(sock, timeout=0.2):
    try:
        sock.settimeout(timeout) 
        data, _ = sock.recvfrom(1024)
        lvl_bytes, interval, report_bytes = struct.unpack('!10sf256s', data)
        lvl_str = lvl_bytes.decode('utf-8').strip('\x00')
        return lvl_str, interval
    except Exception:
        return None, None

def start_single_ue_simulation(server_ip='127.0.0.1', server_port=12345):
    PACKET_FORMAT = '!idffffffff10s'
    device_id = 101
    
    current_interval = 10.0  
    current_lvl = "Level 0"
    target_lvl_key = '0' 
    current_speed = 1.5 

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    print("=" * 80)
    print(f"📡 SIS 終端模擬器 (ID: {device_id}) - 進階情境模擬")
    print(" [0] 正常活動")
    print(" [1] 異常波動 (觸發 L1 / L2)")
    print(" [2] 活動力喪失 (速率衰減 -> 0，觸發 L3)")
    print(" [3] 極端惡化 (休克邊緣，觸發 L4)")
    print(" [Ctrl+C] 退出")
    print("=" * 80)

    try:
        tty.setcbreak(fd)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            while True:
                # 1. 偵測按鍵
                key = get_key(fd)
                if key and key in ['0', '1', '2', '3']:
                    target_lvl_key = key
                    mode_map = {'0': "正常", '1': "異常波動", '2': "活動力喪失", '3': "極端惡化"}
                    print(f"\n[指令] 切換情境為: {mode_map[key]} (按鍵 {key})")
                    
                    # 若切換回正常，重置速率
                    if key == '0':
                        current_speed = 1.5

                # 2. 產生生理與動態數據
                if target_lvl_key == '0':
                    h, hv, o2 = random.uniform(70, 80), random.uniform(50, 60), random.uniform(97, 99)
                    current_speed = max(1.0, current_speed + random.uniform(-0.1, 0.1)) # 隨機走動
                
                elif target_lvl_key == '1':
                    h, hv, o2 = random.uniform(105, 115), random.uniform(25, 33), random.uniform(95, 96.5)
                    current_speed = max(0.5, current_speed - 0.05) # 稍微變慢
                
                elif target_lvl_key == '2':
                    # 生理異常且持續
                    h, hv, o2 = random.uniform(115, 125), random.uniform(15, 25), random.uniform(92, 94.5)
                    # 速率大幅衰減，模擬倒地或無法行動 (每秒減損速度約 0.05，視 interval 而定，約 30 秒歸零)
                    current_speed = max(0.0, current_speed - (0.05 * (4.0 / current_interval)))
                
                elif target_lvl_key == '3':
                    # 極端數據，不論時間長短，直接觸發 L4
                    h, hv, o2 = random.uniform(145, 160), random.uniform(5, 10), random.uniform(85, 88)
                    current_speed = 0.0 # 絕對靜止

                h, hv, o2 = max(30, min(200, h)), max(5, hv), max(70, min(100, o2))
                
                # 打包加密
                packed = struct.pack(PACKET_FORMAT, device_id, time.time(), 36.5, 
                                   h, hv, o2, current_speed, 0.0, 0.0, 100.0, current_lvl.encode('utf-8'))
                raw_data = bytes([b ^ 0xAA for b in packed])
                s.sendto(raw_data, (server_ip, server_port))
                
                # 接收反饋
                new_lvl, new_interval = get_feedback(s, timeout=0.2)
                if new_lvl and (new_lvl != current_lvl):
                    current_lvl = new_lvl
                    current_interval = new_interval
                    print(f"\n[同步] 系統狀態已升級至：{current_lvl} (頻率: {current_interval}s)")

                # 終端顯示更新 (加入 Spd 顯示)
                ts = datetime.now().strftime("%H:%M:%S")
                sys.stdout.write(
                    f"\r[{ts}] 模式:{target_lvl_key} | {current_lvl:<8} | HR:{h:>5.1f} | SpO2:{o2:>4.1f}% | Spd:{current_speed:>4.2f}m/s | 頻率:{current_interval}s "
                )
                sys.stdout.flush()
                
                time.sleep(max(0, current_interval - 0.22))

    except KeyboardInterrupt:
        print("\n\n[INFO] 模擬器已關閉。")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    start_single_ue_simulation()