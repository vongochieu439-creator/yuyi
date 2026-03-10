# -*- coding: utf-8 -*-
"""
分镜预览+视频生成服务
metadata.json(shots) ↔ 图片/视频生成的桥梁
"""
import asyncio
import uuid
import httpx
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

from loguru import logger

from ..config import OUTPUTS_DIR, TTS_DEFAULT_VOICE
from .metadata_manager import MetadataManager
from .prompt_engineer import PromptEngineer
from .provider_factory import get_image_client, get_video_client
from .tts_service import TTSService
from .ffmpeg_composer import CinematicComposer


async def _download_file(url: str, output_path: str) -> str:
    """下载URL到本地文件"""
    async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path


class ScriptPreviewService:
    """分镜预览图+视频生成服务"""

    def __init__(self):
        self.tts = TTSService()
        self.composer = CinematicComposer()

    def _get_project_dir(self, project_id: str) -> Path:
        """获取项目目录"""
        for d in OUTPUTS_DIR.iterdir():
            if d.is_dir() and d.name == project_id:
                return d
        raise FileNotFoundError(f"Project {project_id} not found")

    @staticmethod
    def _is_quality_english_prompt(text: str) -> bool:
        """判断是否已经是足够完整的英文 prompt，不需要 AI 优化"""
        if not text:
            return False
        words = text.split()
        non_ascii = sum(1 for c in text if ord(c) > 127)
        return len(words) >= 20 and non_ascii < 5

    async def generate_preview_images(
        self, project_id: str, global_style: str = ""
    ) -> AsyncGenerator[dict, None]:
        """SSE: 为所有shots生成分镜预览图"""
        try:
            project_dir = self._get_project_dir(project_id)
            metadata = MetadataManager.load_metadata(project_dir)
            shots = metadata.get("shots", [])
            product_name = metadata.get("product_name", "") or metadata.get("topic", "")

            if not shots:
                yield {"event": "error", "data": {"message": "没有找到镜头数据"}}
                return

            preview_dir = project_dir / "preview"
            preview_dir.mkdir(exist_ok=True)

            total = len(shots)
            yield {
                "event": "started",
                "data": {
                    "project_id": project_id,
                    "total_frames": total,
                    "message": f"开始生成{total}帧分镜图...",
                },
            }

            # 使用 PromptEngineer 批量生成优化后的提示词
            engineered_prompts: dict = {}
            if global_style or any(
                not self._is_quality_english_prompt(s.get("visual_prompt", "") or s.get("visual_description", ""))
                for s in shots
            ):
                yield {
                    "event": "prompt_engineering",
                    "data": {"message": "正在用 AI 优化生图提示词..."},
                }
                try:
                    engineer = PromptEngineer()
                    engineered_prompts = await engineer.build_batch(
                        shots, global_style=global_style, product_name=product_name
                    )
                    logger.info(f"PromptEngineer 为 {len(engineered_prompts)} 个镜头生成了优化提示词")
                except Exception as e:
                    logger.warning(f"PromptEngineer 失败，将使用原始 prompt: {e}")

            image_client = get_image_client()
            semaphore = asyncio.Semaphore(3)
            results: dict = {}
            queue: asyncio.Queue = asyncio.Queue()

            async def gen_one(shot: dict, idx: int):
                shot_id = shot.get("shot_id", idx + 1)
                # 优先使用 PromptEngineer 生成的优化 prompt
                prompt = engineered_prompts.get(shot_id, "")
                if not prompt:
                    prompt = shot.get("visual_prompt", "") or shot.get("visual_description", "")
                if not prompt:
                    prompt = "product shot, professional lighting, commercial quality"
                out_path = preview_dir / f"frame_{shot_id:03d}.png"

                async with semaphore:
                    try:
                        urls = await image_client.generate_image(prompt=prompt, num_images=1)
                        if urls and urls[0]:
                            await _download_file(urls[0], str(out_path))
                        img_url = f"/videos/{project_id}/preview/frame_{shot_id:03d}.png"
                        results[shot_id] = img_url
                        await queue.put({
                            "shot_id": shot_id,
                            "image_url": img_url,
                            "success": True,
                        })
                    except Exception as e:
                        logger.warning(f"Frame {shot_id} generation failed: {e}")
                        results[shot_id] = None
                        await queue.put({
                            "shot_id": shot_id,
                            "error": str(e),
                            "success": False,
                        })

            # 并发启动所有任务
            tasks = [asyncio.create_task(gen_one(shot, i)) for i, shot in enumerate(shots)]

            async def _wait_all():
                await asyncio.gather(*tasks, return_exceptions=True)
                await queue.put(None)  # sentinel

            asyncio.create_task(_wait_all())

            # 按完成顺序 yield 事件
            completed = 0
            while True:
                result = await queue.get()
                if result is None:
                    break
                completed += 1
                pct = int(completed / total * 100)
                yield {
                    "event": "frame_generated",
                    "data": {
                        **result,
                        "completed": completed,
                        "total": total,
                        "percent": pct,
                    },
                }

            # 更新metadata中的preview图片路径
            for shot in shots:
                sid = shot.get("shot_id", 0)
                if sid in results and results[sid]:
                    shot["preview_image"] = results[sid]
            metadata["shots"] = shots
            MetadataManager.save_metadata(project_dir, metadata)

            yield {
                "event": "complete",
                "data": {
                    "project_id": project_id,
                    "total_generated": sum(1 for v in results.values() if v),
                    "total_failed": sum(1 for v in results.values() if not v),
                    "message": "分镜图生成完成",
                },
            }

        except Exception as e:
            logger.error(f"Preview generation error: {e}")
            yield {"event": "error", "data": {"message": str(e)}}

    async def regenerate_frame_image(
        self,
        project_id: str,
        shot_id: int,
        feedback: Optional[str] = None,
        global_style: str = "",
    ) -> dict:
        """重新生成单帧分镜图（支持用户反馈和全局风格）"""
        project_dir = self._get_project_dir(project_id)
        metadata = MetadataManager.load_metadata(project_dir)
        shots = metadata.get("shots", [])
        product_name = metadata.get("product_name", "") or metadata.get("topic", "")

        shot = None
        for s in shots:
            if s.get("shot_id") == shot_id:
                shot = s
                break
        if not shot:
            raise ValueError(f"Shot {shot_id} not found")

        # 有用户反馈或全局风格时，用 PromptEngineer 优化 prompt
        if feedback or global_style:
            try:
                engineer = PromptEngineer()
                # 将用户反馈临时融入 shot 描述
                shot_copy = dict(shot)
                if feedback:
                    original = shot_copy.get("visual_description", "") or shot_copy.get("visual_prompt", "")
                    shot_copy["visual_description"] = f"{original}. User requirement: {feedback}"
                prompt = await engineer.build_prompt(shot_copy, global_style=global_style, product_name=product_name)
            except Exception as e:
                logger.warning(f"PromptEngineer 单帧失败，使用原始 prompt: {e}")
                prompt = shot.get("visual_description", "") or shot.get("visual_prompt", "")
                if feedback:
                    prompt = f"{prompt}. {feedback}"
        else:
            prompt = shot.get("visual_description", "") or shot.get("visual_prompt", "")

        if not prompt:
            prompt = "product shot, professional lighting, commercial quality"

        preview_dir = project_dir / "preview"
        preview_dir.mkdir(exist_ok=True)
        out_path = preview_dir / f"frame_{shot_id:03d}.png"

        image_client = get_image_client()
        urls = await image_client.generate_image(prompt=prompt, num_images=1)
        if urls and urls[0]:
            await _download_file(urls[0], str(out_path))

        img_url = f"/videos/{project_id}/preview/frame_{shot_id:03d}.png"
        shot["preview_image"] = img_url
        MetadataManager.save_metadata(project_dir, metadata)

        return {"shot_id": shot_id, "image_url": img_url}

    async def update_frame(
        self,
        project_id: str,
        shot_id: int,
        narration: Optional[str] = None,
        visual_description: Optional[str] = None,
    ) -> dict:
        """更新单帧文案/视觉描述"""
        project_dir = self._get_project_dir(project_id)
        metadata = MetadataManager.load_metadata(project_dir)
        shots = metadata.get("shots", [])

        updated = False
        for shot in shots:
            if shot.get("shot_id") == shot_id:
                if narration is not None:
                    shot["narration"] = narration
                if visual_description is not None:
                    shot["visual_description"] = visual_description
                updated = True
                break

        if not updated:
            raise ValueError(f"Shot {shot_id} not found")

        metadata["shots"] = shots
        MetadataManager.save_metadata(project_dir, metadata)
        return {"shot_id": shot_id, "updated": True}

    async def produce_video(self, project_id: str) -> AsyncGenerator[dict, None]:
        """SSE: 图生视频 + TTS + FFmpeg合成"""
        try:
            project_dir = self._get_project_dir(project_id)
            metadata = MetadataManager.load_metadata(project_dir)
            shots = metadata.get("shots", [])

            if not shots:
                yield {"event": "error", "data": {"message": "没有镜头数据"}}
                return

            total_steps = len(shots) + 2  # videos + tts + compose
            current_step = 0

            yield {
                "event": "started",
                "data": {
                    "project_id": project_id,
                    "total_shots": len(shots),
                    "message": "开始视频生产...",
                },
            }

            # Step 1: 图生视频（并行）
            video_dir = project_dir / "videos"
            video_dir.mkdir(exist_ok=True)

            video_client = get_video_client()
            semaphore = asyncio.Semaphore(3)
            scene_data = []

            # 镜头运动 → Kling cfg_scale（控制运镜幅度）
            _camera_to_cfg = {
                "static": 0.3, "breathe": 0.4,
                "zoom_in": 0.5, "zoom_out": 0.5, "focus_in": 0.5, "focus_out": 0.5,
                "pan_left": 0.6, "pan_right": 0.6, "slow_up": 0.6, "slow_down": 0.6,
                "diagonal": 0.7, "dolly": 0.7, "handheld": 0.65, "shake": 0.8,
            }

            async def gen_video(shot: dict, idx: int):
                async with semaphore:
                    import base64
                    shot_id = shot.get("shot_id", idx + 1)
                    img_path = project_dir / "preview" / f"frame_{shot_id:03d}.png"
                    vid_path = video_dir / f"scene_{shot_id:03d}.mp4"

                    if not img_path.exists():
                        logger.warning(f"No preview image for shot {shot_id}, skipping video")
                        return {"shot_id": shot_id, "video_path": None, "image_path": None}

                    try:
                        # 纯 base64（remenbaike 代理不接受 data: 前缀）
                        with open(str(img_path), "rb") as f:
                            img_b64 = base64.b64encode(f.read()).decode()

                        # 口播文案作为运镜 prompt，引导视频动态
                        narration = shot.get("narration", "")
                        visual = shot.get("visual_prompt", "") or shot.get("visual_description", "")
                        prompt_parts = []
                        if visual:
                            prompt_parts.append(visual[:150])
                        if narration:
                            prompt_parts.append(f"scene: {narration[:80]}")
                        prompt = ", ".join(prompt_parts) if prompt_parts else None

                        # 运镜映射
                        camera = shot.get("camera_movement", "static")
                        cfg_scale = _camera_to_cfg.get(camera, 0.5)

                        # Kling 支持 5s 或 10s
                        raw_dur = int(shot.get("duration", 5))
                        duration = 10 if raw_dur >= 8 else 5

                        video_url = await video_client.generate_video(
                            image_url=img_b64,
                            prompt=prompt,
                            duration=duration,
                            cfg_scale=cfg_scale,
                        )
                        if video_url:
                            await _download_file(video_url, str(vid_path))
                        return {
                            "shot_id": shot_id,
                            "video_path": str(vid_path) if vid_path.exists() else None,
                            "image_path": str(img_path),
                        }
                    except Exception as e:
                        logger.warning(f"Video gen failed for shot {shot_id}: {e}")
                        return {"shot_id": shot_id, "video_path": None, "image_path": str(img_path)}

            vid_queue: asyncio.Queue = asyncio.Queue()

            async def gen_video_task(shot: dict, idx: int):
                result = await gen_video(shot, idx)
                await vid_queue.put(result)

            vid_tasks = [asyncio.create_task(gen_video_task(shot, i)) for i, shot in enumerate(shots)]

            async def _wait_videos():
                await asyncio.gather(*vid_tasks, return_exceptions=True)
                await vid_queue.put(None)

            asyncio.create_task(_wait_videos())

            shot_count = len(shots)
            while True:
                result = await vid_queue.get()
                if result is None:
                    break
                scene_data.append(result)
                current_step += 1
                pct = int(current_step / total_steps * 100)
                yield {
                    "event": "video_generated",
                    "data": {
                        "shot_id": result["shot_id"],
                        "has_video": result["video_path"] is not None,
                        "percent": pct,
                        "message": f"视频片段 {current_step}/{shot_count} 完成",
                    },
                }

            # Step 2: TTS配音
            yield {
                "event": "progress",
                "data": {"step": "tts", "message": "正在生成配音...", "percent": int(current_step / total_steps * 100)},
            }

            full_narration = " ".join(
                s.get("narration", "") for s in shots if s.get("narration")
            )
            narration_path = str(project_dir / "narration.mp3")
            if full_narration.strip():
                try:
                    await self.tts.generate_full_narration(
                        full_text=full_narration,
                        output_path=narration_path,
                        voice=TTS_DEFAULT_VOICE,
                    )
                except Exception as e:
                    logger.warning(f"TTS failed: {e}")
                    narration_path = None
            else:
                narration_path = None

            current_step += 1

            # Step 3: FFmpeg合成
            yield {
                "event": "progress",
                "data": {"step": "compose", "message": "正在合成最终视频...", "percent": int(current_step / total_steps * 100)},
            }

            # 按shot_id排序
            scene_data.sort(key=lambda x: x["shot_id"])
            compose_scenes = []
            for sd in scene_data:
                shot = next((s for s in shots if s.get("shot_id") == sd["shot_id"]), {})
                compose_scenes.append({
                    "video_path": sd.get("video_path"),
                    "image_path": sd.get("image_path"),
                    "duration": shot.get("duration", 5),
                    "camera": shot.get("camera_movement", "static"),
                    "narration": shot.get("narration", ""),
                    "mood": shot.get("mood", "neutral"),
                })

            output_path = str(project_dir / "final_video.mp4")
            try:
                await self.composer.compose(
                    scenes=compose_scenes,
                    narration_audio=narration_path,
                    output_path=output_path,
                    style=metadata.get("style", "cinematic"),
                )
                video_url = f"/videos/{project_id}/final_video.mp4"
            except Exception as e:
                logger.error(f"Composition failed: {e}")
                yield {"event": "error", "data": {"message": f"视频合成失败: {e}"}}
                return

            # 更新metadata
            metadata["video_url"] = video_url
            metadata["generation_stage"] = "export"
            MetadataManager.save_metadata(project_dir, metadata)

            yield {
                "event": "complete",
                "data": {
                    "project_id": project_id,
                    "video_url": video_url,
                    "message": "视频生产完成！",
                },
            }

        except Exception as e:
            logger.error(f"Video production error: {e}")
            yield {"event": "error", "data": {"message": str(e)}}
