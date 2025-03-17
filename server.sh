#!/bin/bash
while true; do
    gunicorn -w 2 -b 0.0.0.0:8080 --access-logfile access.log app:app --timeout 60 
	# python3 ./app.py
    # echo "app.py 终止，正在重新启动..."  
    sleep 10  # 可选，防止过快重启
done
