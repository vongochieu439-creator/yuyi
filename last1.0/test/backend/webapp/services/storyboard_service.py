# -*- coding: utf-8 -*-
"""
分镜审核编排服务
负责分镜生成 → 图片生成 → 审核 → 重新生成 → 视频制作的完整流程
"""
import asyncio
import base64
import json
import time
import uuid
import httpx
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from loguru import logger

from ..config import (
    COMIC_DRAMA_OUTPUT_DIR, COMIC_DRAMA_SCENE_DURATION,
    TTS_DEFAULT_VOICE, GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL,
)
from .storyboard_director import StoryboardDirector
from .provider_factory import get_image_client, get_video_client, get_image_cost_per_unit, get_video_cost_per_unit
from .tts_service import TTSService
from .ffmpeg_composer import CinematicComposer


# 项目缓存 (project_id -> storyboard data)
_storyboard_cache: Dict[str, dict] = {}


class StoryboardService:
    """分镜审核编排服务"""

    def __init__(self):
        self.director = StoryboardDirector()
        self.tts = TTSService(default_voice=TTS_DEFAULT_VOICE)
        self.composer = CinematicComposer(fps=30)
        self.output_base = Path(COMIC_DRAMA_OUTPUT_DIR)
        self.output_base.mkdir(parents=True, exist_ok=True)

    # ==================== 生成分镜 ====================

    async def generate_storyboard(
        self,
        user_input: str,
        style: str = "cinematic",
        hook_type: Optional[str] = None,
        total_duration: int = 45,
        character_description: str = "",
        product_detail: str = "",
    ) -> AsyncGenerator[dict, None]:
        """
        SSE流式生成卖货分镜脚本（多Agent协作）

        Events:
        - started: {project_id}
        - phase_complete: {phase, message} — director/screenwriter/producer
        - storyboard_ready: {storyboard}
        - error: {message}
        """
        project_id = f"sb_{int(time.time())}_{str(uuid.uuid4())[:6]}"
        project_dir = self.output_base / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        yield {"event": "started", "data": {"project_id": project_id, "message": "Director Agent 正在分析产品和市场..."}}

        try:
            phases_data = {}

            async def on_agent(agent_name: str, data: dict):
                phases_data[agent_name] = data

            storyboard = await self.director.generate_storyboard(
                product_name=user_input,
                product_detail=product_detail or "",
                industry=character_description or "",  # 复用为行业字段
                target_duration=total_duration,
                style=style,
                on_agent_complete=on_agent,
            )

            # 通知各Agent完成
            agent_labels = {
                "director": "Director 策略制定完成",
                "screenwriter": "Screenwriter 分镜撰写完成",
                "producer": "Producer 质量审核完成",
            }
            for agent_name, label in agent_labels.items():
                if agent_name in phases_data:
                    yield {
                        "event": "phase_complete",
                        "data": {"phase": agent_name, "message": label},
                    }

            # 添加项目信息
            storyboard["project_id"] = project_id
            storyboard["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

            # 保存到文件和缓存
            self._save_storyboard(project_id, storyboard)

            yield {
                "event": "storyboard_ready",
                "data": storyboard,
            }

        except Exception as e:
            logger.error(f"分镜生成失败: {e}")
            import traceback
            traceback.print_exc()
            yield {"event": "error", "data": {"message": f"分镜生成失败: {str(e)}"}}

    # ==================== 图片生成 ====================

    async def generate_images(self, project_id: str) -> AsyncGenerator[dict, None]:
        """
        为分镜的所有帧并发生成图片

        Events:
        - image_generating: {frame_id}
        - image_generated: {frame_id, image_url}
        - image_failed: {frame_id, error}
        - images_complete: {total, success, failed}
        """
        storyboard = self._load_storyboard(project_id)
        if not storyboard:
            yield {"event": "error", "data": {"message": f"项目不存在: {project_id}"}}
            return

        frames = storyboard.get("frames", [])
        if not frames:
            yield {"event": "error", "data": {"message": "分镜没有帧数据"}}
            return

        project_dir = self.output_base / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        image_client = get_image_client()
        char_desc = storyboard.get("character", {}).get("description", "")
        sem = asyncio.Semaphore(4)

        success_count = 0
        failed_count = 0
        results_queue = asyncio.Queue()

        async def gen_one(frame: dict):
            nonlocal success_count, failed_count
            fid = frame["frame_id"]
            prompt = frame.get("visual_prompt", "")

            # 注入角色描述确保一致性
            if char_desc and char_desc.lower() not in prompt.lower():
                prompt = f"{char_desc}. {prompt}"

            await results_queue.put({"event": "image_generating", "data": {"frame_id": fid}})

            async with sem:
                for attempt in range(2):
                    try:
                        urls = await image_client.generate_image(prompt, num_images=1)
                        if urls:
                            img_path = project_dir / f"frame_{fid:02d}.png"
                            await self._download_file(urls[0], str(img_path))
                            image_url = f"/comic-drama/output/{project_id}/frame_{fid:02d}.png"

                            # 更新frame
                            frame["image_url"] = image_url
                            frame["status"] = "generated"

                            success_count += 1
                            await results_queue.put({
                                "event": "image_generated",
                                "data": {"frame_id": fid, "image_url": image_url},
                            })
                            return
                    except Exception as e:
                        logger.error(f"帧{fid}图片生成失败(尝试{attempt+1}): {e}")
                        if attempt == 0:
                            await asyncio.sleep(2)

                frame["status"] = "pending"
                failed_count += 1
                await results_queue.put({
                    "event": "image_failed",
                    "data": {"frame_id": fid, "error": "生成失败"},
                })

        # 启动所有生成任务
        tasks = [asyncio.create_task(gen_one(f)) for f in frames]

        # 发送sentinel
        async def wait_all():
            await asyncio.gather(*tasks)
            await results_queue.put(None)  # sentinel

        asyncio.create_task(wait_all())

        # 逐个yield事件
        while True:
            item = await results_queue.get()
            if item is None:
                break
            yield item

        # 保存更新后的storyboard
        self._save_storyboard(project_id, storyboard)

        yield {
            "event": "images_complete",
            "data": {
                "total": len(frames),
                "success": success_count,
                "failed": failed_count,
            },
        }

    # ==================== 审核 ====================

    def review_frames(self, project_id: str, actions: List[dict]) -> dict:
        """
        批量审核帧

        Args:
            actions: [{"frame_id": 1, "action": "approve"/"reject", "feedback": "..."}]

        Returns:
            {"approved": [...], "rejected": [...]}
        """
        storyboard = self._load_storyboard(project_id)
        if not storyboard:
            raise FileNotFoundError(f"项目不存在: {project_id}")

        frames_map = {f["frame_id"]: f for f in storyboard.get("frames", [])}
        approved = []
        rejected = []

        for action in actions:
            fid = action["frame_id"]
            frame = frames_map.get(fid)
            if not frame:
                continue

            if action["action"] == "approve":
                frame["status"] = "approved"
                frame["feedback"] = None
                approved.append(fid)
            elif action["action"] == "reject":
                frame["status"] = "rejected"
                frame["feedback"] = action.get("feedback", "")
                rejected.append(fid)

        self._save_storyboard(project_id, storyboard)
        return {"approved": approved, "rejected": rejected}

    # ==================== 单帧重新生成 ====================

    async def regenerate_frame(
        self, project_id: str, frame_id: int, feedback: Optional[str] = None
    ) -> dict:
        """
        用反馈+相邻帧参考重新生成单帧

        Returns:
            {"frame_id": ..., "image_url": ..., "status": ...}
        """
        storyboard = self._load_storyboard(project_id)
        if not storyboard:
            raise FileNotFoundError(f"项目不存在: {project_id}")

        frames = storyboard.get("frames", [])
        target_frame = None
        for f in frames:
            if f["frame_id"] == frame_id:
                target_frame = f
                break

        if not target_frame:
            raise ValueError(f"帧不存在: {frame_id}")

        # 标记为重新生成中
        target_frame["status"] = "regenerating"
        self._save_storyboard(project_id, storyboard)

        # 构建增强prompt
        prompt = target_frame.get("visual_prompt", "")
        char_desc = storyboard.get("character", {}).get("description", "")
        if char_desc and char_desc.lower() not in prompt.lower():
            prompt = f"{char_desc}. {prompt}"

        # 加入反馈指导
        if feedback:
            prompt = f"{prompt}. User feedback: {feedback}"

        # 生成新图片
        image_client = get_image_client()
        project_dir = self.output_base / project_id

        try:
            # 如果支持图生图编辑且有旧图，用旧图作参考
            old_image = target_frame.get("image_url")
            img_ref = None
            if old_image:
                local_path = project_dir / f"frame_{frame_id:02d}.png"
                if local_path.exists():
                    with open(local_path, "rb") as f:
                        img_ref = base64.b64encode(f.read()).decode()

            urls = await image_client.generate_image(
                prompt=prompt,
                num_images=1,
                img_url=img_ref,
            )

            if urls:
                img_path = project_dir / f"frame_{frame_id:02d}.png"
                await self._download_file(urls[0], str(img_path))
                image_url = f"/comic-drama/output/{project_id}/frame_{frame_id:02d}.png"

                target_frame["image_url"] = image_url
                target_frame["status"] = "generated"
                target_frame["feedback"] = feedback
            else:
                target_frame["status"] = "generated"  # 保留旧图
                image_url = target_frame.get("image_url", "")

        except Exception as e:
            logger.error(f"重新生成帧{frame_id}失败: {e}")
            target_frame["status"] = "generated"
            image_url = target_frame.get("image_url", "")

        self._save_storyboard(project_id, storyboard)

        return {
            "frame_id": frame_id,
            "image_url": image_url,
            "status": target_frame["status"],
        }

    # ==================== 视频制作 ====================

    async def produce_video(self, project_id: str) -> AsyncGenerator[dict, None]:
        """
        从已审核帧生成最终视频

        Events:
        - producing_started
        - video_generating: {frame_id}
        - video_generated: {frame_id}
        - composing: {message}
        - produce_complete: {video_url, elapsed}
        - error: {message}
        """
        storyboard = self._load_storyboard(project_id)
        if not storyboard:
            yield {"event": "error", "data": {"message": f"项目不存在: {project_id}"}}
            return

        frames = storyboard.get("frames", [])
        approved_frames = [f for f in frames if f.get("status") in ("approved", "generated")]

        if not approved_frames:
            yield {"event": "error", "data": {"message": "没有已审核的帧"}}
            return

        project_dir = self.output_base / project_id
        start_time = time.time()

        yield {"event": "producing_started", "data": {"total_frames": len(approved_frames)}}

        try:
            # Step 1: 图生视频
            video_client = get_video_client()
            sem = asyncio.Semaphore(4)
            video_paths = {}

            async def gen_video(frame):
                fid = frame["frame_id"]
                img_path = project_dir / f"frame_{fid:02d}.png"

                if not img_path.exists():
                    logger.warning(f"帧{fid}图片不存在，跳过")
                    return

                # 准备图片参数
                image_url = frame.get("image_url", "")
                if image_url.startswith("/"):
                    with open(img_path, "rb") as f:
                        image_for_api = base64.b64encode(f.read()).decode()
                else:
                    image_for_api = image_url

                prompt = frame.get("visual_prompt", "")[:200]
                duration = int(frame.get("duration", 5))

                async with sem:
                    for attempt in range(2):
                        try:
                            video_url = await video_client.generate_video(
                                image_url=image_for_api,
                                prompt=prompt,
                                duration=duration,
                            )
                            if video_url:
                                vpath = project_dir / f"video_{fid:02d}.mp4"
                                await self._download_file(video_url, str(vpath))
                                video_paths[fid] = str(vpath)
                                frame["video_url"] = f"/comic-drama/output/{project_id}/video_{fid:02d}.mp4"
                                return
                        except Exception as e:
                            logger.error(f"帧{fid}视频生成失败(尝试{attempt+1}): {e}")
                            if attempt == 0:
                                await asyncio.sleep(3)

            # 通知每个帧开始
            for frame in approved_frames:
                yield {"event": "video_generating", "data": {"frame_id": frame["frame_id"]}}

            tasks = [gen_video(f) for f in approved_frames]
            await asyncio.gather(*tasks)

            for frame in approved_frames:
                fid = frame["frame_id"]
                has_video = fid in video_paths
                yield {"event": "video_generated", "data": {"frame_id": fid, "has_video": has_video}}

            # Step 2: TTS
            yield {"event": "composing", "data": {"message": "正在生成配音..."}}
            full_narration = "。".join(
                f.get("narration", "") for f in approved_frames if f.get("narration")
            )
            narration_path = str(project_dir / "narration.mp3")
            await self.tts.generate_full_narration(
                full_text=full_narration,
                output_path=narration_path,
            )

            # Step 3: FFmpeg合成
            yield {"event": "composing", "data": {"message": "正在合成最终视频..."}}

            compose_scenes = []
            for frame in approved_frames:
                fid = frame["frame_id"]
                vpath = video_paths.get(fid)
                ipath = str(project_dir / f"frame_{fid:02d}.png")
                compose_scenes.append({
                    "video_path": vpath,
                    "image_path": ipath if Path(ipath).exists() else None,
                    "duration": frame.get("duration", 5.0),
                    "camera": frame.get("camera_movement", "static"),
                    "narration": frame.get("narration", ""),
                    "mood": frame.get("mood", "epic"),
                })

            # 选择BGM
            bgm_path = self._select_bgm("epic")

            output_video = str(project_dir / "final.mp4")
            await self.composer.compose(
                scenes=compose_scenes,
                narration_audio=narration_path if Path(narration_path).exists() else None,
                bgm_path=bgm_path,
                output_path=output_video,
                style=storyboard.get("style", "cinematic"),
            )

            elapsed = round(time.time() - start_time, 1)
            video_url = f"/comic-drama/output/{project_id}/final.mp4"

            # 保存更新
            storyboard["video_url"] = video_url
            storyboard["elapsed_seconds"] = elapsed
            self._save_storyboard(project_id, storyboard)

            yield {
                "event": "produce_complete",
                "data": {
                    "video_url": video_url,
                    "elapsed_seconds": elapsed,
                    "project_id": project_id,
                },
            }

        except Exception as e:
            logger.error(f"视频制作失败: {e}")
            import traceback
            traceback.print_exc()
            yield {"event": "error", "data": {"message": f"视频制作失败: {str(e)}"}}

    # ==================== 查询/成本 ====================

    def get_storyboard(self, project_id: str) -> Optional[dict]:
        """获取分镜数据"""
        return self._load_storyboard(project_id)

    def get_cost_estimate(self, project_id: str) -> dict:
        """获取成本估算"""
        storyboard = self._load_storyboard(project_id)
        if not storyboard:
            return {"error": "项目不存在"}

        frames = storyboard.get("frames", [])
        image_cost = get_image_cost_per_unit() * len(frames)
        video_cost = sum(
            get_video_cost_per_unit(int(f.get("duration", 5))) for f in frames
        )
        tts_cost = 0  # edge-tts免费

        return {
            "image_count": len(frames),
            "image_unit_cost": get_image_cost_per_unit(),
            "image_total": round(image_cost, 2),
            "video_total_seconds": sum(f.get("duration", 5) for f in frames),
            "video_total": round(video_cost, 2),
            "tts_cost": tts_cost,
            "grand_total": round(image_cost + video_cost + tts_cost, 2),
        }

    # ==================== 内部工具 ====================

    def _save_storyboard(self, project_id: str, data: dict):
        """保存分镜数据"""
        _storyboard_cache[project_id] = data
        project_dir = self.output_base / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        storyboard_file = project_dir / "storyboard.json"
        with open(storyboard_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def _load_storyboard(self, project_id: str) -> Optional[dict]:
        """加载分镜数据"""
        if project_id in _storyboard_cache:
            return _storyboard_cache[project_id]

        storyboard_file = self.output_base / project_id / "storyboard.json"
        if storyboard_file.exists():
            with open(storyboard_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            _storyboard_cache[project_id] = data
            return data

        return None

    async def _download_file(self, url: str, save_path: str):
        """下载文件"""
        try:
            async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                Path(save_path).write_bytes(resp.content)
        except Exception as e:
            logger.error(f"文件下载失败: {url}, {e}")
            raise

    def _select_bgm(self, bgm_style: str) -> Optional[str]:
        """选择BGM"""
        from ..config import PROJECT_ROOT
        bgm_dir = PROJECT_ROOT / "webapp" / "static" / "bgm"
        if not bgm_dir.exists():
            bgm_dir = Path(__file__).parent.parent / "static" / "bgm"
        bgm_file = bgm_dir / f"{bgm_style}.mp3"
        if bgm_file.exists():
            return str(bgm_file)
        for f in bgm_dir.glob("*.mp3"):
            return str(f)
        return None
