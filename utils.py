# 这个文件是所有的“工具函数”的所在
import pandas as pd
from openai import OpenAI
from dashscope import Application
from http import HTTPStatus
from dashscope import Application
import os
from collections import deque
import re
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def open_df():
    # 读取数据
    df = load_data('./data/all.csv')
    return df
def load_data(csv_path):
    df = pd.read_csv(csv_path)
    return df

def filter_dataframe(df, keywords_list):
    # 处理关键词列表为空的情况
    if not keywords_list:
        return pd.DataFrame(columns=df.columns)
    # 创建副本避免修改原DataFrame
    df = df.copy()
    # 生成分组标识：主帖用post_code，评论用Root_code
    df['group_id'] = df['Root_code'].fillna(df['post_code'])
    # 检查内容是否包含所有关键词
    def contains_all_keywords(content):
        if pd.isna(content):
            return False
        return all(keyword in content for keyword in keywords_list)
    # 应用检查函数
    mask = df['content'].apply(contains_all_keywords)
    # 获取所有匹配的分组ID
    matched_groups = df.loc[mask, 'group_id'].unique()
    # 过滤出所有匹配分组的数据
    filtered_df = df[df['group_id'].isin(matched_groups)].copy()
    # 移除临时列
    filtered_df.drop(columns=['group_id'], inplace=True)
    # 返回结果，确保列顺序与原始DataFrame一致
    return filtered_df

def convert_df_to_forum(df):
    forum_data = {"posts": []}
    
    # 先筛选出主帖子（Root_code 为空的）
    posts = df[df["Root_code"].isna()].copy()
    
    # 先构建基础的帖子字典
    post_dict = {}
    for _, post in posts.iterrows():
        post_dict[post["post_code"]] = {
            "id": post["id"],
            "content": post["content"],
            "comments": []  # 先留空，后续填充
        }
    
    # 筛选出所有评论（Root_code 不为空的）
    comments = df[df["Root_code"].notna()].copy()
    
    # 将评论添加到对应的帖子中
    for _, comment in comments.iterrows():
        root_code = comment["Root_code"]  # 获取所属帖子 post_code
        if root_code in post_dict:  # 确保主帖存在
            post_dict[root_code]["comments"].append({
                "id": comment["id"],
                "content": comment["content"]
            })
    
    # 组装最终的 forum_data
    forum_data["posts"] = list(post_dict.values())
    final={}
    final["type"]="exact"
    final["results"]=forum_data
    
    return final


def truncate_dataframe(df: pd.DataFrame, max_size: int) -> pd.DataFrame:
    """
    截断 DataFrame，使其总大小不超过 max_size 字节。
    
    :param df: 输入的 pandas DataFrame。
    :param max_size: 允许的最大字节数。
    :return: 截断后的 DataFrame。
    """
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
    
    target_df=filter_dataframe(df,keywd_list[0])
    target_df=truncate_dataframe(target_df, 1024*512)
    with open('./data/target.csv', 'w', encoding='utf-8') as f:
        target_df.to_csv(f, index=False)
    forum_data=convert_df_to_forum(target_df)
    
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

df=open_df()