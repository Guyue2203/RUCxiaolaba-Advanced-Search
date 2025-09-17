import pandas as pd
import os
import json
import re
from dashscope import Generation
from http import HTTPStatus

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def load_data():
    """加载CSV数据"""
    csv_path = './data/all.csv'
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ 成功加载数据，共 {len(df)} 行")
        return df
    except Exception as e:
        print(f"❌ 加载数据失败: {e}")
        return pd.DataFrame()

def simple_search(keywords_list):
    """简化的搜索功能"""
    if not keywords_list:
        return pd.DataFrame()
    
    # 过滤空关键词
    keywords_list = [kw for kw in keywords_list if kw and kw.strip()]
    if not keywords_list:
        return pd.DataFrame()
    
    # 加载数据
    df = load_data()
    if df.empty:
        return pd.DataFrame()
    
    # 简单搜索：只要内容包含任一关键词就匹配
    mask = pd.Series([False] * len(df))
    for keyword in keywords_list:
        # 转义特殊字符，避免正则表达式错误
        escaped_keyword = re.escape(keyword)
        mask |= df['content'].str.contains(escaped_keyword, case=False, na=False)
    
    result = df[mask].copy()
    print(f"🔍 搜索关键词 {keywords_list}，找到 {len(result)} 条结果")
    return result

def format_search_results(df, keywords_list):
    """格式化搜索结果"""
    if df.empty:
        return {
            "type": "exact",
            "results": {
                "posts": [{
                    "id": 0,
                    "content": "没有找到相关信息",
                    "comments": []
                }]
            }
        }
    
    # 高亮关键词
    def highlight_keywords(text):
        if pd.isna(text):
            return ""
        for keyword in keywords_list:
            if keyword:
                text = text.replace(keyword, f'<mark>{keyword}</mark>')
        return text
    
    # 分组处理：根据post_code后缀区分主帖子和评论
    # 主帖子：post_code以P1结尾，Root_code为空
    # 评论：post_code以P2结尾，Root_code为主帖子的post_code
    root_posts = df[(df['post_code'].str.endswith('P1')) & (df['Root_code'].isna())].copy()
    
    # 加载所有评论数据（不仅仅是搜索结果中的评论）
    all_data = load_data()
    all_comments = all_data[all_data['post_code'].str.endswith('P2')].copy()
    
    posts = []
    for _, post in root_posts.iterrows():
        # 获取该帖子的所有评论（从完整数据中获取）
        post_comments = all_comments[all_comments['Root_code'] == post['post_code']]
        
        comment_list = []
        for _, comment in post_comments.iterrows():
            comment_list.append({
                "id": comment['id'],
                "content": highlight_keywords(comment['content']),
                "post_time": comment.get('time', ''),
                "post_code": comment['post_code']
            })
        
        posts.append({
            "id": post['id'],
            "content": highlight_keywords(post['content']),
            "post_time": post.get('time', ''),
            "comments": comment_list,
            "comment_count": post.get('comment_count', len(comment_list))
        })
    
    # 按时间排序（如果有post_code的话）
    try:
        posts.sort(key=lambda x: x['post_time'], reverse=True)
    except:
        pass
    
    return {
        "type": "exact",
        "results": {"posts": posts}
    }

def ai_search(query):
    """简化的AI搜索"""
    try:
        # 设置API
        os.environ['DASHSCOPE_HTTP_BASE_URL'] = 'https://dashscope.aliyuncs.com/api/v1/'
        
        # 第一阶段：生成关键词
        stage1 = f'''
        你现在需要帮助一名中国人民大学的学生用户解决问题，用户需要从一个文字论坛中过滤出他所需要的信息。
        接下来他会给出一个要求，请你根据这个要求给出一些相关的关键词，最终只返回一个元素为列表的列表，其中每个元素列表包含一些关键词。
        关键词的选取原则是：如果当若干个关键词同时出现时代表了该文本可能包含用户所需要的信息，那么就将这些关键词作为关键词列表的一个元素。请返回尽可能多的列表
        
        如果用户的信息不是一个请求，或者你认为用户的信息和论坛可能的信息无关，那么请返回一个空列表。
        
        例如用户信息为：请帮我总结一下统计学院的保研率相关信息
        那么你可以返回[['统计学院', '保研率'],['统院','保研率'],['统院','保研'],['统计学院','推免'],['统院','推免']]
        
        用户信息：{query}
        '''
        
        response = Generation.call(
            api_key='',  # 需要配置API密钥
            model='qwen-plus',
            prompt=stage1
        )
        
        if response.status_code != HTTPStatus.OK:
            return f"AI服务暂时不可用，请稍后再试"
        
        try:
            keywords_list = eval(response.output.text)
        except:
            keywords_list = []
        
        if not keywords_list:
            return "抱歉，我无法理解您的请求，请尝试更具体的描述"
        
        # 使用第一个关键词组合进行搜索
        search_result = simple_search(keywords_list[0])
        
        if search_result.empty:
            return "没有找到相关信息，请尝试其他关键词"
        
        # 限制结果数量
        if len(search_result) > 50:
            search_result = search_result.head(50)
        
        # 第二阶段：AI总结
        stage2 = f'''
        你现在需要帮助一名中国人民大学的学生用户从下面的论坛信息中总结相关内容。
        
        论坛信息：
        {search_result[['content']].to_string()}
        
        用户请求：{query}
        
        请用简洁明了的中文总结相关信息，重点突出用户关心的内容。
        '''
        
        response2 = Generation.call(
            api_key='',  # 需要配置API密钥
            model='qwen-plus',
            prompt=stage2
        )
        
        if response2.status_code == HTTPStatus.OK:
            return response2.output.text
        else:
            return "AI总结服务暂时不可用，但已找到相关帖子"
            
    except Exception as e:
        print(f"AI搜索出错: {e}")
        return "AI搜索服务暂时不可用，请使用精确搜索"