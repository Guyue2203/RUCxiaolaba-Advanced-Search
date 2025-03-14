#!/bin/bash
python3 /path/to/spider.py
# crontab中运行着下面的指令
# 5 3 * * * /path/to/run_spider.sh >> /path/to/spider.log 2>&1
