# -*- coding: utf-8 -*-
"""
羽翼Pro V2 - Remenbaike API配置
基于测试成功的Veo、Kling、Grok三个平台
"""

import os
from pathlib import Path

# ==================== 项目路径 ====================
PROJECT_ROOT = Path(__file__).parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TEMP_DIR = PROJECT_ROOT / "temp"
CACHE_DIR = PROJECT_ROOT / "cache"
LOGS_DIR = PROJECT_ROOT / "logs"

# 确保目录存在
for dir_path in [OUTPUTS_DIR, TEMP_DIR, CACHE_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ==================== Remenbaike API配置 ====================
REMENBAIKE_API_KEY = os.getenv("REMENBAIKE_API_KEY", "sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq")
REMENBAIKE_BASE_URL = "https://api.remenbaike.com"

# ==================== 视频模型配置 ====================
# 3个已测试成功的视频生成模型
VIDEO_MODELS = {
    # Veo 3.1 Fast - Google出品，快速版本
    "veo3.1-fast": {
        "name": "Veo 3.1 Fast",
        "provider": "google",
        "platform": "veo",
        "create_endpoint": f"{REMENBAIKE_BASE_URL}/v1/video/create",
        "query_endpoint": f"{REMENBAIKE_BASE_URL}/v1/video/query",
        "cost_per_video": 1.5,  # 估算成本（元）
        "duration_options": [5, 10],  # 秒
        "aspect_ratios": ["9:16", "16:9", "1:1"],
        "strengths": ["生成快速", "成本低", "稳定"],
        "best_for": ["scene", "transition", "talking_head"],
        "quality_score": 85,
        "speed_score": 95,  # 测试结果：177秒
        "avg_generation_time": 177,  # 平均生成时间（秒）

        # API参数格式
        "request_format": {
            "model": "veo3.1-fast",
            "prompt": "{prompt}",
            "enhance_prompt": True,
            "aspect_ratio": "{aspect_ratio}"
        },
        "response_format": "veo",  # 响应格式类型
        "status_field": "state",  # 状态字段名
        "video_url_field": "video_url",  # 视频URL字段名
        "task_id_field": "task_id"  # 任务ID字段名
    },

    # Kling v2.5 Turbo - 快手出品，最快的模型
    "kling-v2.5-turbo": {
        "name": "Kling v2.5 Turbo",
        "provider": "kuaishou",
        "platform": "kling",
        "create_endpoint": f"{REMENBAIKE_BASE_URL}/kling/v1/videos/text2video",
        "query_endpoint": f"{REMENBAIKE_BASE_URL}/kling/v1/videos/text2video/{{task_id}}",
        "cost_per_video": 1.2,
        "duration_options": [5, 10],
        "aspect_ratios": ["9:16", "16:9", "1:1"],
        "strengths": ["超快速度", "高帧率", "性价比高"],
        "best_for": ["hands_on", "scene", "product"],
        "quality_score": 88,
        "speed_score": 98,  # 测试结果：76秒（最快！）
        "avg_generation_time": 76,

        # API参数格式
        "request_format": {
            "model_name": "kling-v2-5-turbo",
            "prompt": "{prompt}",
            "duration": "{duration}",
            "aspect_ratio": "{aspect_ratio}"
        },
        "response_format": "kling",
        "status_field": "task_status",
        "video_url_field": "videos[0].url",  # 嵌套路径
        "task_id_field": "task_id"
    },

    # Grok Video 3 - xAI出品，实时进度展示
    "grok-video-3": {
        "name": "Grok Video 3",
        "provider": "xai",
        "platform": "grok",
        "create_endpoint": f"{REMENBAIKE_BASE_URL}/grok/v1/video/generations",
        "query_endpoint": f"{REMENBAIKE_BASE_URL}/grok/v1/video/generations/{{task_id}}",
        "cost_per_video": 1.8,
        "duration_options": [5, 10],
        "aspect_ratios": ["9:16", "16:9", "1:1"],
        "strengths": ["实时进度", "质量稳定", "支持多种风格"],
        "best_for": ["effect", "product", "scene"],
        "quality_score": 90,
        "speed_score": 85,  # 测试结果：120秒
        "avg_generation_time": 120,

        # API参数格式
        "request_format": {
            "prompt": "{prompt}",
            "aspect_ratio": "{aspect_ratio}",
            "duration": "{duration}"
        },
        "response_format": "grok",
        "status_field": "status",
        "video_url_field": "video_url",
        "task_id_field": "id"
    },
}

# ==================== 分镜类型定义 ====================
SHOT_TYPES = {
    "talking_head": {
        "name": "人物口播",
        "duration_range": (3, 5),  # 秒
        "visual_weight": 0.7,  # 视觉重要性
        "typical_models": ["veo3.1-fast", "kling-v2.5-turbo"],  # 推荐用快速模型
    },
    "product": {
        "name": "产品展示",
        "duration_range": (5, 8),
        "visual_weight": 0.95,
        "typical_models": ["grok-video-3", "kling-v2.5-turbo"],  # 推荐高质量模型
    },
    "scene": {
        "name": "环境场景",
        "duration_range": (5, 8),
        "visual_weight": 0.8,
        "typical_models": ["veo3.1-fast", "kling-v2.5-turbo", "grok-video-3"],  # 都可以
    },
    "hands_on": {
        "name": "手部操作",
        "duration_range": (3, 5),
        "visual_weight": 0.85,
        "typical_models": ["kling-v2.5-turbo", "grok-video-3"],  # 需要高帧率
    },
    "effect": {
        "name": "效果展示",
        "duration_range": (5, 8),
        "visual_weight": 0.9,
        "typical_models": ["grok-video-3", "kling-v2.5-turbo"],  # 需要高质量
    },
    "transition": {
        "name": "过渡转场",
        "duration_range": (2, 3),
        "visual_weight": 0.5,
        "typical_models": ["veo3.1-fast"],  # 用最快的
    },
}

# ==================== 视频长度配置 ====================
VIDEO_LENGTH_PRESETS = {
    "short": {
        "name": "短视频",
        "total_duration": 60,  # 60秒
        "shot_count_range": (10, 15),
        "pace": "快节奏",
    },
    "medium": {
        "name": "中等长度",
        "total_duration": 120,  # 2分钟
        "shot_count_range": (20, 30),
        "pace": "中等节奏",
    },
    "long": {
        "name": "长视频",
        "total_duration": 180,  # 3分钟
        "shot_count_range": (30, 45),
        "pace": "叙事节奏",
    },
    "ultra_long": {
        "name": "超长视频",
        "total_duration": 300,  # 5分钟
        "shot_count_range": (45, 60),
        "pace": "完整故事",
    },
}

# ==================== 三幕式结构 ====================
THREE_ACT_STRUCTURE = {
    "act1": {
        "name": "冲突引入",
        "duration_ratio": 0.25,  # 占总时长的25%
        "shot_count_ratio": 0.3,  # 占总分镜数的30%
        "pace": "快速",
        "preferred_models": ["veo3.1-fast", "kling-v2.5-turbo"],  # 快速模型
        "shot_types": ["talking_head", "scene", "transition"],
        "emotion_curve": [0.3, 0.5, 0.7],  # 情绪逐渐升高
    },
    "act2": {
        "name": "深度展开",
        "duration_ratio": 0.5,  # 占50%
        "shot_count_ratio": 0.5,
        "pace": "稳定",
        "preferred_models": ["grok-video-3", "kling-v2.5-turbo"],  # 高质量模型
        "shot_types": ["product", "hands_on", "effect"],
        "emotion_curve": [0.7, 0.8, 0.9, 0.85],  # 高位震荡
    },
    "act3": {
        "name": "行动号召",
        "duration_ratio": 0.25,  # 占25%
        "shot_count_ratio": 0.2,
        "pace": "快速",
        "preferred_models": ["veo3.1-fast", "kling-v2.5-turbo"],
        "shot_types": ["talking_head", "effect", "transition"],
        "emotion_curve": [0.85, 0.95, 1.0],  # 冲向高潮
    },
}

# ==================== 爆款预测配置 ====================
VIRAL_PREDICTION_WEIGHTS = {
    "hook_strength": 0.25,  # 开头吸引力 (前3秒)
    "emotion_curve": 0.20,  # 情绪曲线
    "visual_impact": 0.15,  # 视觉冲击力
    "info_density": 0.15,   # 信息密度
    "cta_clarity": 0.10,    # 行动号召明确性
    "shareability": 0.10,   # 传播意愿
    "platform_fit": 0.05,   # 平台适配度
}

VIRAL_SCORE_THRESHOLDS = {
    "excellent": 90,  # 优秀 (预测爆款概率 >80%)
    "good": 80,       # 良好 (预测爆款概率 50-80%)
    "average": 70,    # 一般 (预测爆款概率 20-50%)
    "poor": 60,       # 较差 (预测爆款概率 <20%)
}

# ==================== AI配置 ====================
# Gemini配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "sk-qnEWMTAuxto2gX0e0629De3d85Cd42559a9752Da1423254b")
GEMINI_BASE_URL = "https://api.apiyi.com/v1"
GEMINI_MODEL = "gemini-2.5-flash"

# ==================== 并发配置 ====================
MAX_CONCURRENT_SUBMISSIONS = 10  # 减少到10（remenbaike API可能有限制）
MAX_CONCURRENT_DOWNLOADS = 5     # 减少到5
TASK_POLL_INTERVAL = 10          # 任务轮询间隔(秒)
TASK_MAX_WAIT_TIME = 300         # 任务最大等待时间(秒) - 基于测试最慢177秒

# ==================== 日志配置 ====================
LOG_LEVEL = "INFO"
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"

# ==================== 平台状态映射 ====================
# 不同平台的状态字符串统一映射
STATUS_MAPPING = {
    "veo": {
        "pending": ["pending", "processing"],
        "completed": ["completed", "succeed", "success"],
        "failed": ["failed", "error"]
    },
    "kling": {
        "pending": ["submitted", "processing"],
        "completed": ["succeed"],
        "failed": ["failed"]
    },
    "grok": {
        "pending": ["pending", "processing", "queued"],
        "completed": ["completed", "success"],
        "failed": ["failed", "error"]
    }
}
