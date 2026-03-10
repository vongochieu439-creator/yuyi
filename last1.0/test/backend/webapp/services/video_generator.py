# -*- coding: utf-8 -*-
"""
视频生成器 - 将批准的关键帧转换为视频
"""
import uuid
import asyncio
import base64
import mimetypes
import httpx
from pathlib import Path
from typing import Dict, List, Optional, AsyncIterator
from datetime import datetime
from loguru import logger

from ..config import (
    OUTPUTS_DIR,
    KLING_API_KEY,
    KLING_API_BASE_URL
)
from ..models.schemas import ExportStatus
from .provider_factory import get_video_client, get_video_cost_per_unit
from .metadata_manager import MetadataManager


class VideoGenerator:
    """视频生成器 - 通过provider_factory自动选择图生视频API"""

    def __init__(self, api_key: Optional[str] = None, api_base_url: Optional[str] = None):
        self.generation_tasks: Dict[str, Dict] = {}
        self.outputs_dir = Path(OUTPUTS_DIR)
        self.metadata_manager = MetadataManager()

        # 通过工厂获取客户端（支持Seedance和Kling自动切换）
        self.client = get_video_client()
        logger.info(f"视频生成器已初始化，使用: {type(self.client).__name__}")

    async def create_generation_task(
        self,
        project_id: str,
        config: Dict
    ) -> Dict:
        """创建视频生成任务"""
        task_id = str(uuid.uuid4())

        metadata = self.metadata_manager.load_metadata_from_project_id(project_id)
        if not metadata:
            raise FileNotFoundError(f"项目不存在: {project_id}")

        keyframes = metadata.get("keyframes", [])
        if not keyframes:
            raise ValueError("项目没有关键帧数据")

        # 筛选已批准的关键帧
        approved_keyframes = [kf for kf in keyframes if kf.get("status") == "approved"]

        if not approved_keyframes:
            raise ValueError("没有已批准的关键帧，请先批准关键帧")

        # 成本估算：支持按秒计费（Seedance）和按个计费（Kling）
        default_duration = config.get("duration", 5)
        if hasattr(self.client, 'cost_per_second'):
            total_seconds = sum(kf.get("duration", default_duration) for kf in approved_keyframes)
            estimated_cost = self.client.cost_per_second * total_seconds
        else:
            estimated_cost = self.client.calculate_cost(len(approved_keyframes))

        task = {
            "task_id": task_id,
            "project_id": project_id,
            "config": config,
            "status": "pending",
            "progress": 0.0,
            "message": "等待开始生成视频...",
            "total_shots": len(approved_keyframes),
            "completed_shots": 0,
            "estimated_cost": estimated_cost,
            "actual_cost": 0.0,
            "created_at": datetime.now().isoformat()
        }

        self.generation_tasks[task_id] = task
        logger.info(f"创建视频生成任务: {task_id}, 项目: {project_id}, 分镜数: {len(approved_keyframes)}")

        return task

    async def process_generation(self, task_id: str):
        """执行批量视频生成（后台任务，并行）"""
        task = self.generation_tasks.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return

        project_id = task["project_id"]
        config = task["config"]
        project_dir = self.outputs_dir / project_id

        try:
            task["status"] = "processing"
            task["message"] = "准备生成视频..."
            task["progress"] = 0.1
            logger.info(f"开始处理视频生成任务: {task_id}")

            metadata = self.metadata_manager.load_metadata_from_project_id(project_id)
            keyframes = metadata.get("keyframes", [])
            approved_keyframes = [kf for kf in keyframes if kf.get("status") == "approved"]

            if not approved_keyframes:
                raise ValueError("没有已批准的关键帧")

            total = len(approved_keyframes)
            logger.info(f"找到 {total} 个已批准的关键帧，将并行生成")
            task["message"] = f"并行生成 {total} 个视频..."
            task["progress"] = 0.2

            default_duration = config.get("duration", 5)
            model = config.get("model", "kling-v1")
            cfg_scale = config.get("cfg_scale", 0.5)

            # 并行控制：API支持高并发，全部同时提交
            semaphore = asyncio.Semaphore(100)
            lock = asyncio.Lock()
            completed_count = 0
            total_cost = 0.0

            async def generate_one(kf):
                nonlocal completed_count, total_cost
                shot_id = kf.get("shot_id")

                # 从versions数组中查找选中的版本
                selected_version_id = kf.get("selected_version_id")
                selected_version = None
                for v in kf.get("versions", []):
                    if v.get("version_id") == selected_version_id:
                        selected_version = v
                        break
                if not selected_version:
                    for v in kf.get("versions", []):
                        if v.get("image_url"):
                            selected_version = v
                            break

                if not selected_version or not selected_version.get("image_url"):
                    logger.warning(f"分镜 {shot_id} 没有可用的关键帧图片，跳过")
                    return

                raw_image_url = selected_version["image_url"]
                prompt = selected_version.get("prompt", kf.get("visual_description", ""))

                # 本地图片转纯base64（remenbaike代理不接受data:前缀）
                image_for_api = raw_image_url
                if raw_image_url.startswith("/videos/"):
                    local_path = self.outputs_dir / raw_image_url.replace("/videos/", "")
                    if local_path.exists():
                        with open(local_path, "rb") as img_f:
                            b64 = base64.b64encode(img_f.read()).decode()
                        image_for_api = b64
                        logger.info(f"分镜 {shot_id}: 本地图片已转base64 ({len(b64)//1024}KB)")
                    else:
                        logger.warning(f"分镜 {shot_id}: 本地图片不存在 {local_path}")
                        return

                async with semaphore:
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            logger.info(f"[并行] 开始生成视频: shot_{shot_id}" + (f" (重试{attempt})" if attempt > 0 else ""))

                            # 支持每个镜头独立时长
                            shot_duration = kf.get("duration", default_duration)
                            video_url = await self.client.generate_video(
                                image_url=image_for_api,
                                prompt=prompt,
                                duration=int(shot_duration),
                                model=model,
                                cfg_scale=cfg_scale
                            )

                            video_filename = f"scene_{shot_id:03d}.mp4"
                            await self._download_and_save_video(
                                video_url, project_dir, video_filename
                            )

                            cost = self.client.calculate_cost(1)
                            async with lock:
                                completed_count += 1
                                total_cost += cost
                                task["completed_shots"] = completed_count
                                task["actual_cost"] = total_cost
                                task["progress"] = 0.2 + (completed_count / total) * 0.7
                                task["message"] = f"已完成 {completed_count}/{total} 个视频..."

                            logger.info(f"视频生成成功: {video_filename}, 成本: ¥{cost:.2f} ({completed_count}/{total})")
                            break  # 成功，退出重试循环

                        except Exception as e:
                            logger.error(f"生成视频失败 shot_{shot_id} (尝试{attempt+1}/{max_retries}): {e}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(5)  # 等5秒后重试

            # 并行启动所有任务
            tasks = [generate_one(kf) for kf in approved_keyframes]
            await asyncio.gather(*tasks)

            metadata["generation_stage"] = "videos"
            metadata["videos_ready"] = completed_count
            self.metadata_manager.save_metadata_to_project_id(project_id, metadata)

            task["status"] = "completed"
            task["progress"] = 1.0
            task["message"] = f"所有视频生成完成！{completed_count}/{total} 成功，总成本: ¥{total_cost:.2f}"
            logger.info(f"视频生成任务完成: {task_id}, {completed_count}/{total}, 总成本: ¥{total_cost:.2f}")

        except Exception as e:
            logger.error(f"视频生成任务失败 {task_id}: {e}")
            logger.exception("详细错误信息:")
            task["status"] = "failed"
            task["message"] = f"生成失败: {str(e)}"

    async def _download_and_save_video(
        self,
        video_url: str,
        save_dir: Path,
        filename: str
    ) -> Path:
        """下载并保存视频到本地"""
        save_path = save_dir / filename

        try:
            async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                resp = await client.get(video_url)
                resp.raise_for_status()

                with open(save_path, "wb") as f:
                    f.write(resp.content)

                logger.info(f"视频已保存: {save_path}")
                return save_path

        except Exception as e:
            logger.error(f"下载视频失败 {video_url}: {e}")
            raise

    async def get_progress_stream(self, task_id: str) -> AsyncIterator[Dict]:
        """获取进度流（用于WebSocket推送）"""
        logger.info(f"开始推送视频生成进度: {task_id}")

        while True:
            task = self.generation_tasks.get(task_id)

            if not task:
                logger.warning(f"任务不存在: {task_id}")
                break

            yield {
                "task_id": task_id,
                "progress": task["progress"],
                "current_step": task["message"],
                "status": task["status"],
                "completed_shots": task["completed_shots"],
                "total_shots": task["total_shots"],
                "actual_cost": task["actual_cost"]
            }

            if task["status"] in ["completed", "failed"]:
                logger.info(f"任务 {task_id} 已结束，停止推送")
                break

            await asyncio.sleep(0.5)

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        return self.generation_tasks.get(task_id)
