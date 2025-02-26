from flask import Flask, render_template, request, jsonify
import json
import os
from openai import OpenAI
from flask_cors import CORS
from werkzeug.utils import secure_filename
import datetime
import logging
from typing import Dict, Optional
import httpx

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

# 初始化Flask应用，指定静态文件夹
app = Flask(__name__, static_folder='static')
CORS(app)

# 确保静态图片文件夹存在
if not os.path.exists('static/images'):
    os.makedirs('static/images')

# 配置
API_KEY = "b5d630b2-e00c-4eeb-b71c-bd92384578bc"  # 使用提供的API密钥
MODEL_ID = "deepseek-v3-241226"  # 使用提供的模型ID
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 图片路径配置
SAFETY_PLAN_IMAGE = "/static/images/safety_plan.png"
VALUE_PLAN_IMAGE = "/static/images/value_plan.png"

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

# 初始化OpenAI客户端
http_client = httpx.Client()
client = OpenAI(
    api_key=API_KEY,  # 使用提供的API密钥
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    http_client=http_client
)

# 地区特征检测类
class RegionDetector:
    def __init__(self):
        # 加载地区关键词配置
        self.region_keywords = {
            "中国": ["中国", "北京", "上海", "广州", "深圳", "成都", "重庆",
                   "风水", "朝向", "阴阳", "八卦"],
            "北欧": ["挪威", "瑞典", "芬兰", "丹麦", "冰岛", 
                   "斯堪的纳维亚", "北欧", "极昼", "极夜"],
            "日本": ["日本", "东京", "大阪", "京都", "和室", "榻榻米"],
            "中东": ["迪拜", "阿联酋", "沙特", "科威特", "伊斯兰"],
            # 可以继续添加更多地区
        }
        
        # 加载地区特征配置
        self.region_characteristics = {
            "中国": {
                "cultural_elements": ["风水", "八卦", "阴阳调和"],
                "design_focus": ["朝向", "财位", "宜忌"],
                "prompt_template": """
                请特别注意以下风水要点：
                1. 主要设备避免正对大门
                2. 注意设备安装高度与财位关系
                3. 光线配置需符合阴阳调和
                4. 考虑设备颜色与五行相生相克关系
                5. 摄像头避免对着床位或财位
                """
            },
            "北欧": {
                "cultural_elements": ["极昼极夜", "简约设计", "自然采光"],
                "design_focus": ["光照补充", "色温调节", "节能环保"],
                "prompt_template": """
                请特别注意以下设计要点：
                1. 考虑极昼极夜的光照变化
                2. 强调自然光与人工光的智能切换
                3. 注重节能环保设计
                4. 推荐使用木质元素搭配
                5. 灯光布置需考虑漫长冬季的心理健康
                """
            },
            "日本": {
                "cultural_elements": ["和式空间", "极简主义", "自然元素"],
                "design_focus": ["空间利用", "隐蔽式设计", "多功能"],
                "prompt_template": """
                请特别注意以下设计要点：
                1. 设备应尽量隐蔽，不破坏空间和谐
                2. 考虑小空间的高效利用
                3. 注重设备与传统元素的融合
                4. 灯光应营造温和舒适的氛围
                5. 安防设备应不影响生活动线
                """
            },
            "中东": {
                "cultural_elements": ["伊斯兰图案", "奢华风格", "隐私保护"],
                "design_focus": ["隐私安全", "温度控制", "奢华体验"],
                "prompt_template": """
                请特别注意以下设计要点：
                1. 强调家庭隐私保护
                2. 考虑高温环境下设备的散热
                3. 设计应体现奢华感
                4. 注重女性空间的特殊安防需求
                5. 考虑宗教习俗对设备布置的影响
                """
            },
            "default": {
                "cultural_elements": ["通用设计原则"],
                "design_focus": ["实用性", "安全性"],
                "prompt_template": """
                请注意以下通用设计要点：
                1. 设备布置应符合人体工程学
                2. 确保安防覆盖无死角
                3. 照明应满足基本功能需求
                4. 系统应易于使用和维护
                5. 考虑未来扩展的可能性
                """
            }
        }
    
    def detect_region(self, location: str) -> Dict:
        """
        检测位置所属地区并返回相应的特征配置
        """
        location = location.lower()
        
        # 遍历所有地区的关键词
        for region, keywords in self.region_keywords.items():
            for keyword in keywords:
                if keyword.lower() in location:
                    return {
                        "region": region,
                        "characteristics": self.region_characteristics.get(region, {})
                    }
        
        # 如果没有匹配到任何地区，返回默认配置
        return {
            "region": "default",
            "characteristics": self.region_characteristics.get("default", {})
        }

