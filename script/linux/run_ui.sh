#!/bin/bash

cd "$(dirname "$0")"

echo "Starting UIs..."

python3 2_web_monitoring_station.py &
PID1=$!

python3 2_web_ue.py &
PID2=$!

python3 3_party_ui.py &
PID3=$!

python3 4_insurance_ui.py &
PID4=$!

echo "=========================================================="
echo "2_web_monitoring_station.py runs on http://localhost:5000 (PID: $PID1)"
echo "2_web_ue.py                 runs on http://localhost:5001 (PID: $PID2)"
echo "3_party_ui.py               runs on http://localhost:5003 (PID: $PID3)"
echo "4_insurance_ui.py           runs on http://localhost:5004 (PID: $PID4)"
echo "=========================================================="
echo "Press Ctrl+C to stop all."

# 捕捉 Ctrl+C (SIGINT) 信號，自動終止所有背景程式
trap "echo -e '\nStopping all UIs...'; kill $PID1 $PID2 $PID3 $PID4 2>/dev/null; exit" SIGINT

# 等待所有背景程序
wait
