import duckdb
from openai import OpenAI
from dashscope import Application
from http import HTTPStatus
import os
import json
import pandas as pd
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

initialize_duckdb()  # 应用启动时初始化数据库
def filter_dataframe(keywords_list):
    # ...前面代码保持不变...
#     """使用DuckDB进行高效数据过滤"""
    if not keywords_list or not all(keywords_list):
        return pd.DataFrame()

    conn = duckdb.connect('./data/all.duckdb', read_only=True)
    try:
        # 构建动态查询条件
        conditions = []
        params = []
        for keyword in keywords_list:
            conditions.append("content LIKE ?")
            params.append(f"%{keyword}%")
        where_clause = " AND ".join(conditions) if conditions else "1=0"
        
        query = f"""
            WITH filtered_groups AS (
                SELECT COALESCE(Root_code, post_code) AS group_id
                FROM df
                WHERE {where_clause}
                GROUP BY group_id
            )
            SELECT *,
                post_code  
            FROM df
            WHERE COALESCE(Root_code, post_code) IN (SELECT group_id FROM filtered_groups)
        """
        return conn.execute(query, params).fetchdf()
    finally:
        conn.close()
def convert_df_to_forum(temp_df, keywords_list):
    """使用DuckDB高效构建论坛数据结构"""
    if temp_df.empty:
        final={}
        final["type"]="exact"
        posts = []
        posts.append({
            "id": 0,
            "content": "没有找到相关信息",
            "comments": []
        })
        final["results"]={"posts": posts}
        return {"posts": []}

    conn = duckdb.connect()
    try:
        conn.register('temp_df', temp_df)
        query = """
            WITH main_posts AS (
                SELECT 
                    id,
                    content,
                    post_code,
                    post_code
                FROM temp_df WHERE Root_code IS NULL
            ),
            comments AS (
                SELECT 
                    id,
                    content,
                    post_code,
                    Root_code
                FROM temp_df WHERE Root_code IS NOT NULL
            )
            SELECT 
                main.id,
                main.content,
                main.post_code,
                COALESCE((
                    SELECT json_group_array(json_object(
                        'id', c.id, 
                        'content', c.content,
                        'post_code', c.post_code
                    ))
                    FROM comments c 
                    WHERE c.Root_code = main.post_code
                ), '[]') AS comments
            FROM main_posts main
        """
        result = conn.execute(query).fetchall()
        # 高亮处理逻辑
        def highlight_keywords(text):
            for keyword in keywords_list:
                if keyword:
                    text = text.replace(keyword, f'<mark>{keyword}</mark>')
            return text

        posts = []
        for row in result:
            highlighted_content = highlight_keywords(row[1])
            comments = json.loads(row[3]) if row[3] else []
            
            highlighted_comments = []
            for comment in comments:
                comment['content'] = highlight_keywords(comment['content'])
                highlighted_comments.append(comment)
            
            posts.append({
                "id": row[0],
                "content": highlighted_content,
                "post_time": row[2],
                "comments": highlighted_comments,
                "comment_count": len(highlighted_comments)  # 添加评论数用于排序
            })

        # 添加默认按时间排序
        posts.sort(key=lambda x: x['post_time'], reverse=True)
        final={}
        final["type"]="exact"
        final["results"] = {"posts": posts}
        return final
    finally:
        conn.close()


def truncate_dataframe(df: pd.DataFrame, max_size: int) -> pd.DataFrame:
    """截断DataFrame（保留Pandas处理小数据集）"""
    # 原有实现保持不变，因处理的是过滤后的小数据
    total_size = df.memory_usage(deep=True).sum()
    if total_size <= max_size:
        return df
    
    truncated_df = df.iloc[:1].copy()
    for i in range(1, len(df)):
        new_size = truncated_df.memory_usage(deep=True).sum() + df.iloc[i:i+1].memory_usage(deep=True).sum()
        if new_size > max_size:
            break
        truncated_df = pd.concat([truncated_df, df.iloc[i:i+1]], ignore_index=True)
    return truncated_df

def AI_search(query):
    """AI搜索处理逻辑（保持原有结构，适配DuckDB）"""
    # 原有AI处理逻辑保持不变...
    # 示例核心处理部分：
    os.environ['DASHSCOPE_HTTP_BASE_URL'] = 'https://dashscope.aliyuncs.com/api/v1/'
    print("msg sent")
    stage1='''
    你现在需要帮助一名中国人民大学的学生用户解决问题，用户需要从一个文字论坛中过滤出他所需要的信息。
    接下来他会给出一个要求，请你根据这个要求给出一些相关的关键词，最终只返回一个元素为列表的列表，其中每个元素列表包含一些关键词。
    关键词的选取原则是：如果当若干个关键词同时出现时代表了该文本可能包含用户所需要的信息，那么就将这些关键词作为关键词列表的一个元素。请返回尽可能多的列表
    
    如果用户的信息不是一个请求，或者你认为用户的信息和论坛可能的信息无关，那么请返回一个空列表。
    
    例如用户信息为：请帮我总结一下统计学院的保研率相关信息
    那么你可以返回[['统计学院', '保研率'],['统院','保研率'],['统院','保研'],['统计学院','推免'],['统院','推免']]
    
    用户信息：
    '''
    stage1+=query
    response = Application.call(
        # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
        api_key='',
        app_id='c3cc0a7b365d4b2da7cb88ebd1aef1a0',# 替换为实际的应用 ID
        prompt=stage1)
    if response.status_code != HTTPStatus.OK:
        print(f'request_id={response.request_id}')
        print(f'code={response.status_code}')
        print(f'message={response.message}')
        print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
    print(response.output.text)
    try:
        keywd_list=eval(response.output.text)
    except:
        keywd_list=[]
    if keywd_list==[]:
        return "出错啦！可能是因为您的输入不是一个请求或者AI出现了幻觉，请重新搜索"
    
    target_df = filter_dataframe(keywd_list[0])
    target_df = truncate_dataframe(target_df, 1024*512)
    
    # 保存和后续处理
    target_df.to_csv('./data/target.csv', index=False)
    forum_data = convert_df_to_forum(target_df)
    
    # ...后续处理逻辑
    stage2='''
    你现在需要帮助一名中国人民大学的学生用户从下面的格式化消息中总结信息。信息：
    '''
    stage2+=str(forum_data)
    stage2+="\n用户请求："
    stage2+=query   
    response = Application.call(
        # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
        api_key='',
        app_id='c3cc0a7b365d4b2da7cb88ebd1aef1a0',# 替换为实际的应用 ID
        prompt=stage2)
    return response.output.text