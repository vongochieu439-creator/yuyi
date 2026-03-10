# -*- coding: utf-8 -*-
"""
Seedream 5.0 图片生成API客户端 - 火山引擎 Ark API
同步返回，无需轮询
"""
import asyncio
import base64
import httpx
from typing import Dict, List, Optional
from loguru import logger


class SeedreamClient:
    """Seedream 5.0 图片生成客户端 - 火山引擎方舟API"""

    def __init__(self, api_key: str, base_url: str = "https://ark.cn-beijing.volces.com/api/v3"):
        self.api_key = api_key
        self.base_url = base_url
        self.generate_url = f"{self.base_url}/images/generations"
        self.cost_per_image = 0.25  # ¥0.25/张

    async def generate_image(
        self,
        prompt: str,
        num_images: int = 1,
        img_url: Optional[str] = None,
        size: str = "1920x1080",
        model: str = "doubao-seedream-5-0-260128",
    ) -> List[str]:
        """
        生成图片（同步返回，无需轮询）

        Args:
            prompt: 提示词
            num_images: 生成数量 (1-4)
            img_url: 可选的参考图URL/base64（图生图编辑）
            size: 图片尺寸
            model: 模型名称或endpoint ID

        Returns:
            List[str]: 图片URL列表（base64 data URI）
        """
        logger.info(f"Seedream生成图片: prompt={prompt[:50]}..., num={num_images}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": min(num_images, 4),
            "response_format": "url",
        }

        # 图生图编辑模式
        if img_url:
            payload["image"] = img_url

        # 批量一致性（最多4张时自动启用）
        if num_images > 1:
            payload["sequential_image_generation"] = "auto"

        try:
            async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                resp = await client.post(
                    self.generate_url,
                    json=payload,
                    headers=headers,
                    timeout=120.0,
                )

                if resp.status_code != 200:
                    logger.error(f"Seedream API错误: status={resp.status_code}, body={resp.text[:500]}")
                    raise RuntimeError(f"Seedream API返回错误: {resp.status_code}")

                data = resp.json()
                images = []

                for item in data.get("data", []):
                    url = item.get("url")
                    b64 = item.get("b64_json")
                    if url:
                        images.append(url)
                    elif b64:
                        images.append(f"data:image/png;base64,{b64}")

                if not images:
                    raise RuntimeError(f"Seedream未返回图片: {data}")

                logger.info(f"Seedream图片生成成功: {len(images)}张")
                return images

        except httpx.HTTPError as e:
            logger.error(f"Seedream API网络错误: {e}")
            raise
        except Exception as e:
            logger.error(f"Seedream图片生成失败: {e}")
            raise

    def calculate_cost(self, num_images: int) -> float:
        """计算生成成本"""
        return self.cost_per_image * num_images

    async def batch_generate(
        self,
        prompts: List[str],
        num_images_per_prompt: int = 1,
    ) -> List[List[str]]:
        """批量生成多个提示词的图片"""
        results = []
        for i, prompt in enumerate(prompts):
            try:
                images = await self.generate_image(prompt, num_images_per_prompt)
                results.append(images)
            except Exception as e:
                logger.error(f"批量生成第{i+1}个失败: {e}")
                results.append([])
            await asyncio.sleep(0.3)
        return results