# 初始化地区检测器
region_detector = RegionDetector()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file part"
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No selected file"
            }), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, new_filename)
            file.save(filepath)
            
            return jsonify({
                "success": True,
                "filename": new_filename,
                "filepath": filepath
            })
        else:
            return jsonify({
                "success": False,
                "error": "File type not allowed"
            }), 400
            
    except Exception as e:
        logging.error(f"Error in upload_image: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

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
        prompt = f"""作为一个eufy智能家居解决方案专家，你需要严格按照以下格式提供两套不同的方案，只使用eufy的产品：

地理位置：{location}
户型信息：{floor_plan}
客户需求：{requirements}

检测到的地区特征: {region_info['region']}
文化元素: {', '.join(region_info['characteristics']['cultural_elements'])}
设计重点: {', '.join(region_info['characteristics']['design_focus'])}

{region_info['characteristics']['prompt_template']}

{'参考图片已上传，请结合图片内容。' if image_paths else ''}

你必须提供以下两套方案，并严格使用Markdown表格格式：

# 方案一：安全至上方案

![安全至上方案]({SAFETY_PLAN_IMAGE})

## 安防设备

| 产品名称 | 数量 | 安装位置 | 单价 | 小计 |
|---------|-----|---------|------|------|
| eufyCam 3 | 2 | 前门、后院 | ¥1,999 | ¥3,998 |
| ... | ... | ... | ... | ... |

## 照明产品

| 产品名称 | 数量 | 安装位置 | 单价 | 小计 |
|---------|-----|---------|------|------|
| Smart Light Strip | 3 | 客厅、主卧、厨房 | ¥299 | ¥897 |
| ... | ... | ... | ... | ... |

## 其他智能设备

| 产品名称 | 数量 | 安装位置 | 单价 | 小计 |
|---------|-----|---------|------|------|
| HomeBase 3 | 1 | 客厅 | ¥1,499 | ¥1,499 |
| ... | ... | ... | ... | ... |

## 方案一总预算：¥XX,XXX

## 方案一特色建议
...

# 方案二：性价比方案

![性价比方案]({VALUE_PLAN_IMAGE})

## 安防设备

| 产品名称 | 数量 | 安装位置 | 单价 | 小计 |
|---------|-----|---------|------|------|
| SoloCam E40 | 2 | 前门、后院 | ¥799 | ¥1,598 |
| ... | ... | ... | ... | ... |

## 照明产品

| 产品名称 | 数量 | 安装位置 | 单价 | 小计 |
|---------|-----|---------|------|------|
| Smart Bulb | 4 | 客厅、主卧、次卧、厨房 | ¥129 | ¥516 |
| ... | ... | ... | ... | ... |

## 其他智能设备

| 产品名称 | 数量 | 安装位置 | 单价 | 小计 |
|---------|-----|---------|------|------|
| ... | ... | ... | ... | ... |

## 方案二总预算：¥XX,XXX

## 方案二特色建议
...

## 系统集成建议
...

重要：你必须在"方案一：安全至上方案"标题下放置安全方案图片，在"方案二：性价比方案"标题下放置性价比方案图片，不可更改图片链接。

以上Markdown表格格式必须严格遵守，请确保所有产品都来自以下eufy产品列表：
{product_info}
"""

        logging.info("Sending request to API")
        
        # 调用API
        response = client.chat.completions.create(
            model=MODEL_ID,  # 使用提供的模型ID
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

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "success": False,
        "error": "文件大小超过限制"
    }), 413

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
