# -*- coding: utf-8 -*-
"""
Kling图生视频客户端 - 将关键帧图片转换为视频
基于Kling官方API规范: POST /v1/videos/image2video + GET /v1/videos/{task_id}
"""
import asyncio
import httpx
from typing import Dict, List, Optional
from loguru import logger


class ImageToVideoClient:
    """Kling图生视频客户端 - 处理异步队列式视频生成"""

    def __init__(self, api_key: str, base_url: str = "https://api.remenbaike.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.submit_endpoint = "/kling/v1/videos/image2video"
        self.query_endpoint = "/kling/v1/videos"   # 查询 image2video 任务状态

        # 定价信息（每个视频成本）
        self.cost_per_video = 1.20  # ¥1.20/个

    async def generate_video(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        duration: int = 5,
        model: str = "kling-v1",
        cfg_scale: float = 0.5,
        mode: str = "std"
    ) -> str:
        """
        从图片生成视频（异步队列方式）

        Args:
            image_url: 关键帧图片URL或base64数据
            prompt: 可选的提示词
            duration: 视频时长（秒），支持5或10秒
            model: 模型版本
            cfg_scale: 运镜强度（0.0-1.0）
            mode: 模式（std=标准, pro=专业）

        Returns:
            str: 生成的视频URL
        """
        logger.info(f"开始图生视频: image={image_url[:60]}..., duration={duration}s")

        try:
            async with httpx.AsyncClient(timeout=180.0, trust_env=False) as client:
                # 1. 提交生成请求
                task_id = await self._submit_request(
                    client, image_url, prompt, duration, model, cfg_scale, mode
                )

                if not task_id:
                    raise RuntimeError("提交请求失败，未获取到task_id")

                logger.info(f"请求已提交: task_id={task_id}")

                # 2. 轮询状态直到完成
                result = await self._poll_until_complete(client, task_id)

                if result.get("status") != "succeed":
                    raise RuntimeError(f"生成失败，状态: {result.get('status')}, 消息: {result.get('message', '未知')}")

                # 3. 提取视频URL
                video_url = result.get("video_url")
                if not video_url:
                    raise RuntimeError("生成成功但未获取到视频URL")

                logger.info(f"视频生成成功: {video_url[:80]}...")
                return video_url

        except Exception as e:
            logger.error(f"Kling图生视频API调用失败: {e}")
            raise

    async def _submit_request(
        self,
        client: httpx.AsyncClient,
        image_url: str,
        prompt: Optional[str],
        duration: int,
        model: str,
        cfg_scale: float,
        mode: str
    ) -> Optional[str]:
        """提交图生视频请求，返回task_id"""
        url = f"{self.base_url}{self.submit_endpoint}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model_name": model,
            "image": image_url,
            "mode": mode,
            "duration": str(duration),
            "cfg_scale": cfg_scale
        }

        if prompt:
            payload["prompt"] = prompt

        try:
            logger.info(f"提交请求到: {url}")
            resp = await client.post(url, json=payload, headers=headers, timeout=120.0)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"提交响应: code={data.get('code')}, message={data.get('message')}")
            logger.debug(f"提交响应完整: {data}")

            # Kling API格式: {"code": 0, "data": {"task_id": "...", "task_status": "submitted"}}
            if data.get("code") == 0 and "data" in data:
                task_id = data["data"].get("task_id")
                if task_id:
                    return task_id

            # 兼容其他格式
            if "task_id" in data:
                return data["task_id"]
            if "data" in data and isinstance(data["data"], dict):
                return data["data"].get("task_id")

            logger.error(f"无法从响应中提取task_id: {data}")
            return None

        except httpx.HTTPError as e:
            logger.error(f"提交请求HTTP错误: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"响应内容: {e.response.text[:500]}")
            return None

    async def _poll_until_complete(
        self,
        client: httpx.AsyncClient,
        task_id: str,
        max_retries: int = 120,
        interval: float = 5.0
    ) -> Dict:
        """轮询任务状态直到完成，返回 {"status": ..., "video_url": ...}"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        query_url = f"{self.base_url}{self.query_endpoint}/{task_id}"
        logger.info(f"开始轮询任务状态: {query_url}")

        for attempt in range(max_retries):
            try:
                resp = await client.get(query_url, headers=headers, timeout=15.0)
                resp.raise_for_status()
                data = resp.json()

                logger.debug(f"轮询原始响应: {data}")

                # Kling API格式: {"code": 0, "data": {"task_id": "...", "task_status": "succeed/processing/failed", "task_result": {"videos": [...]}}}
                task_data = data.get("data", {}) if isinstance(data.get("data"), dict) else {}
                task_status = task_data.get("task_status", data.get("status", "unknown"))

                logger.info(f"轮询 {attempt + 1}/{max_retries}: task_status={task_status}")

                # 成功
                if task_status in ["succeed", "completed", "success"]:
                    video_url = self._extract_video_url(data)
                    return {"status": "succeed", "video_url": video_url}

                # 失败
                if task_status in ["failed", "cancelled", "error"]:
                    error_msg = task_data.get("task_status_msg", data.get("message", "未知错误"))
                    logger.error(f"任务失败: status={task_status}, msg={error_msg}")
                    return {"status": task_status, "message": error_msg}

                # 处理中 (submitted, processing, etc.)
                await asyncio.sleep(interval)

            except Exception as e:
                logger.warning(f"轮询异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(interval)

        logger.error(f"轮询超时: 已重试{max_retries}次 ({max_retries * interval}秒)")
        return {"status": "timeout", "message": "轮询超时"}

    def _extract_video_url(self, response_data: Dict) -> Optional[str]:
        """从查询响应中提取视频URL"""
        # Kling标准格式: data.task_result.videos[0].url
        task_data = response_data.get("data", {})
        if isinstance(task_data, dict):
            task_result = task_data.get("task_result", {})
            if isinstance(task_result, dict):
                videos = task_result.get("videos", [])
                if isinstance(videos, list) and len(videos) > 0:
                    video = videos[0]
                    if isinstance(video, dict) and "url" in video:
                        logger.info(f"从 data.task_result.videos[0].url 提取视频URL")
                        return video["url"]

        # 兼容其他格式
        if "video_url" in response_data:
            return response_data["video_url"]
        if "data" in response_data and isinstance(response_data["data"], dict):
            if "video_url" in response_data["data"]:
                return response_data["data"]["video_url"]
        if "videos" in response_data and isinstance(response_data["videos"], list):
            if len(response_data["videos"]) > 0:
                v = response_data["videos"][0]
                return v.get("url") if isinstance(v, dict) else v

        logger.error(f"无法从响应中提取视频URL: {response_data}")
        return None

    def calculate_cost(self, num_videos: int) -> float:
        """计算生成成本"""
        return self.cost_per_video * num_videos

    async def batch_generate(
        self,
        image_prompts: List[Dict],
        duration: int = 5,
        model: str = "kling-v1",
        cfg_scale: float = 0.5
    ) -> List[str]:
        """批量生成多个视频"""
        tasks = []
        for item in image_prompts:
            task = self.generate_video(
                image_url=item["image_url"],
                prompt=item.get("prompt"),
                duration=duration,
                model=model,
                cfg_scale=cfg_scale
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量生成第{i+1}个失败: {result}")
                final_results.append(None)
            else:
                final_results.append(result)

        return final_results
