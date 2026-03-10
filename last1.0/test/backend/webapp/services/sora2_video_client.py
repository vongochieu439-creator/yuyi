# -*- coding: utf-8 -*-
"""
Sora2图生视频客户端 - 使用易API的sora2_video模型
API格式兼容OpenAI /chat/completions，图片通过image_url传入
"""
import asyncio
import base64
import aiohttp
from pathlib import Path
from typing import Optional
from loguru import logger


class Sora2VideoClient:
    """Sora2图生视频客户端（异步版本）"""

    def __init__(self, api_key: str, base_url: str = "https://api.apiyi.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "sora2_video"

    async def generate_video(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        duration: int = 5,
        **kwargs,
    ) -> Optional[str]:
        """
        图生视频

        Args:
            image_url: 图片URL或data URI (data:image/png;base64,...)
            prompt: 运动描述提示词
            duration: 时长（Sora2不支持精确控制，忽略）

        Returns:
            生成的视频URL
        """
        if not prompt:
            prompt = "Smooth cinematic camera movement, professional commercial quality, 4K"

        logger.info(f"[Sora2] 图生视频: prompt={prompt[:60]}...")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]

        payload = {"model": self.model, "messages": messages}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as resp:
                    data = await resp.json()

                    if "error" in data:
                        err_msg = data["error"].get("message", str(data["error"]))
                        logger.error(f"[Sora2] API错误: {err_msg}")
                        raise RuntimeError(f"Sora2 API错误: {err_msg}")

                    video_url = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )

                    if video_url and video_url.startswith("http"):
                        logger.info(f"[Sora2] 视频生成成功: {video_url[:80]}...")
                        return video_url

                    logger.error(f"[Sora2] 未获取到有效视频URL: {video_url[:100] if video_url else 'empty'}")
                    return None

        except asyncio.TimeoutError:
            logger.error("[Sora2] 请求超时(300秒)")
            raise RuntimeError("Sora2请求超时")
        except Exception as e:
            logger.error(f"[Sora2] 调用失败: {e}")
            raise
