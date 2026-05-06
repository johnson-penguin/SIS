import socket, time, struct, random, base64

def start_multi_ue_simulation(server_ip='127.0.0.1', server_port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        devices = [
            {"id": 101, "type": "XOR", "area": "Area_A"},
            {"id": 201, "type": "B64", "area": "Area_B"}
        ]
        
        # 封包格式: i(ID), d(Time), 8個 f (T, H, HRV, S, Speed, Head, Dist, Bat)
        PACKET_FORMAT = '!idffffffff'

        while True:
            for dev in devices:
                uid = dev["id"]
                curr_time = time.time()
                
                # 模擬數據
                temp = round(random.uniform(36.0, 38.5), 2)
                heart = round(random.uniform(60.0, 110.0), 2)
                hrv = round(random.uniform(20.0, 60.0), 2)  # 新增 HRV
                spo2 = round(random.uniform(93.0, 100.0), 2)
                speed = round(random.uniform(0, 5.0), 2)
                
                packed = struct.pack(PACKET_FORMAT, uid, curr_time, temp, heart, hrv, spo2, speed, 0.0, 0.0, 100.0)
                
                if dev["type"] == "XOR":
                    raw_data = bytes([b ^ 0xAA for b in packed])
                else:
                    raw_data = base64.b64encode(bytes([(b + 3) % 256 for b in packed]))
                
                s.sendto(raw_data, (server_ip, server_port))
                time.sleep(0.1)
            time.sleep(1) # 依照 Level 0 初始頻率
            
if __name__ == "__main__":
    start_multi_ue_simulation()