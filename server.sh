#!/bin/bash
while true; do
    python3 /path/to/app.py
    echo "app.py 终止，正在重新启动..."  
    sleep 10  # 可选，防止过快重启
done
