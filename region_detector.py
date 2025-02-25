import json
from typing import Dict, Optional

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
                """
            },
            # 可以继续添加更多地区特征
        }
    
    def detect_region(self, location: str) -> Optional[Dict]:
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
            "characteristics": {
                "cultural_elements": ["通用设计原则"],
                "design_focus": ["实用性", "安全性"],
                "prompt_template": "请提供通用的智能家居解决方案..."
            }
        }