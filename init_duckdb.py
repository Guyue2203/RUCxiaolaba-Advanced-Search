import duckdb
import os
from collections import deque
import re
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def initialize_duckdb():
    """初始化DuckDB数据库，将CSV数据导入到持久化数据库中"""
    db_path = './data/all.duckdb'
    csv_path = './data/all.csv'
    if not os.path.exists(db_path):
        conn = duckdb.connect(db_path)
        # 添加时间字段处理
        conn.execute(f"""
            CREATE TABLE df AS 
            SELECT *,
                substr(post_code,1,4) || '-' || substr(post_code,5,2) || '-' || substr(post_code,7,2) as post_time 
            FROM read_csv('{csv_path}')
        """)
        conn.close()
        print("duckdb init complete")

initialize_duckdb()  # 应用启动时初始化数据库