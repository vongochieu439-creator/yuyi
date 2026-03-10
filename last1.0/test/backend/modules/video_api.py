# -*- coding: utf-8 -*-
"""
统一视频生成API
支持速创11个视频模型的统一调用接口
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import asyncio
from typing import Dict, Optional, Tuple
from loguru import logger

from config import SUCHUANG_API_KEY, VIDEO_MODELS


class VideoAPI:
    """统一视频生成API"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or SUCHUANG_API_KEY
        self.models = VIDEO_MODELS
        logger.info("🎥 视频生成API初始化完成")
        logger.info(f"   支持模型: {len(self.models)} 个")

    async def submit_task(
        self,
        model_id: str,
        prompt: str,
        duration: Optional[int] = None,
        aspect_ratio: str = "9:16",
        size: str = "small"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        提交视频生成任务

        Args:
            model_id: 模型ID
            prompt: 提示词
            duration: 时长(秒)，None则使用模型默认
            aspect_ratio: 宽高比
            size: 清晰度

        Returns:
            (成功?, 任务ID, 错误信息)
        """
        if model_id not in self.models:
            return False, None, f"未知模型: {model_id}"

        model_info = self.models[model_id]

        # 确定时长
        if duration is None:
            duration = model_info["duration_options"][0]
        elif duration not in model_info["duration_options"]:
            # 选择最接近的
            duration = min(model_info["duration_options"], key=lambda x: abs(x - duration))

        # 构建请求
        endpoint = model_info["endpoint"]
        url_with_key = f"{endpoint}?key={self.api_key}"

        data = {
            "prompt": prompt,
            "duration": str(duration),
            "aspectRatio": aspect_ratio,
            "size": size
        }

        try:
            async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
                resp = await client.post(url_with_key, data=data)

                if resp.status_code != 200:
                    error_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    logger.error(f"❌ 提交失败: {error_msg}")
                    return False, None, error_msg

                response_data = resp.json()
                code = response_data.get("code")

                if code != 200:
                    error_msg = f"API错误: code={code}, msg={response_data.get('msg', '')}"
                    logger.error(f"❌ {error_msg}")
                    return False, None, error_msg

                task_id = response_data.get("data", {}).get("id")
                if not task_id:
                    return False, None, "未返回任务ID"

                logger.info(f"✅ 任务已提交: {task_id} (模型: {model_id})")
                return True, task_id, None

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 提交异常: {error_msg}")
            return False, None, error_msg

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
            状态: 0=排队, 1=成功, 2=失败, 3=处理中
        """
        if model_id not in self.models:
            return 2, None, f"未知模型: {model_id}"

        model_info = self.models[model_id]
        query_endpoint = model_info["query_endpoint"]
        url_with_params = f"{query_endpoint}?key={self.api_key}&id={task_id}"

        try:
            async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
                resp = await client.get(url_with_params)

                if resp.status_code != 200:
                    return 2, None, f"HTTP {resp.status_code}"

                response_data = resp.json()
                code = response_data.get("code")

                if code != 200:
                    return 2, None, f"API错误: code={code}"

                data = response_data.get("data", {})
                status = data.get("status", 0)
                video_url = data.get("remote_url")

                return status, video_url, None

        except Exception as e:
            return 2, None, str(e)

    async def download_video(
        self,
        video_url: str,
        save_path: str
    ) -> bool:
        """下载视频"""
        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True, trust_env=False) as client:
                async with client.stream("GET", video_url) as response:
                    if response.status_code == 200:
                        with open(save_path, "wb") as f:
                            async for chunk in response.aiter_bytes():
                                f.write(chunk)
                        logger.info(f"💾 下载成功: {save_path}")
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
        api = VideoAPI()

        # 测试提交
        print("\n测试提交任务...")
        success, task_id, error = await api.submit_task(
            model_id="sora2-new",
            prompt="一位年轻女性在现代办公室对镜头微笑",
            duration=10
        )

        if success:
            print(f"✅ 提交成功! 任务ID: {task_id}")

            # 测试查询
            print("\n测试查询任务...")
            for i in range(5):
                await asyncio.sleep(10)
                status, video_url, error = await api.query_task("sora2-new", task_id)
                print(f"状态: {status}")

                if status == 1:
                    print(f"✅ 生成成功! URL: {video_url}")
                    break
                elif status == 2:
                    print(f"❌ 生成失败: {error}")
                    break
        else:
            print(f"❌ 提交失败: {error}")

    asyncio.run(test())
