# -*- coding: utf-8 -*-
"""
关键帧生成器 - 使用nanobanana API生成关键帧图片
"""
import json
import uuid
import asyncio
import httpx
from pathlib import Path
from typing import Dict, List, Optional, AsyncIterator, Tuple
from datetime import datetime
from loguru import logger

from ..config import (
    OUTPUTS_DIR,
    NANOBANANA_API_KEY,
    NANOBANANA_API_BASE_URL,
    KEYFRAME_NUM_VERSIONS
)
from ..models.schemas import (
    KeyframeStatus, KeyframeInfo, KeyframeVersion,
    KeyframeGenerationTask, KeyframeGenerationConfig
)
from .provider_factory import get_image_client


class KeyframeGenerator:
    """关键帧生成器 - 通过provider_factory自动选择图片生成API"""

    def __init__(self, api_key: Optional[str] = None, api_base_url: Optional[str] = None):
        self.generation_tasks: Dict[str, Dict] = {}  # 存储生成任务状态
        self.outputs_dir = Path(OUTPUTS_DIR)

        # 通过工厂获取客户端（支持Seedream和NanoBanana自动切换）
        self.client = get_image_client()
        logger.info(f"关键帧生成器已初始化，使用: {type(self.client).__name__}")

    async def create_generation_task(
        self,
        project_id: str,
        shot_data: List[Dict],
        config: KeyframeGenerationConfig
    ) -> KeyframeGenerationTask:
        """创建批量关键帧生成任务"""
        task_id = str(uuid.uuid4())

        # 计算预估成本
        estimated_cost = self._estimate_cost(len(shot_data), config)

        task = KeyframeGenerationTask(
            task_id=task_id,
            project_id=project_id,
            status="pending",
            total_shots=len(shot_data),
            completed_shots=0,
            progress=0.0,
            message="等待开始生成关键帧...",
            estimated_cost=estimated_cost,
            actual_cost=0.0
        )

        self.generation_tasks[task_id] = task.model_dump()
        logger.info(f"创建关键帧生成任务: {task_id}, 项目: {project_id}, 分镜数: {len(shot_data)}")

        return task

    async def process_generation(
        self,
        task_id: str,
        shot_data: List[Dict],
        config: KeyframeGenerationConfig
    ):
        """
        执行批量关键帧生成（后台任务）- 并发版本
        使用信号量控制并发数，每完成一个立即写入metadata.json
        """
        task = self.generation_tasks.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return

        project_id = task["project_id"]
        project_dir = self.outputs_dir / project_id
        keyframes_dir = project_dir / "keyframes"
        keyframes_dir.mkdir(exist_ok=True)

        # 加载metadata
        metadata_path = project_dir / "metadata.json"
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        # 获取产品图信息
        product_images = metadata.get("product_images", [])

        # 预编码产品图（只做一次）
        product_img_b64 = None
        if product_images:
            raw_url = product_images[0]
            if raw_url and raw_url.startswith("/videos/"):
                local_path = self.outputs_dir / raw_url.replace("/videos/", "")
                if local_path.exists():
                    import base64
                    import mimetypes
                    mime_type = mimetypes.guess_type(str(local_path))[0] or "image/jpeg"
                    with open(local_path, "rb") as img_f:
                        b64 = base64.b64encode(img_f.read()).decode()
                    product_img_b64 = f"data:{mime_type};base64,{b64}"
                    logger.info(f"产品图已预编码: {local_path} ({len(b64)//1024}KB)")
            elif raw_url and raw_url.startswith("http"):
                product_img_b64 = raw_url

        try:
            task["status"] = "processing"
            task["message"] = "开始生成关键帧..."
            logger.info(f"开始处理关键帧生成任务: {task_id}")

            # 结果容器（按索引存放，保证顺序）
            keyframes_results = [None] * len(shot_data)
            total_cost = 0.0
            completed_count = 0
            failed_count = 0
            lock = asyncio.Lock()

            # 并发信号量（最多3个同时生成）
            semaphore = asyncio.Semaphore(3)

            async def generate_one(idx: int, shot: Dict):
                nonlocal total_cost, completed_count, failed_count

                async with semaphore:
                    shot_id = shot.get("id", shot.get("shot_id", idx + 1))
                    visual_desc = shot.get("visual_description", "")
                    shot_type = shot.get("shot_type", "broll")
                    use_product_image = shot.get("use_product_image", False)

                    # 优化提示词
                    prompt = visual_desc
                    if config.optimize_prompt:
                        prompt = await self._optimize_prompt(visual_desc, shot_type)

                    # 产品图
                    img_url = None
                    if use_product_image and product_img_b64 and shot_type in ("product", "hands_on"):
                        img_url = product_img_b64

                    try:
                        image_url, cost = await self._generate_image(
                            prompt=prompt,
                            model=config.model,
                            quality=config.quality,
                            aspect_ratio=config.aspect_ratio,
                            img_url=img_url
                        )

                        filename = f"keyframe_{shot_id:03d}_v1.jpg"
                        await self._download_and_save_image(image_url, keyframes_dir, filename)

                        local_image_url = f"/videos/{project_id}/keyframes/{filename}"
                        keyframe_info = {
                            "shot_id": shot_id,
                            "status": "completed",
                            "versions": [
                                {
                                    "version_id": 1,
                                    "image_url": local_image_url,
                                    "prompt": prompt,
                                    "model": config.model,
                                    "quality_score": None,
                                    "is_selected": True,
                                    "cost": cost,
                                    "created_at": datetime.now().isoformat()
                                }
                            ],
                            "selected_version_id": 1,
                            "visual_description": visual_desc,
                            "narration": shot.get("narration", ""),
                            "duration": shot.get("duration", 5.0)
                        }

                        async with lock:
                            keyframes_results[idx] = keyframe_info
                            total_cost += cost
                            completed_count += 1
                            task["actual_cost"] = total_cost
                            task["completed_shots"] = completed_count + failed_count
                            task["progress"] = (completed_count + failed_count) / len(shot_data) * 0.9
                            task["message"] = f"已完成 {completed_count}/{len(shot_data)} 个关键帧..."

                            # 实时写入metadata
                            current_kfs = [kf for kf in keyframes_results if kf is not None]
                            metadata["keyframes"] = current_kfs
                            with open(metadata_path, "w", encoding="utf-8") as f:
                                json.dump(metadata, f, ensure_ascii=False, indent=2)

                        logger.info(f"关键帧生成成功: shot_{shot_id}, 成本: ¥{cost:.2f}")

                    except Exception as e:
                        logger.error(f"生成关键帧失败 shot_{shot_id}: {e}")
                        keyframe_info = {
                            "shot_id": shot_id,
                            "status": "failed",
                            "versions": [],
                            "selected_version_id": None,
                            "visual_description": visual_desc,
                            "narration": shot.get("narration", ""),
                            "duration": shot.get("duration", 5.0)
                        }
                        async with lock:
                            keyframes_results[idx] = keyframe_info
                            failed_count += 1
                            task["completed_shots"] = completed_count + failed_count
                            task["progress"] = (completed_count + failed_count) / len(shot_data) * 0.9

            # 并发启动所有任务
            tasks = [generate_one(idx, shot) for idx, shot in enumerate(shot_data)]
            await asyncio.gather(*tasks)

            # 完成: 更新generation_stage
            final_kfs = [kf for kf in keyframes_results if kf is not None]
            metadata["keyframes"] = final_kfs
            metadata["generation_stage"] = "keyframes"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            task["status"] = "completed"
            task["progress"] = 1.0
            task["message"] = f"关键帧生成完成！成功 {completed_count}/{len(shot_data)} 个，总成本: ¥{total_cost:.2f}"
            logger.info(f"关键帧生成任务完成: {task_id}, 成功{completed_count}, 失败{failed_count}, 总成本: ¥{total_cost:.2f}")

        except Exception as e:
            logger.error(f"关键帧生成任务失败 {task_id}: {e}")
            logger.exception("详细错误信息:")
            task["status"] = "failed"
            task["message"] = f"生成失败: {str(e)}"

    async def regenerate_keyframe(
        self,
        project_id: str,
        shot_id: int,
        version_count: int = 3,
        config: Optional[KeyframeGenerationConfig] = None
    ) -> List[KeyframeVersion]:
        """重新生成单个关键帧（生成多个版本）"""
        if config is None:
            config = KeyframeGenerationConfig()

        project_dir = self.outputs_dir / project_id
        keyframes_dir = project_dir / "keyframes"

        # 从metadata读取分镜信息
        visual_desc = f"Shot {shot_id} visual description"
        metadata_path = project_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            for shot in metadata.get("shots", []):
                if shot.get("id") == shot_id:
                    visual_desc = shot.get("visual_description", visual_desc)
                    break

        versions = []

        for version_id in range(1, version_count + 1):
            try:
                # 优化提示词
                prompt = visual_desc
                if config.optimize_prompt:
                    prompt = await self._optimize_prompt(visual_desc)

                # 生成图片
                image_url, cost = await self._generate_image(
                    prompt=prompt,
                    model=config.model,
                    quality=config.quality,
                    aspect_ratio=config.aspect_ratio
                )

                # 下载保存
                saved_path = await self._download_and_save_image(
                    image_url,
                    keyframes_dir,
                    f"keyframe_{shot_id:03d}_v{version_id}.jpg"
                )

                # 创建版本对象
                version = KeyframeVersion(
                    version_id=version_id,
                    image_url=f"/videos/{project_id}/keyframes/keyframe_{shot_id:03d}_v{version_id}.jpg",
                    prompt=prompt,
                    model=config.model,
                    quality_score=None,
                    is_selected=False,
                    cost=cost
                )
                versions.append(version)

                logger.info(f"生成关键帧版本: shot_{shot_id}_v{version_id}, 成本: ¥{cost:.2f}")

            except Exception as e:
                logger.error(f"生成版本失败 shot_{shot_id}_v{version_id}: {e}")

        # 更新metadata中的keyframes
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            keyframes = metadata.get("keyframes", [])
            for kf in keyframes:
                if kf.get("shot_id") == shot_id:
                    kf["versions"] = [v.model_dump() for v in versions]
                    kf["status"] = "completed"
                    if versions:
                        kf["selected_version_id"] = 1
                        versions[0].is_selected = True
                    break
            metadata["keyframes"] = keyframes
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)

        return versions

    async def _generate_image(
        self,
        prompt: str,
        model: str = "nano-banana",
        quality: str = "high",
        aspect_ratio: str = "16:9",
        img_url: Optional[str] = None
    ) -> Tuple[str, float]:
        """调用nanobanana API生成图片"""
        logger.info(f"调用NanoBanana API生成图片: prompt={prompt[:50]}...")

        try:
            images = await self.client.generate_image(
                prompt=prompt,
                num_images=1,
                img_url=img_url
            )

            if not images:
                raise RuntimeError("未生成图片")

            image_url = images[0]
            cost = self.client.calculate_cost(1)

            logger.info(f"图片生成成功: {image_url[:80]}..., 成本: ¥{cost:.2f}")
            return image_url, cost

        except Exception as e:
            logger.error(f"调用NanoBanana API失败: {e}")
            raise

    async def _optimize_prompt(
        self,
        original_prompt: str,
        shot_type: Optional[str] = None
    ) -> str:
        """使用规则增强提示词"""
        enhanced = f"{original_prompt}, high quality, professional lighting, cinematic composition, 4K, detailed"
        logger.info(f"提示词优化: {original_prompt[:30]}... -> {enhanced[:30]}...")
        return enhanced

    async def _download_and_save_image(
        self,
        image_url: str,
        save_dir: Path,
        filename: str
    ) -> Path:
        """下载并保存图片到本地"""
        save_path = save_dir / filename

        try:
            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                resp = await client.get(image_url)
                resp.raise_for_status()

                with open(save_path, "wb") as f:
                    f.write(resp.content)

                logger.info(f"图片已保存: {save_path}")
                return save_path

        except Exception as e:
            logger.error(f"下载图片失败 {image_url}: {e}")
            raise

    def _estimate_cost(
        self,
        shot_count: int,
        config: KeyframeGenerationConfig
    ) -> float:
        """估算生成成本"""
        model_prices = {
            "flux-pro": 0.05,
            "midjourney": 0.10,
            "sdxl": 0.02
        }

        unit_price = model_prices.get(config.model, 0.1)
        total_cost = shot_count * unit_price

        return round(total_cost, 2)

    async def get_progress_stream(
        self,
        task_id: str
    ) -> AsyncIterator[Dict]:
        """获取进度流（用于WebSocket推送）"""
        logger.info(f"开始推送关键帧生成进度: {task_id}")

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
