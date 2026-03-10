# -*- coding: utf-8 -*-
"""
图片生成API客户端 - 速创API (wuyinkeji.com)
支持 sora-image 模型的文生图
"""
import asyncio
import httpx
from typing import Dict, List, Optional
from loguru import logger


class NanoBananaClient:
    """图片生成客户端 - 使用速创API"""

    def __init__(self, api_key: str, base_url: str = "https://api.wuyinkeji.com/api"):
        self.api_key = api_key
        self.base_url = base_url
        self.submit_url = f"{self.base_url}/img/draw"
        self.query_url = f"{self.base_url}/img/drawDetail"
        self.cost_per_image = 0.12  # ¥0.12/张

    async def generate_image(
        self,
        prompt: str,
        num_images: int = 1,
        img_url: Optional[str] = None
    ) -> List[str]:
        """
        生成图片（提交+轮询方式）

        Args:
            prompt: 提示词
            num_images: 生成数量
            img_url: 可选的参考图URL

        Returns:
            List[str]: 图片URL列表
        """
        logger.info(f"开始生成图片: prompt={prompt[:50]}..., num_images={num_images}")

        images = []
        try:
            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                for i in range(num_images):
                    # 1. 提交生成请求
                    task_id = await self._submit_request(client, prompt, img_url=img_url)
                    if not task_id:
                        raise RuntimeError("提交请求失败")

                    logger.info(f"请求已提交: id={task_id}")

                    # 2. 轮询状态直到完成
                    image_url = await self._poll_until_complete(client, task_id)

                    if image_url:
                        images.append(image_url)
                        logger.info(f"图片生成成功: {image_url[:80]}...")
                    else:
                        raise RuntimeError(f"轮询超时，未获取到图片, task_id={task_id}")

            logger.info(f"图片生成完成: {len(images)}张")
            return images

        except Exception as e:
            logger.error(f"图片生成API调用失败: {e}")
            raise

    async def _submit_request(
        self,
        client: httpx.AsyncClient,
        prompt: str,
        img_url: Optional[str] = None
    ) -> Optional[int]:
        """提交生成请求"""
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "model": "sora-image",
            "prompt": prompt,
            "size": "auto"
        }

        if img_url:
            payload["img_url"] = img_url

        try:
            resp = await client.post(
                self.submit_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            data = resp.json()
            logger.debug(f"提交响应: {data}")

            if data.get("code") == 200:
                return data["data"]["id"]
            else:
                logger.error(f"提交请求失败: {data}")
                return None

        except Exception as e:
            logger.error(f"提交请求异常: {e}")
            return None

    async def _poll_until_complete(
        self,
        client: httpx.AsyncClient,
        task_id: int,
        max_retries: int = 60,
        interval: float = 3.0
    ) -> Optional[str]:
        """
        轮询状态直到完成

        状态码: 0=排队中, 1=生成中, 2=成功, 3=失败
        """
        query_params = {
            "key": self.api_key,
            "id": task_id
        }

        for attempt in range(max_retries):
            try:
                resp = await client.get(
                    self.query_url,
                    params=query_params,
                    timeout=15.0
                )
                data = resp.json()

                if data.get("code") != 200:
                    logger.error(f"查询失败: {data}")
                    await asyncio.sleep(interval)
                    continue

                result = data.get("data", {})
                status = result.get("status", -1)
                image_url = result.get("image_url", "")

                logger.info(f"轮询 {attempt + 1}/{max_retries}: status={status}")

                # 成功
                if status == 2 and image_url:
                    return image_url

                # 失败
                if status == 3:
                    fail_reason = result.get("fail_reason", "未知原因")
                    logger.error(f"生成失败: {fail_reason}")
                    raise RuntimeError(f"API生成失败: {fail_reason}")

                # 排队中(0)或生成中(1)，继续等
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"轮询异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(interval)

        logger.error(f"轮询超时: 已重试{max_retries}次")
        return None

    def calculate_cost(self, num_images: int) -> float:
        """计算生成成本"""
        return self.cost_per_image * num_images

    async def batch_generate(
        self,
        prompts: List[str],
        num_images_per_prompt: int = 1
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
            await asyncio.sleep(0.5)
        return results
