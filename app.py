from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 导入简化的工具函数
from utils import simple_search, format_search_results, ai_search
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts', methods=['GET'])
def get_posts():
    """获取所有帖子，支持分页"""
    try:
        # 检查维护时间
        now = datetime.now()
        if now.hour == 3:
            return jsonify({"error": "系统维护中"}), 503
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 读取数据
        try:
            df = pd.read_csv('./data/all.csv')
        except FileNotFoundError:
            return jsonify({"posts": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0})
        
        # 数据预处理
        df = df[pd.to_numeric(df['id'], errors='coerce').notnull()]
        df['id'] = df['id'].astype(int)
        
        # 只显示根帖子（Root_code为空的）
        root_posts = df[df['Root_code'].isna()].copy()
        
        # 按时间排序（最新的在上面）
        # 先尝试按时间字段排序，如果时间格式有问题则按ID排序
        try:
            root_posts['time_parsed'] = pd.to_datetime(root_posts['time'], errors='coerce')
            root_posts = root_posts.sort_values('time_parsed', ascending=False, na_position='last')
        except:
            # 如果时间解析失败，按ID降序排序（ID越大越新）
            root_posts = root_posts.sort_values('id', ascending=False)
        
        # 计算分页
        total = len(root_posts)
        total_pages = (total + per_page - 1) // per_page
        
        # 获取当前页数据
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_posts = root_posts.iloc[start_idx:end_idx]
        
        # 格式化数据
        posts = []
        for _, post in page_posts.iterrows():
            posts.append({
                'id': int(post['id']),
                'content': str(post['content']),
                'post_code': str(post['post_code']),
                'class_name': str(post['class_name']),
                'time': str(post['time']),
                'good_count': int(post['good_count']) if pd.notna(post['good_count']) else 0,
                'comment_count': int(post['comment_count']) if pd.notna(post['comment_count']) else 0
            })
        
        return jsonify({
            "posts": posts,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        })
        
    except Exception as e:
        print(f"获取帖子列表错误: {e}")
        return jsonify({"error": "获取帖子列表失败"}), 500

@app.route('/post/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """获取指定帖子的评论"""
    try:
        # 检查维护时间
        now = datetime.now()
        if now.hour == 3:
            return jsonify({"error": "系统维护中"}), 503
        
        # 读取数据
        try:
            df = pd.read_csv('./data/all.csv')
        except FileNotFoundError:
            return jsonify({"comments": []})
        
        # 数据预处理
        df = df[pd.to_numeric(df['id'], errors='coerce').notnull()]
        df['id'] = df['id'].astype(int)
        
        # 查找指定帖子的评论（Root_code不为空且等于该帖子的post_code）
        # 首先找到该帖子的post_code
        post_row = df[df['id'] == post_id]
        if post_row.empty:
            return jsonify({"comments": []})
        
        post_code = post_row.iloc[0]['post_code']
        
        # 查找该帖子的所有评论
        comments = df[(df['Root_code'] == post_code) & (df['id'] != post_id)]
        
        # 按时间排序（最新的在上面）
        try:
            comments['time_parsed'] = pd.to_datetime(comments['time'], errors='coerce')
            comments = comments.sort_values('time_parsed', ascending=False, na_position='last')
        except:
            # 如果时间解析失败，按ID降序排序
            comments = comments.sort_values('id', ascending=False)
        
        # 格式化评论数据
        comments_list = []
        for _, comment in comments.iterrows():
            comments_list.append({
                'id': int(comment['id']),
                'content': str(comment['content']),
                'post_code': str(comment['post_code']),
                'class_name': str(comment['class_name']),
                'time': str(comment['time']),
                'good_count': int(comment['good_count']) if pd.notna(comment['good_count']) else 0,
                'comment_count': int(comment['comment_count']) if pd.notna(comment['comment_count']) else 0
            })
        
        return jsonify({"comments": comments_list})
        
    except Exception as e:
        print(f"获取评论错误: {e}")
        return jsonify({"error": "获取评论失败"}), 500

@app.route('/search', methods=['POST'])
def handle_search():
    try:
        # 检查维护时间
        now = datetime.now()
        if now.hour == 3:
            return render_template('maintenance.html')
        
        # 获取请求数据
        data = request.json
        if not data:
            return jsonify({"error": "无效的请求数据"}), 400
        
        search_type = data.get('type')
        query = data.get('query')
        
        # 记录查询日志
        try:
            with open('./data/query.txt', 'a', encoding='utf-8') as f:
                f.write(f"{str(query)} - {datetime.now()}\n")
        except:
            pass
        
        if search_type == 'exact':
            # 精确搜索
            if not query or len(query) == 0:
                return jsonify({"type": "exact", "results": {"posts": []}})
            
            # 过滤空关键词
            query = [q for q in query if q and q.strip()]
            if not query:
                return jsonify({"type": "exact", "results": {"posts": []}})
            
            # 执行搜索
            search_result = simple_search(query)
            result = format_search_results(search_result, query)
            return jsonify(result)
            
        else:
            # AI搜索
            if not query or not query.strip():
                return jsonify({"type": "ai", "results": "请输入搜索内容"})
            
            ai_result = ai_search(query)
            return jsonify({
                "type": "ai",
                "results": ai_result
            })
            
    except Exception as e:
        print(f"搜索错误: {e}")
        return jsonify({"error": "搜索服务暂时不可用"}), 500

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    try:
        data = request.json
        if not data:
            return jsonify({'status': 'failed', 'message': '无效的请求数据'}), 400
        
        feedback = data.get('feedback', '')
        if not feedback or len(feedback) > 300:
            return jsonify({'status': 'failed', 'message': '反馈内容长度应在1-300字符之间'}), 400
        
        # 保存反馈
        with open('./data/feedback.txt', 'a', encoding='utf-8') as f:
            f.write(f"{feedback} - {datetime.now()}\n")
        
        print(f"收到用户反馈：{feedback}")
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"反馈处理错误: {e}")
        return jsonify({'status': 'failed', 'message': '服务器错误'}), 500

if __name__ == '__main__':
    print("🚀 启动小喇叭高级搜索系统...")
    print("📱 访问地址: http://localhost:8080")
    print("🔍 支持精确搜索和AI智能搜索")
    app.run(host='0.0.0.0', port=8080, debug=False)