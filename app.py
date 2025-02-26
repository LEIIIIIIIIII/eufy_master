from flask import Flask, render_template, request, jsonify
import json
import os
from openai import OpenAI
from flask_cors import CORS
from werkzeug.utils import secure_filename
import datetime
import logging
from typing import Dict, Optional

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

# eufy产品信息库
EUFY_PRODUCTS = {
    "security": [
        {"name": "eufyCam 3", "description": "4K无线安防摄像头，太阳能供电", "price": "¥1,999"},
        {"name": "Video Doorbell Dual", "description": "双镜头智能门铃，可检测包裹", "price": "¥1,299"},
        {"name": "Indoor Cam 2K", "description": "室内安防摄像头，支持人脸识别", "price": "¥349"},
        {"name": "SoloCam E40", "description": "2K无线摄像头，内置聚光灯", "price": "¥799"},
        {"name": "SmartDrop", "description": "智能包裹箱，防盗防雨", "price": "¥3,499"},
        {"name": "Entry Sensor", "description": "门窗传感器，开门提醒", "price": "¥199"},
        {"name": "Motion Sensor", "description": "动作传感器，检测移动", "price": "¥249"}
    ],
    "lighting": [
        {"name": "Smart Light Strip", "description": "可调色温智能灯带", "price": "¥299"},
        {"name": "Smart Bulb", "description": "智能灯泡，支持语音控制", "price": "¥129"},
        {"name": "Lumos Smart Bulb", "description": "可调色温智能灯泡", "price": "¥149"},
        {"name": "Floodlight Cam 2 Pro", "description": "三头泛光灯摄像头", "price": "¥1,999"}
    ],
    "smart_home": [
        {"name": "HomeBase 3", "description": "智能家居控制中心", "price": "¥1,499"},
        {"name": "Smart Lock C210", "description": "指纹密码锁", "price": "¥1,299"},
        {"name": "Smart Scale P2 Pro", "description": "智能体脂称", "price": "¥399"},
        {"name": "RoboVac X8", "description": "激光导航扫地机器人", "price": "¥2,999"}
    ]
}

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

        # 检测地区特征
        region_info = region_detector.detect_region(location)
        logging.info(f"Detected region: {region_info['region']}")

        # 准备eufy产品信息
        product_info = ""
        for category, products in EUFY_PRODUCTS.items():
            product_info += f"\n{category.upper()} 产品系列:\n"
            for product in products:
                product_info += f"- {product['name']}: {product['description']} ({product['price']})\n"

        # 构建提示词
        prompt = f"""作为一个eufy智能家居解决方案专家，请根据以下信息设计两套不同的方案，主要推荐eufy的产品：

地理位置：{location}
户型信息：{floor_plan}
客户需求：{requirements}

检测到的地区特征: {region_info['region']}
文化元素: {', '.join(region_info['characteristics']['cultural_elements'])}
设计重点: {', '.join(region_info['characteristics']['design_focus'])}

{region_info['characteristics']['prompt_template']}

{'参考图片已上传，请结合图片内容。' if image_paths else ''}

请提供两套方案：
1. 【安全至上方案】：优先考虑最全面的安全保障，预算充足
2. 【性价比方案】：在保证基本功能的前提下，追求最佳性价比

对于每个方案，请以表格形式列出以下内容：
1. 安防设备：包括产品名称、数量、安装位置和价格
2. 照明产品：包括产品名称、数量、安装位置和价格
3. 其他智能设备：包括产品名称、数量、安装位置和价格

另外，请提供一个系统集成建议，说明如何让这些设备协同工作。最后给出总预算和根据地区特点的定制化建议。

请使用Markdown表格格式，确保输出美观，便于阅读。例如：

## 安全至上方案

### 安防设备

| 产品名称 | 数量 | 安装位置 | 单价 | 小计 |
|---------|-----|---------|------|------|
| eufyCam 3 | 2 | 前门、后院 | ¥1,999 | ¥3,998 |
| ... | ... | ... | ... | ... |

请主要推荐以下eufy产品：
{product_info}
"""

        logging.info("Sending request to API")
        
        # 调用API
        response = client.chat.completions.create(
            model="deepseek-v3-241226",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.7,
            max_tokens=2500
        )

        result = response.choices[0].message.content
        logging.info("Received API response")

        return jsonify({
            "success": True,
            "solution": {
                "recommendation": result,
                "region_info": {
                    "region": region_info["region"],
                    "cultural_elements": region_info["characteristics"]["cultural_elements"],
                    "design_focus": region_info["characteristics"]["design_focus"]
                }
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
