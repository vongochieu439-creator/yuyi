# -*- coding: utf-8 -*-
"""
Web应用配置文件
"""
from pathlib import Path
from .runtime import get_app_dir, get_bundle_dir

# 项目根目录
PROJECT_ROOT = get_app_dir()

# 输出目录（视频存储位置）
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# 静态文件目录
STATIC_DIR = get_bundle_dir() / "webapp" / "static"

# Web服务器配置
HOST = "0.0.0.0"
PORT = 8085

# CORS配置（允许跨域）
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082",
    "http://localhost:8085",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://127.0.0.1:8082",
    "http://127.0.0.1:8085",
]

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = PROJECT_ROOT / "logs" / "webapp.log"

# 视频处理配置
DEFAULT_RESOLUTION = "1920x1080"
DEFAULT_FPS = 30
DEFAULT_BITRATE = "5M"
MAX_CONCURRENT_EXPORTS = 3  # 最多同时导出3个视频

# 缓存配置
CACHE_TTL = 300  # 项目列表缓存5分钟

# ==================== AI服务API配置 ====================

# NanoBanana API (Fal.ai平台 - 图片生成)
import os

NANOBANANA_API_KEY = os.getenv("NANOBANANA_API_KEY", "Q0X6CV17w4th5qwBxxaKAcjatj")
NANOBANANA_API_BASE_URL = os.getenv("NANOBANANA_API_BASE_URL", "https://api.wuyinkeji.com/api")

# 图片生成默认配置
KEYFRAME_DEFAULT_MODEL = "nano-banana"  # 默认模型
KEYFRAME_DEFAULT_QUALITY = "high"       # 默认质量
KEYFRAME_ASPECT_RATIO = "16:9"          # 默认宽高比
KEYFRAME_NUM_VERSIONS = 3               # 重新生成时的版本数

# 成本配置（元）
COST_PER_IMAGE = 0.05      # NanoBanana单张图片成本
COST_PER_VIDEO = 1.20      # Kling单个视频成本
COST_PER_IMAGE_SEEDREAM = 0.25   # Seedream单张图片成本
COST_PER_SECOND_SEEDANCE = 1.0   # Seedance每秒视频成本

# AI评分配置（暂未接入，预留）
ENABLE_AI_SCORING = False
AI_SCORE_PROVIDER = "none"

# 提示词优化配置
ENABLE_PROMPT_OPTIMIZATION = True  # 是否启用提示词优化
PROMPT_OPTIMIZER_PROVIDER = "rule-based"  # 提示词优化方式 (rule-based / gpt4)

# Gemini API (脚本生成)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "sk-qnEWMTAuxto2gX0e0629De3d85Cd42559a9752Da1423254b")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://api.apiyi.com/v1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# TikHub API (抖音数据)
TIKHUB_API_KEY = os.getenv("TIKHUB_API_KEY", "k40dDp4s0V2pqHGuTJC15k36ahixSsFavT3U7EyjUv29lHOfJWWZUAqRMw==")
TIKHUB_BASE_URL = "https://api.tikhub.io"

# Tavily API (AI搜索)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")
TAVILY_BASE_URL = "https://api.tavily.com"

# 品牌档案目录
BRAND_PROFILES_DIR = PROJECT_ROOT / "brand_profiles"

# Kling API (图生视频)
KLING_API_KEY = os.getenv("KLING_API_KEY", "sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq")
KLING_API_BASE_URL = os.getenv("KLING_API_BASE_URL", "https://api.remenbaike.com")

# 视频生成默认配置
VIDEO_DEFAULT_MODEL = "kling-v1"    # 默认模型
VIDEO_DEFAULT_DURATION = 5          # 默认时长（秒）
VIDEO_DEFAULT_CFG_SCALE = 0.5       # 默认运镜强度

# 阶跃星辰 Realtime API (语音访谈)
STEPFUN_API_KEY = os.getenv("STEPFUN_API_KEY", "2LEhcYyCUsSBnNX7hgQnZfvdVGjBMTKlIqmlNxhVbzZbk9og92VMngcmGE4YMAbUr")
STEPFUN_REALTIME_URL = "wss://api.stepfun.com/v1/realtime?model=step-audio-2"
STEPFUN_VOICE = "qingchunshaonv"  # 女声

# ==================== 即梦生态API配置 (火山引擎Ark) ====================
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
SEEDREAM_MODEL = os.getenv("SEEDREAM_MODEL", "doubao-seedream-5-0-260128")
SEEDANCE_ENDPOINT = os.getenv("SEEDANCE_ENDPOINT", "1bd7c3fd-3172-4e0f-b93a-6ec912915ebc")

# 图片/视频生成器选择 (seedream/nanobanana, seedance/kling)
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "nanobanana")
VIDEO_PROVIDER = os.getenv("VIDEO_PROVIDER", "kling")

# ==================== 漫剧生成配置 ====================
COMIC_DRAMA_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "comic_drama"
COMIC_DRAMA_DEFAULT_STYLE = "cinematic"
COMIC_DRAMA_SCENES_COUNT = 6
COMIC_DRAMA_SCENE_DURATION = 5.0
TTS_DEFAULT_VOICE = "zh-CN-YunxiNeural"

# ==================== 阿里云百炼(DashScope) ASR配置 ====================
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-bf8c49192e5a461a86aca4b121c3ac03")
