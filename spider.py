import requests
import csv
import time
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import re
import os 
os.chdir(os.path.dirname(os.path.abspath(__file__)))
'''
这是一个独立于app.py的程序，用于读取all.csv还没有的数据。设定为每天凌晨三点启动（同时服务器关闭一小时）

每天大概有3000条帖子，那就每天更新多4000好了

由于各种问题，all.csv中的日期可能是错的，未来需要重爬
'''
def renew_start_id():
    with open('start_id.txt', 'w') as f:
        f.write(str(get_start_id()+4000))
    return get_start_id()+4000
def get_newest_id():
    # 初始化参数
    newest_id = 0
    with open('newest_id.txt', 'r') as f:
        newest_id = int(f.read())
        if newest_id>0:
            print(f"newest_id is {newest_id}")
    return newest_id
def get_last_id():
    df=pd.read_csv('./data/all.csv')
    print(df["id"].max())
    with open('last_id.txt', 'w') as f:
        f.write(str(int(df["id"].max())))
    return int(df["id"].max())
def get_start_id():#这个是爬取刚开始时最新帖子的id，和newest_id不同的是他只在一次爬取结束（爬完newest_id到last_id）时才更新，而不是每爬一个帖子就更新
    df=pd.read_csv('./data/all.csv')
    return int(df["id"].max())

def get_all_posts(root_file_path: str, comment_file_path: str, newest_id,last_id=0):
    # 检查文件是否存在，并初始化写入器
    root_file_exists = os.path.isfile(root_file_path)
    comment_file_exists = os.path.isfile(comment_file_path)

    with open(root_file_path, 'a', newline='', encoding='utf-8') as root_csv, \
         open(comment_file_path, 'a', newline='', encoding='utf-8') as comment_csv:
        
        root_writer = csv.writer(root_csv)
        comment_writer = csv.writer(comment_csv)

        # 写入标题行（如果文件不存在）
        if not root_file_exists:
            root_writer.writerow(["id", "content", "post_code", "class_code", "class_name", "time", "good_count", "comment_count"])
        
        if not comment_file_exists:
            comment_writer.writerow(["id", "content", "post_code", "class_code", "class_name", "time", "good_count", "comment_count", "Root_code"])

        # 公共请求头
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090c11) XWEB/11275 Flue",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://ruc.yunshangxiaoyuan.cn",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://ruc.yunshangxiaoyuan.cn/treehole/20220429RUC",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "close",
        }

        root_url = "https://ruc.yunshangxiaoyuan.cn/xiaoyuanapi/treeholeuser/getPostList"
        comment_url = "https://ruc.yunshangxiaoyuan.cn/xiaoyuanapi/treeholeuser/getPostCommentList"

        while True:
            # 爬取根帖子分页
            payload = {
                "directCode": "20220429RUC",
                "classCode": "0",
                "typeId": 4,
                "lastId": newest_id,
                "openid": "ogEqTwqw93-HBCQ4dhnNKoluQSuc",
                "keywords": "",
                "sessionId": "",
                "direct": "20220429RUC",
            }

            try:
                response = requests.post(root_url, headers=headers, json=payload)
                if response.status_code != 200:
                    print(f"根帖子请求失败，状态码：{response.status_code}")
                    break

                data = response.json()
                post_list = data.get("postList", [])
                if newest_id <= last_id:
                    print("本次爬取任务已完成")
                    break
                if not post_list:
                    print("跳过id为"+str(newest_id)+"的根帖子")
                    newest_id-=1
                    continue


                # 处理每个根帖子
                for post in post_list:
                    # 写入根帖子
                    root_writer.writerow([
                        post.get("id"),
                        post.get("content"),
                        post.get("post_code"),
                        post.get("class_code"),
                        post.get("class_name"),
                        post.get("time"),
                        post.get("good_count"),
                        post.get("comment_count"),
                    ])
                    print(f"已写入根帖子 {post.get('post_code')}")

                    # 立即爬取该根帖子的回复
                    root_code = post.get("post_code")
                    comment_newest_id = 0
                    while True:
                        comment_payload = {
                            "rootCode": root_code,
                            "lastId": comment_newest_id,
                            "openid": "ogEqTwqw93-HBCQ4dhnNKoluQSuc",
                            "sessionId": "",
                            "directCode": "20220429RUC",
                            "direct": "20220429RUC",
                        }

                        try:
                            comment_response = requests.post(comment_url, headers=headers, json=comment_payload)
                            if comment_response.status_code != 200:
                                print(f"回复请求失败，状态码：{comment_response.status_code}")
                                break

                            comment_data = comment_response.json()
                            comment_list = comment_data.get("commentList", [])

                            if not comment_list:
                                break  # 没有更多回复

                            # 写入回复并添加Root_code
                            for comment in comment_list:
                                comment_writer.writerow([
                                    comment.get("id"),
                                    comment.get("content"),
                                    comment.get("post_code"),
                                    comment.get("class_code"),
                                    comment.get("class_name"),
                                    comment.get("time"),
                                    comment.get("good_count"),
                                    comment.get("comment_count"),
                                    root_code  # 添加关联字段
                                ])
                            print(f"为根帖子 {root_code} 写入 {len(comment_list)} 条回复")

                            # 更新评论分页ID
                            if comment_list:
                                comment_newest_id = comment_list[-1].get("id")
                            else:
                                break

                            time.sleep(0.4)  # 控制请求频率

                        except Exception as e:
                            print(f"回复请求异常：{str(e)}")
                            break

                # 更新根帖子分页ID
                newest_id = post_list[-1].get("id")
                with open('newest_id.txt', 'w') as f:
                    f.write(str(newest_id))
                print(f"更新根帖子分页ID至：{newest_id}")
                time.sleep(0.6)  # 控制根帖子请求频率

            except Exception as e:
                print(f"根帖子请求异常：{str(e)}")
                time.sleep(60)
                continue
                # break

    print("爬取任务完成")
    return

