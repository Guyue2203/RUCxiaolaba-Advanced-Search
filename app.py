from flask import Flask, request, jsonify, render_template
import os
import utils
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

os.chdir(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def handle_search():
    now = datetime.now()
    if now.hour == 3:
        return render_template('maintenance.html')
    
    data = request.json
    search_type = data.get('type')
    query = data.get('query')

    if search_type == 'exact':
        if not query or len(query[0]) == 0:
            return jsonify([])
        
        temp_df = utils.filter_dataframe(query)
        result = utils.convert_df_to_forum(temp_df)
        return jsonify(result)
    else:
        return jsonify({
            "type": "ai",
            "results": utils.AI_search(query)
        })

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
    app.run(host='0.0.0.0', port=8080)