from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 导入简化的工具函数
from utils import simple_search, format_search_results, ai_search

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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