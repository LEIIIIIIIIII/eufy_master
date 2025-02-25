from flask import Flask, render_template, request, jsonify
import json
import os
from openai import OpenAI
from flask_cors import CORS
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
CORS(app)

# 简化文件上传配置
UPLOAD_FOLDER = '/tmp/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 降低到5MB

# API配置
client = OpenAI(
    api_key="b5d630b2-e00c-4eeb-b71c-bd92384578bc",  # 直接使用API key
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    http_client=None
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_solution', methods=['POST'])
def generate_solution():
    try:
        data = request.json
        
        # 基本验证
        if not all(key in data for key in ['location', 'floor_plan', 'requirements']):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # 构建精简的提示词
        prompt = f"""基于以下信息生成智能家居方案：
位置：{data['location']}
户型：{data['floor_plan']}
需求：{data['requirements']}

请提供：
1. 安防设备布置
2. 照明系统设计
3. 预算估算"""

        # 调用API时设置较短的超时时间
        response = client.chat.completions.create(
            model="deepseek-v3-241226",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,  # 减少token数量
            timeout=30  # 设置30秒超时
        )

        return jsonify({
            "success": True,
            "solution": {
                "recommendation": response.choices[0].message.content
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
