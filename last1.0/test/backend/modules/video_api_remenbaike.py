# -*- coding: utf-8 -*-
"""
Remenbaike API统一接口层
支持Veo、Kling、Grok三个平台的统一调用
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import asyncio
from typing import Dict, Optional, Tuple
from loguru import logger

from config_remenbaike import (
    REMENBAIKE_API_KEY,
    REMENBAIKE_BASE_URL,
    VIDEO_MODELS,
    STATUS_MAPPING
)


class RembaikeVideoAPI:
    """Remenbaike统一视频生成API"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or REMENBAIKE_API_KEY
        self.base_url = REMENBAIKE_BASE_URL
        self.models = VIDEO_MODELS
        logger.info("🎥 Remenbaike视频API初始化完成")
        logger.info(f"   支持模型: {len(self.models)} 个 (Veo, Kling, Grok)")

    async def submit_task(
        self,
        model_id: str,
        prompt: str,
        duration: Optional[int] = None,
        aspect_ratio: str = "9:16"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        提交视频生成任务

        Args:
            model_id: 模型ID
            prompt: 提示词
            duration: 时长(秒)，None则使用模型默认
            aspect_ratio: 宽高比

        Returns:
            (成功?, 任务ID, 错误信息)
        """
        if model_id not in self.models:
            return False, None, f"未知模型: {model_id}"

        model_info = self.models[model_id]
        platform = model_info["platform"]

        # 确定时长
        if duration is None:
            duration = model_info["duration_options"][0]
        elif duration not in model_info["duration_options"]:
            # 选择最接近的
            duration = min(model_info["duration_options"], key=lambda x: abs(x - duration))

        # 根据平台构建请求
        try:
            if platform == "veo":
                return await self._submit_veo(model_info, prompt, aspect_ratio)
            elif platform == "kling":
                return await self._submit_kling(model_info, prompt, duration, aspect_ratio)
            elif platform == "grok":
                return await self._submit_grok(model_info, prompt, duration, aspect_ratio)
            else:
                return False, None, f"未支持的平台: {platform}"

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 提交异常 [{model_id}]: {error_msg}")
            return False, None, error_msg

    async def _submit_veo(
        self,
        model_info: Dict,
        prompt: str,
        aspect_ratio: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """提交Veo任务"""
        url = model_info["create_endpoint"]

        request_data = {
            "model": "veo3.1-fast",
            "prompt": prompt,
            "enhance_prompt": True,
            "aspect_ratio": aspect_ratio
        }

        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=request_data
            )

            if response.status_code != 200:
                return False, None, f"HTTP {response.status_code}: {response.text[:200]}"

            result = response.json()

            # Veo响应格式: {code, data: {task_id}}
            code = result.get("code")
            if code == 0:
                data = result.get("data", {})
                task_id = data.get("task_id")
                if task_id:
                    logger.info(f"✅ Veo任务已提交: {task_id}")
                    return True, task_id, None
                else:
                    return False, None, "未返回任务ID"
            else:
                message = result.get("message", "未知错误")
                return False, None, f"API错误: code={code}, message={message}"

    async def _submit_kling(
        self,
        model_info: Dict,
        prompt: str,
        duration: int,
        aspect_ratio: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """提交Kling任务"""
        url = model_info["create_endpoint"]

        request_data = {
            "model_name": "kling-v2-5-turbo",
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio
        }

        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=request_data
            )

            if response.status_code != 200:
                return False, None, f"HTTP {response.status_code}: {response.text[:200]}"

            result = response.json()

            # Kling响应格式: {code, data: {task_id, task_status}}
            code = result.get("code")
            if code == 0:
                data = result.get("data", {})
                task_id = data.get("task_id")
                if task_id:
                    logger.info(f"✅ Kling任务已提交: {task_id}")
                    return True, task_id, None
                else:
                    return False, None, "未返回任务ID"
            else:
                message = result.get("message", "未知错误")
                return False, None, f"API错误: code={code}, message={message}"

    async def _submit_grok(
        self,
        model_info: Dict,
        prompt: str,
        duration: int,
        aspect_ratio: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """提交Grok任务"""
        url = model_info["create_endpoint"]

        request_data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "duration": duration
        }

        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=request_data
            )

            if response.status_code != 200:
                return False, None, f"HTTP {response.status_code}: {response.text[:200]}"

            result = response.json()

            # Grok响应格式: {code, data: {id, status}} 或 {id, status}
            code = result.get("code")
            if code is not None and code == 0:
                # 标准格式
                data = result.get("data", {})
                task_id = data.get("id")
            else:
                # 直接格式
                task_id = result.get("id")

            if task_id:
                logger.info(f"✅ Grok任务已提交: {task_id}")
                return True, task_id, None
            else:
                return False, None, "未返回任务ID"

    async def query_task(
        self,
        model_id: str,
        task_id: str
    ) -> Tuple[int, Optional[str], Optional[str]]:
        """
        查询任务状态

        Args:
            model_id: 模型ID
            task_id: 任务ID

        Returns:
            (状态, 视频URL, 错误信息)
            状态: 0=排队/处理中, 1=成功, 2=失败
        """
        if model_id not in self.models:
            return 2, None, f"未知模型: {model_id}"

        model_info = self.models[model_id]
        platform = model_info["platform"]

        try:
            if platform == "veo":
                return await self._query_veo(model_info, task_id)
            elif platform == "kling":
                return await self._query_kling(model_info, task_id)
            elif platform == "grok":
                return await self._query_grok(model_info, task_id)
            else:
                return 2, None, f"未支持的平台: {platform}"

        except Exception as e:
            return 2, None, str(e)

    async def _query_veo(
        self,
        model_info: Dict,
        task_id: str
    ) -> Tuple[int, Optional[str], Optional[str]]:
        """查询Veo任务状态"""
        url = model_info["query_endpoint"]

        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json={"task_id": task_id}
            )

            if response.status_code != 200:
                return 2, None, f"HTTP {response.status_code}"

            result = response.json()

            # Veo响应: {code, data: {state, video_url}}
            code = result.get("code")
            if code != 0:
                return 2, None, f"API错误: code={code}"

            data = result.get("data", {})
            state = data.get("state", "").lower()
            video_url = data.get("video_url")

            # 状态映射
            if state in ["completed", "succeed", "success"]:
                return 1, video_url, None
            elif state in ["failed", "error"]:
                error = data.get("error", "生成失败")
                return 2, None, error
            else:  # pending, processing
                return 0, None, None

    async def _query_kling(
        self,
        model_info: Dict,
        task_id: str
    ) -> Tuple[int, Optional[str], Optional[str]]:
        """查询Kling任务状态"""
        # Kling的查询URL需要包含task_id
        url = model_info["query_endpoint"].replace("{task_id}", task_id)

        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

            if response.status_code != 200:
                return 2, None, f"HTTP {response.status_code}"

            result = response.json()

            # Kling响应: {code, data: {task_status, task_result: {videos: [{url}]}}}
            code = result.get("code")
            if code != 0:
                return 2, None, f"API错误: code={code}"

            data = result.get("data", {})
            task_status = data.get("task_status", "").lower()

            # 状态映射
            if task_status == "succeed":
                task_result = data.get("task_result", {})
                videos = task_result.get("videos", [])
                if videos and len(videos) > 0:
                    video_url = videos[0].get("url")
                    return 1, video_url, None
                else:
                    return 2, None, "未返回视频URL"
            elif task_status == "failed":
                error = data.get("task_status_msg", "生成失败")
                return 2, None, error
            else:  # submitted, processing
                return 0, None, None

    async def _query_grok(
        self,
        model_info: Dict,
        task_id: str
    ) -> Tuple[int, Optional[str], Optional[str]]:
        """查询Grok任务状态"""
        url = model_info["query_endpoint"].replace("{task_id}", task_id)

        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

            if response.status_code != 200:
                return 2, None, f"HTTP {response.status_code}"

            result = response.json()

            # Grok响应: {code, data: {status, video_url}} 或 {status, video_url}
            code = result.get("code")
            if code is not None:
                # 标准格式
                if code != 0:
                    return 2, None, f"API错误: code={code}"
                data = result.get("data", {})
                status = data.get("status", "").lower()
                video_url = data.get("video_url")
            else:
                # 直接格式
                status = result.get("status", "").lower()
                video_url = result.get("video_url")

            # 状态映射
            if status in ["completed", "success"]:
                return 1, video_url, None
            elif status in ["failed", "error"]:
                error = result.get("error", "生成失败")
                return 2, None, error
            else:  # pending, processing, queued
                return 0, None, None

    async def download_video(
        self,
        video_url: str,
        save_path: str
    ) -> bool:
        """下载视频"""
        try:
            async with httpx.AsyncClient(
                timeout=120,
                follow_redirects=True,
                trust_env=False
            ) as client:
                async with client.stream("GET", video_url) as response:
                    if response.status_code == 200:
                        with open(save_path, "wb") as f:
                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                f.write(chunk)
                        logger.debug(f"💾 下载成功: {save_path}")
                        return True
                    else:
                        logger.error(f"❌ 下载失败: HTTP {response.status_code}")
                        return False
        except Exception as e:
            logger.error(f"❌ 下载异常: {e}")
            return False

    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """获取模型信息"""
        return self.models.get(model_id)

    def get_all_models(self) -> Dict[str, Dict]:
        """获取所有模型信息"""
        return self.models


# 测试
if __name__ == "__main__":
    async def test():
        api = RembaikeVideoAPI()

        # 测试Kling（最快）
        print("\n测试Kling v2.5 Turbo...")
        success, task_id, error = await api.submit_task(
            model_id="kling-v2.5-turbo",
            prompt="一位年轻女性在现代办公室对镜头微笑",
            duration=5,
            aspect_ratio="9:16"
        )

        if success:
            print(f"✅ 提交成功! 任务ID: {task_id}")

            # 轮询查询
            print("\n轮询查询任务状态...")
            for i in range(30):  # 最多等待5分钟
                await asyncio.sleep(10)
                status, video_url, error = await api.query_task("kling-v2.5-turbo", task_id)

                if status == 1:
                    print(f"✅ 生成成功! URL: {video_url}")

                    # 测试下载
                    print("\n测试下载...")
                    success = await api.download_video(video_url, "./test_video.mp4")
                    if success:
                        print("✅ 下载成功!")
                    break
                elif status == 2:
                    print(f"❌ 生成失败: {error}")
                    break
                else:
                    print(f"⏳ 处理中... ({i+1}/30)")
        else:
            print(f"❌ 提交失败: {error}")

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(test())
