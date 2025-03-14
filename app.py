from flask import Flask, request, jsonify, render_template
import os
import utils
from datetime import datetime

from concurrent.futures import ThreadPoolExecutor


os.chdir(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__)

df=utils.df
# 首页路由
@app.route('/')
def index():
    return render_template('index.html')

# 搜索接口
@app.route('/search', methods=['POST'])
def handle_search():
    now = datetime.now()
    if now.hour == 3:
        return render_template('maintenance.html')  # 返回维护页面
    data = request.json
    search_type = data.get('type')
    query = data.get('query')#当是精确搜索时，query是一个列表，AI搜索时，query是一个字符串
    with open ('./data/query.txt','a') as f:
        f.write(query+' AT: '+datetime.now()+'\n')
    if search_type == 'exact':
        temp_df=utils.filter_dataframe(df, query)
        result = utils.convert_df_to_forum(temp_df)

        return jsonify(result)
    else:
        # AI搜索示例返回数据
        return jsonify({
            "type": "ai",
            "results": utils.AI_search(query)
        })
# 反馈接口
@app.route('/feedback', methods=['POST'])
def handle_feedback():
    feedback_count=0
    with open('./data/feedback_count.txt', 'r') as f:
        feedback_count = int(f.read())
    data = request.json
    feedback = data.get('feedback')
    # 这里可以添加处理反馈的逻辑
    if(len(feedback)>300):
        return jsonify({'status': 'failed'})
    print(f"收到用户反馈：{feedback}")
    if feedback_count>20000:
        return
    feedback_count+=1
    with open('./data/feedback.txt', 'a') as f:
        f.write(feedback + '\n')
    with open('./data/feedback_count.txt', 'w') as f:
        f.write(str(feedback_count))
    return jsonify({'status': 'success'})
if __name__ == '__main__':
    feedback_count=0
    app.run(host='0.0.0.0', port=8080)  # 树莓派需要允许外部访问