def convert_relative_time(relative_time: str) -> str:
    # 当前时间
    now = datetime.now()

    # 正则匹配不同时间单位的字符串
    patterns = {
        'minute': r'\s*(\d+)\s*分钟前',
        'hour': r'\s*(\d+)\s*小时前',
        'day': r'\s*(\d+)\s*天前',
        'week': r'\s*(\d+)\s*周前',
        'month': r'\s*(\d+)\s*月前',
        'year': r'\s*(\d+)\s*年前'
    }
    for unit, pattern in patterns.items():
        match = re.match(pattern, relative_time)
        if match:
            value = int(match.group(1))
            if unit == 'minute':
                delta = timedelta(minutes=value)
            elif unit == 'hour':
                delta = timedelta(hours=value)
            elif unit == 'day':
                delta = timedelta(days=value)
            elif unit == 'week':
                delta = timedelta(weeks=value)
            elif unit == 'month':
                delta = timedelta(days=value * 30)  # 假设一个月大约30天
            elif unit == 'year':
                delta = timedelta(days=value * 365)  # 假设一年有365天
            # 计算并返回目标时间
            target_time = now - delta
            return target_time.strftime('%Y-%m-%d')

    return relative_time
def combine_posts(root_path: str, comment_path: str) -> pd.DataFrame:
    """
    将根帖子和回复合并为树形结构的DataFrame
    
    参数：
    root_path: 根帖子文件路径（csv格式）
    comment_path: 回复文件路径（csv格式）
    
    返回：
    合并后的DataFrame，结构为：
    [id, content, post_code, class_code, class_name, time, 
     good_count, comment_count, Root_code]
    """
    # 读取数据
    root_df = pd.read_csv(root_path)
    comment_df = pd.read_csv(comment_path)
    
    # 为根帖子添加Root_code列（空值）
    root_df['Root_code'] = pd.NA
    
    # 确保列顺序一致
    columns = [
        "id", "content", "post_code", "class_code", 
        "class_name", "time", "good_count", "comment_count", "Root_code"
    ]
    
    # 创建根帖子排序索引
    root_order = {code: idx for idx, code in enumerate(root_df['post_code'])}
    
    # 处理回复数据
    comment_df['sort_key'] = comment_df['Root_code'].map(root_order)
    
    # 合并数据集
    combined = pd.concat([root_df, comment_df], ignore_index=True)
    
    # 生成排序辅助列
    combined['root_order'] = combined['post_code'].map(root_order).fillna(
        combined['sort_key'])
    combined['is_root'] = combined['Root_code'].isna().astype(int)
    
    # 最终排序（先按根帖子顺序，再按是否是根帖子倒序）
    combined = combined.sort_values(
        ['root_order', 'is_root'], 
        ascending=[True, False]
    ).drop(['sort_key', 'root_order', 'is_root'], axis=1)
    combined['time']=combined['time'].apply(convert_relative_time)
    return combined
# 使用示例
def concat_csv(dest_path,append_path):
    df1 = pd.read_csv(dest_path)
    df2 = pd.read_csv(append_path)
    df_combined = pd.concat([df1, df2], ignore_index=True)
    print("结合成果")
    # 按 'id' 降序排序
    df_combined = df_combined.sort_values(by='id', ascending=False)

    # 保存合并后的 CSV 文件
    df_combined.to_csv('./data/all.csv', index=False)
    return
if __name__ == "__main__":
    with open('start_id.txt', 'w') as f:
        start_id = get_start_id()
        f.write(str(start_id))
    get_all_posts("./data/root_posts.csv", "./data/comments.csv", newest_id=renew_start_id(),last_id=get_last_id())
    combine_posts("./data/root_posts.csv", "./data/comments.csv").to_csv("./data/temp.csv", index=False)
    concat_csv('./data/all.csv','./data/temp.csv')
    