SOLUTION_DATABASE = {
    "examples": [
        {
            "id": 1,
            "location": {
                "country": "中国",
                "city": "北京",
                "type": "公寓",
                "floor": "低层"
            },
            "floor_plan": {
                "size": "90平米",
                "rooms": ["客厅", "主卧", "次卧", "厨房", "阳台"],
                "special_features": ["大落地窗", "开放式厨房"]
            },
            "requirements": ["安防", "智能照明", "远程控制"],
            "solution": "...",  # 详细方案
            "products": [
                {"type": "摄像头", "model": "Indoor Cam 2K", "count": 2},
                {"type": "门铃", "model": "Video Doorbell Dual", "count": 1}
            ]
        },
        {
            "id": 2,
            "location": {
                "country": "挪威",
                "city": "奥斯陆",
                "type": "独栋",
                "floor": "双层"
            },
            "floor_plan": {
                "size": "150平米",
                "rooms": ["客厅", "餐厅", "主卧", "次卧", "书房"],
                "special_features": ["大窗户", "地暖"]
            },
            "requirements": ["光照控制", "安防", "自动化"],
            "solution": "...",  # 详细方案
            "products": [
                {"type": "智能灯带", "model": "Light Strip", "count": 3},
                {"type": "摄像头", "model": "Outdoor Cam Pro", "count": 2}
            ]
        }
        # ... 继续添加更多案例
    ]
}