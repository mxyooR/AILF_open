# noise.py - 干扰域场景定义
# 包含游戏、社交、智能家居等非核心业务场景，用于测试模型的抗干扰能力

NOISE_SCENES = {
    "gaming": {
        "apis": [
            {
                "id": "api_skin",
                "path": "/api/game/buy",
                "method": "POST",
                "desc": "购买皮肤",
                "request": [
                    {"name": "hero_id", "type": "int", "label": "英雄ID", "required": True},
                    {"name": "skin_id", "type": "int", "label": "皮肤ID", "required": True}
                ],
                "response": [
                    {"name": "success", "type": "boolean", "desc": "是否成功"}
                ]
            },
            {
                "id": "api_game_rank",
                "path": "/api/game/rank",
                "method": "GET",
                "desc": "查询排行榜",
                "request": [
                    {"name": "season", "type": "string", "label": "赛季", "required": False}
                ],
                "response": [
                    {"name": "rankings", "type": "array", "desc": "排行榜"}
                ]
            },
            {
                "id": "api_game_match",
                "path": "/api/game/match",
                "method": "POST",
                "desc": "开始匹配",
                "request": [
                    {"name": "mode", "type": "string", "label": "游戏模式", "required": True}
                ],
                "response": [
                    {"name": "match_id", "type": "string", "desc": "匹配ID"}
                ]
            }
        ],
        "workflows": []
    },
    "social": {
        "apis": [
            {
                "id": "api_tweet",
                "path": "/api/sns/post",
                "method": "POST",
                "desc": "发布动态",
                "request": [
                    {"name": "content", "type": "string", "label": "内容", "required": True},
                    {"name": "images", "type": "array", "label": "图片", "required": False}
                ],
                "response": [
                    {"name": "post_id", "type": "string", "desc": "动态ID"}
                ]
            },
            {
                "id": "api_follow",
                "path": "/api/sns/follow",
                "method": "POST",
                "desc": "关注用户",
                "request": [
                    {"name": "user_id", "type": "string", "label": "用户ID", "required": True}
                ],
                "response": [
                    {"name": "success", "type": "boolean", "desc": "是否成功"}
                ]
            },
            {
                "id": "api_timeline",
                "path": "/api/sns/timeline",
                "method": "GET",
                "desc": "查看时间线",
                "request": [
                    {"name": "page", "type": "integer", "label": "页码", "required": False}
                ],
                "response": [
                    {"name": "posts", "type": "array", "desc": "动态列表"}
                ]
            },
            {
                "id": "api_like",
                "path": "/api/sns/like",
                "method": "POST",
                "desc": "点赞",
                "request": [
                    {"name": "post_id", "type": "string", "label": "动态ID", "required": True}
                ],
                "response": [
                    {"name": "success", "type": "boolean", "desc": "是否成功"}
                ]
            }
        ],
        "workflows": []
    },
    "smarthome": {
        "apis": [
            {
                "id": "api_light",
                "path": "/api/iot/switch",
                "method": "POST",
                "desc": "开关灯",
                "request": [
                    {"name": "device_id", "type": "string", "label": "设备ID", "required": True},
                    {"name": "status", "type": "bool", "label": "状态(开/关)", "required": True}
                ],
                "response": [
                    {"name": "success", "type": "boolean", "desc": "是否成功"}
                ]
            },
            {
                "id": "api_temp_set",
                "path": "/api/iot/temperature",
                "method": "POST",
                "desc": "设置温度",
                "request": [
                    {"name": "device_id", "type": "string", "label": "设备ID", "required": True},
                    {"name": "temperature", "type": "float", "label": "温度", "required": True}
                ],
                "response": [
                    {"name": "success", "type": "boolean", "desc": "是否成功"}
                ]
            },
            {
                "id": "api_device_list",
                "path": "/api/iot/devices",
                "method": "GET",
                "desc": "查询设备列表",
                "request": [
                    {"name": "room", "type": "string", "label": "房间", "required": False}
                ],
                "response": [
                    {"name": "devices", "type": "array", "desc": "设备列表"}
                ]
            },
            {
                "id": "api_scene_trigger",
                "path": "/api/iot/scene",
                "method": "POST",
                "desc": "触发场景",
                "request": [
                    {"name": "scene_id", "type": "string", "label": "场景ID", "required": True}
                ],
                "response": [
                    {"name": "success", "type": "boolean", "desc": "是否成功"}
                ]
            }
        ],
        "workflows": []
    }
}
