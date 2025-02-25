from flask import Flask, render_template, request, jsonify
import json
import os
from openai import OpenAI
from flask_cors import CORS
from werkzeug.utils import secure_filename
import datetime
import logging

# 创建必要的文件夹
UPLOAD_FOLDER = '/tmp/uploads'
LOG_FOLDER = '/tmp/logs'
for folder in [UPLOAD_FOLDER, LOG_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 配置日志
logging.basicConfig(
    filename=os.path.join(LOG_FOLDER, 'app.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
CORS(app)

# 文件上传配置
class UploadConfig:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB最大限制
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in UploadConfig.ALLOWED_EXTENSIONS

# 应用配置
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = UploadConfig.MAX_CONTENT_LENGTH

# API配置
os.environ["ARK_API_KEY"] = "b5d630b2-e00c-4eeb-b71c-bd92384578bc"
MODEL_ID = "deepseek-v3-241226"

client = OpenAI(
    api_key=os.environ.get("ARK_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        if not UploadConfig.allowed_file(file.filename):
            return jsonify({'success': False, 'error': '不支持的文件类型'})
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        
        # 创建基于日期的子文件夹
        date_folder = datetime.datetime.now().strftime('%Y%m%d')
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], date_folder)
        
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        
        # 保存文件
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        
        logging.info(f"File uploaded successfully: {filepath}")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath
        })
        
    except Exception as e:
        logging.error(f"File upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate_solution', methods=['POST'])
def generate_solution():
    try:
        # 获取用户输入
        data = request.json
        logging.info(f"Received request data: {data}")
        
        location = data.get('location', '').strip()
        floor_plan = data.get('floor_plan', '').strip()
        requirements = data.get('requirements', '').strip()
        image_paths = data.get('image_paths', [])

        # 验证输入
        if not all([location, floor_plan, requirements]):
            return jsonify({
                "success": False,
                "error": "所有字段都必须填写"
            })

        # 构建提示词
        prompt = f"""作为一个智能家居解决方案专家，请根据以下信息设计方案：

地理位置：{location}
户型信息：{floor_plan}
客户需求：{requirements}

{'参考图片已上传，请结合图片内容。' if image_paths else ''}

请从以下几个方面进行分析和建议：
1. 安防设备布置：包括摄像头、门铃、传感器等的具体安装位置和型号建议
2. 照明方案设计：包括不同区域的照明需求和相应的智能照明产品推荐
3. 系统集成建议：如何让安防和照明系统协同工作
4. 预算估算：大致的投资预算范围
5. 特色建议：根据地理位置和环境特点提供定制化建议"""

        logging.info("Sending request to API")
        
        # 调用API
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.7,
            max_tokens=2000
        )

        result = response.choices[0].message.content
        logging.info("Received API response")

        return jsonify({
            "success": True,
            "solution": {
                "recommendation": result
            }
        })

    except Exception as e:
        logging.error(f"Error in generate_solution: {str(e)}")
        error_message = str(e)
        if "InternalServiceError" in error_message:
            error_message = "服务暂时不可用，请稍后重试"
        
        return jsonify({
            "success": False,
            "error": error_message
        }), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "success": False,
        "error": "文件大小超过限制"
    }), 413

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)