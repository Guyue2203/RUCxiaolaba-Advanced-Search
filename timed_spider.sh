python3 /home/re/desktop/web/spider.py
rm /home/re/desktop/web/data/all.duckdb
python3 /home/re/desktop/web/init_duckdb.py
# crontab中运行着下面的指令
# 5 3 * * * /path/to/run_spider.sh >> /path/to/spider.log 2>&1
