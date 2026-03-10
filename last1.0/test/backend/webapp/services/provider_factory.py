# -*- coding: utf-8 -*-
"""
图片/视频生成器工厂 - 根据配置返回对应的API客户端
"""
from loguru import logger

from ..config import (
    NANOBANANA_API_KEY, NANOBANANA_API_BASE_URL,
    KLING_API_KEY, KLING_API_BASE_URL,
    IMAGE_PROVIDER, VIDEO_PROVIDER,
)


def get_image_client():
    """
    根据配置返回图片生成客户端

    Returns:
        SeedreamClient 或 NanoBananaClient（接口兼容）
    """
    provider = IMAGE_PROVIDER.lower()

    if provider == "seedream":
        from ..config import ARK_API_KEY, ARK_BASE_URL, SEEDREAM_MODEL
        from .seedream_client import SeedreamClient
        logger.info("使用Seedream 5.0图片生成")
        return SeedreamClient(
            api_key=ARK_API_KEY,
            base_url=ARK_BASE_URL,
            # model通过generate_image参数传入
        )
    else:
        from .nanobanana_client import NanoBananaClient
        logger.info("使用NanoBanana图片生成")
        return NanoBananaClient(
            api_key=NANOBANANA_API_KEY,
            base_url=NANOBANANA_API_BASE_URL,
        )


def get_video_client():
    """
    根据配置返回视频生成客户端

    Returns:
        SeedanceClient / Sora2VideoClient / ImageToVideoClient（接口兼容）
    """
    provider = VIDEO_PROVIDER.lower()

    if provider == "seedance":
        from ..config import ARK_API_KEY, ARK_BASE_URL, SEEDANCE_ENDPOINT
        from .seedance_client import SeedanceClient
        logger.info("使用Seedance 2.0图生视频")
        return SeedanceClient(
            api_key=ARK_API_KEY,
            base_url=ARK_BASE_URL,
            endpoint_id=SEEDANCE_ENDPOINT,
        )
    elif provider == "sora2":
        from ..config import GEMINI_API_KEY, GEMINI_BASE_URL
        from .sora2_video_client import Sora2VideoClient
        logger.info("使用Sora2图生视频")
        return Sora2VideoClient(
            api_key=GEMINI_API_KEY,
            base_url=GEMINI_BASE_URL,
        )
    else:
        from .image_to_video_client import ImageToVideoClient
        logger.info("使用Kling图生视频")
        return ImageToVideoClient(
            api_key=KLING_API_KEY,
            base_url=KLING_API_BASE_URL,
        )


def get_image_cost_per_unit() -> float:
    """获取当前图片生成单价"""
    provider = IMAGE_PROVIDER.lower()
    if provider == "seedream":
        from ..config import COST_PER_IMAGE_SEEDREAM
        return COST_PER_IMAGE_SEEDREAM
    else:
        from ..config import COST_PER_IMAGE
        return COST_PER_IMAGE


def get_video_cost_per_unit(duration: int = 5) -> float:
    """获取当前视频生成单价"""
    provider = VIDEO_PROVIDER.lower()
    if provider == "seedance":
        from ..config import COST_PER_SECOND_SEEDANCE
        return COST_PER_SECOND_SEEDANCE * duration
    else:
        from ..config import COST_PER_VIDEO
        return COST_PER_VIDEO
