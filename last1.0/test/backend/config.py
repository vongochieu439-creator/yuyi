# -*- coding: utf-8 -*-
"""
羽翼Pro V2 - 颠覆性视频生成系统
全局配置文件
"""

import os
import sys
from pathlib import Path

# ==================== 项目路径 ====================
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TEMP_DIR = PROJECT_ROOT / "temp"
CACHE_DIR = PROJECT_ROOT / "cache"
LOGS_DIR = PROJECT_ROOT / "logs"

# 确保目录存在
for dir_path in [OUTPUTS_DIR, TEMP_DIR, CACHE_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ==================== 速创API配置 ====================
SUCHUANG_API_KEY = os.getenv("SUCHUANG_API_KEY", "Q0X6CV17w4th5qwBxxaKAcjatj")
SUCHUANG_BASE_URL = "https://api.wuyinkeji.com/api"

# ==================== 视频模型配置 ====================
# 11个速创支持的视频生成模型
VIDEO_MODELS = {
    # Sora2 系列 - OpenAI出品
    "sora2-new": {
        "name": "Sora2 New",
        "provider": "openai",
        "endpoint": f"{SUCHUANG_BASE_URL}/sora2-new/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/sora2-new/detail",
        "cost_per_video": 2.5,  # 元
        "duration_options": [10, 15],  # 秒
        "strengths": ["表情自然", "人物对话", "AI音频"],
        "best_for": ["talking_head", "scene"],
        "quality_score": 90,
        "speed_score": 75,  # 生成速度
    },
    "sora2-pro": {
        "name": "Sora2 Pro",
        "provider": "openai",
        "endpoint": f"{SUCHUANG_BASE_URL}/sora2-pro/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/sora2-pro/detail",
        "cost_per_video": 3.5,
        "duration_options": [10, 15],
        "strengths": ["超高质量", "复杂场景"],
        "best_for": ["product", "effect"],
        "quality_score": 95,
        "speed_score": 60,
    },

    # Veo3 系列 - Google出品
    "veo3": {
        "name": "Veo 3",
        "provider": "google",
        "endpoint": f"{SUCHUANG_BASE_URL}/veo3/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/veo3/detail",
        "cost_per_video": 2.0,
        "duration_options": [8, 12],
        "strengths": ["4K画质", "高分辨率"],
        "best_for": ["product", "scene"],
        "quality_score": 92,
        "speed_score": 70,
    },
    "veo3.1": {
        "name": "Veo 3.1",
        "provider": "google",
        "endpoint": f"{SUCHUANG_BASE_URL}/veo3.1/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/veo3.1/detail",
        "cost_per_video": 2.2,
        "duration_options": [8, 12],
        "strengths": ["最新版本", "优化画质"],
        "best_for": ["product", "scene", "effect"],
        "quality_score": 93,
        "speed_score": 72,
    },
    "veo3.1-pro": {
        "name": "Veo 3.1 Pro",
        "provider": "google",
        "endpoint": f"{SUCHUANG_BASE_URL}/veo3.1-pro/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/veo3.1-pro/detail",
        "cost_per_video": 3.0,
        "duration_options": [8, 12],
        "strengths": ["顶级画质", "产品细节"],
        "best_for": ["product", "hands_on"],
        "quality_score": 96,
        "speed_score": 65,
    },
    "veo3.1-fast": {
        "name": "Veo 3.1 Fast",
        "provider": "google",
        "endpoint": f"{SUCHUANG_BASE_URL}/veo3.1-fast/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/veo3.1-fast/detail",
        "cost_per_video": 1.5,
        "duration_options": [8, 12],
        "strengths": ["生成快速", "成本低"],
        "best_for": ["scene", "transition"],
        "quality_score": 85,
        "speed_score": 95,
    },

    # Jimeng AI - 字节跳动
    "jimeng": {
        "name": "即梦AI",
        "provider": "bytedance",
        "endpoint": f"{SUCHUANG_BASE_URL}/jimeng/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/jimeng/detail",
        "cost_per_video": 1.8,
        "duration_options": [10, 15],
        "strengths": ["中文场景", "本土化"],
        "best_for": ["talking_head", "scene"],
        "quality_score": 88,
        "speed_score": 80,
    },

    # Runway - 专业视频编辑
    "runway": {
        "name": "Runway Gen-3",
        "provider": "runway",
        "endpoint": f"{SUCHUANG_BASE_URL}/runway/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/runway/detail",
        "cost_per_video": 2.8,
        "duration_options": [10, 15],
        "strengths": ["专业后期", "特效"],
        "best_for": ["effect", "transition"],
        "quality_score": 91,
        "speed_score": 68,
    },

    # Kling - 快手
    "kling": {
        "name": "可灵 Kling",
        "provider": "kuaishou",
        "endpoint": f"{SUCHUANG_BASE_URL}/kling/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/kling/detail",
        "cost_per_video": 2.0,
        "duration_options": [10, 15],
        "strengths": ["高帧率", "1080p@30fps"],
        "best_for": ["hands_on", "scene"],
        "quality_score": 89,
        "speed_score": 77,
    },

    # Vidu - 生数科技
    "vidu": {
        "name": "Vidu AI",
        "provider": "shengsu",
        "endpoint": f"{SUCHUANG_BASE_URL}/vidu/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/vidu/detail",
        "cost_per_video": 1.6,
        "duration_options": [8, 12],
        "strengths": ["性价比高", "稳定"],
        "best_for": ["scene", "talking_head"],
        "quality_score": 86,
        "speed_score": 82,
    },

    # PixVerse
    "pixverse": {
        "name": "PixVerse",
        "provider": "pixverse",
        "endpoint": f"{SUCHUANG_BASE_URL}/pixverse/submit",
        "query_endpoint": f"{SUCHUANG_BASE_URL}/pixverse/detail",
        "cost_per_video": 1.2,
        "duration_options": [8, 12],
        "strengths": ["超低成本", "快速"],
        "best_for": ["transition", "scene"],
        "quality_score": 80,
        "speed_score": 90,
    },
}

# ==================== 分镜类型定义 ====================
SHOT_TYPES = {
    "talking_head": {
        "name": "人物口播",
        "duration_range": (3, 5),  # 秒
        "visual_weight": 0.7,  # 视觉重要性
        "typical_models": ["sora2-new", "jimeng", "vidu"],
    },
    "product": {
        "name": "产品展示",
        "duration_range": (5, 8),
        "visual_weight": 0.95,
        "typical_models": ["veo3.1-pro", "sora2-pro", "veo3.1"],
    },
    "scene": {
        "name": "环境场景",
        "duration_range": (5, 8),
        "visual_weight": 0.8,
        "typical_models": ["veo3.1", "kling", "jimeng"],
    },
    "hands_on": {
        "name": "手部操作",
        "duration_range": (3, 5),
        "visual_weight": 0.85,
        "typical_models": ["veo3.1-pro", "kling", "sora2-new"],
    },
    "effect": {
        "name": "效果展示",
        "duration_range": (5, 8),
        "visual_weight": 0.9,
        "typical_models": ["sora2-pro", "runway", "veo3.1"],
    },
    "transition": {
        "name": "过渡转场",
        "duration_range": (2, 3),
        "visual_weight": 0.5,
        "typical_models": ["veo3.1-fast", "pixverse", "vidu"],
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
        "preferred_models": ["sora2-new", "veo3.1-fast"],  # 快速模型
        "shot_types": ["talking_head", "scene", "transition"],
        "emotion_curve": [0.3, 0.5, 0.7],  # 情绪逐渐升高
    },
    "act2": {
        "name": "深度展开",
        "duration_ratio": 0.5,  # 占50%
        "shot_count_ratio": 0.5,
        "pace": "稳定",
        "preferred_models": ["veo3.1-pro", "sora2-pro"],  # 高质量模型
        "shot_types": ["product", "hands_on", "effect"],
        "emotion_curve": [0.7, 0.8, 0.9, 0.85],  # 高位震荡
    },
    "act3": {
        "name": "行动号召",
        "duration_ratio": 0.25,  # 占25%
        "shot_count_ratio": 0.2,
        "pace": "快速",
        "preferred_models": ["veo3.1-fast", "sora2-new"],
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
MAX_CONCURRENT_SUBMISSIONS = 50  # 最大同时提交数
MAX_CONCURRENT_DOWNLOADS = 10    # 最大同时下载数
TASK_POLL_INTERVAL = 15          # 任务轮询间隔(秒)
TASK_MAX_WAIT_TIME = 600         # 任务最大等待时间(秒)

# ==================== 日志配置 ====================
LOG_LEVEL = "INFO"
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
