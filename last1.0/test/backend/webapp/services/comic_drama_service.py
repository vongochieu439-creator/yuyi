# -*- coding: utf-8 -*-
"""
漫剧一键生成主编排服务 V2
Pipeline: Gemini分镜 → 并行(NanoBanana图片 + TTS) → Kling图生视频 → FFmpeg合成
"""
import asyncio
import base64
import copy
import json
import re
import time
import uuid
import httpx
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from loguru import logger

from ..config import (
    GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL,
    COMIC_DRAMA_OUTPUT_DIR, COMIC_DRAMA_SCENES_COUNT,
    COMIC_DRAMA_SCENE_DURATION, TTS_DEFAULT_VOICE,
)
from .comic_drama_prompts import (
    get_storyboard_prompt, get_style_suffix,
    FALLBACK_STORYBOARDS,
)
from .tts_service import TTSService
from .ffmpeg_composer import CinematicComposer
from .provider_factory import get_image_client, get_video_client


# 结果缓存 (task_id -> result)
_result_cache: Dict[str, dict] = {}
# 生成历史
_history: list = []


class ComicDramaService:
    """漫剧一键生成服务"""

    def __init__(self):
        self.image_client = get_image_client()
        self.video_client = get_video_client()
        self.tts = TTSService(default_voice=TTS_DEFAULT_VOICE)
        self.composer = CinematicComposer(fps=30)

    async def generate(
        self,
        user_input: str,
        style: str = "cinematic",
    ) -> AsyncGenerator[dict, None]:
        """
        一键生成漫剧 (SSE流式返回进度)

        Pipeline时间线(目标):
        0-3s    Gemini分镜
        3-50s   NanoBanana 6张图(并行) + TTS(并行)
        50-170s Kling图生视频 6个(并行)
        170-190s FFmpeg转场+字幕+配音+BGM
        """
        task_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        output_dir = Path(COMIC_DRAMA_OUTPUT_DIR) / task_id
        output_dir.mkdir(parents=True, exist_ok=True)

        yield {"event": "started", "data": {"task_id": task_id, "message": "AI正在构思剧情..."}}

        try:
            # ========== Step 1: Gemini分镜 ==========
            yield {"event": "progress", "data": {"step": "storyboard", "message": "AI正在创作分镜剧本...", "percent": 5}}
            storyboard = await self._generate_storyboard(user_input, style)
            yield {
                "event": "storyboard_ready",
                "data": {
                    "title": storyboard["title"],
                    "character": storyboard["character"],
                    "scenes": storyboard["scenes"],
                    "bgm_style": storyboard.get("bgm_style", "epic"),
                },
            }
            t1 = time.time() - start_time
            logger.info(f"[{task_id}] Step1 分镜完成: {t1:.1f}s")

            # ========== Step 2: 并行生成图片 + TTS ==========
            yield {"event": "progress", "data": {"step": "images", "message": "正在生成AI画面...", "percent": 15}}

            full_narration = "。".join(
                s["narration"] for s in storyboard["scenes"] if s.get("narration")
            )

            # 全并行: 6张图片同时生成 + TTS
            images_task = self._generate_all_images(storyboard, style, str(output_dir))
            tts_task = self.tts.generate_full_narration(
                full_text=full_narration,
                output_path=str(output_dir / "narration.mp3"),
            )

            image_results, narration_path = await asyncio.gather(images_task, tts_task)

            # 逐张通知前端
            for i, (img_path, img_url) in enumerate(image_results):
                yield {
                    "event": "image_generated",
                    "data": {
                        "scene_id": i + 1,
                        "image_url": f"/comic-drama/output/{task_id}/scene_{i+1:02d}.png",
                        "total": len(image_results),
                    },
                }

            t2 = time.time() - start_time
            logger.info(f"[{task_id}] Step2 图片+TTS完成: {t2:.1f}s")

            # ========== Step 3: Kling图生视频 (并行) ==========
            yield {"event": "progress", "data": {"step": "video_gen", "message": "正在生成动态视频场景...", "percent": 40}}

            video_paths = await self._generate_videos_from_images(
                image_results, storyboard, str(output_dir), task_id,
            )

            t3 = time.time() - start_time
            logger.info(f"[{task_id}] Step3 Kling视频完成: {t3:.1f}s")

            # 通知前端每个视频完成
            for i, vp in enumerate(video_paths):
                yield {
                    "event": "video_generated",
                    "data": {
                        "scene_id": i + 1,
                        "has_video": vp is not None and vp.endswith(".mp4"),
                        "total": len(video_paths),
                    },
                }

            # ========== Step 4: FFmpeg合成 ==========
            yield {"event": "progress", "data": {"step": "composing", "message": "正在合成最终视频...", "percent": 80}}

            bgm_path = self._select_bgm(storyboard.get("bgm_style", "epic"))

            compose_scenes = []
            for i, scene in enumerate(storyboard["scenes"]):
                vpath = video_paths[i] if i < len(video_paths) else None
                ipath = image_results[i][0] if i < len(image_results) else None
                compose_scenes.append({
                    "video_path": vpath,          # Kling生成的视频 (优先)
                    "image_path": ipath,           # 图片fallback
                    "duration": scene.get("duration", COMIC_DRAMA_SCENE_DURATION),
                    "camera": scene.get("camera", "static"),
                    "narration": scene.get("narration", ""),
                    "mood": scene.get("mood", "epic"),
                })

            output_video = str(output_dir / "final.mp4")
            await self.composer.compose(
                scenes=compose_scenes,
                narration_audio=narration_path,
                bgm_path=bgm_path,
                output_path=output_video,
                style=style,
            )

            elapsed = time.time() - start_time
            video_url = f"/comic-drama/output/{task_id}/final.mp4"

            # 缓存结果
            result = {
                "task_id": task_id,
                "title": storyboard["title"],
                "video_url": video_url,
                "scenes": storyboard["scenes"],
                "style": style,
                "user_input": user_input,
                "elapsed_seconds": round(elapsed, 1),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            _result_cache[task_id] = result
            _history.insert(0, {
                "task_id": task_id,
                "title": storyboard["title"],
                "style": style,
                "video_url": video_url,
                "created_at": result["created_at"],
                "elapsed_seconds": result["elapsed_seconds"],
            })
            if len(_history) > 20:
                _history.pop()

            yield {
                "event": "complete",
                "data": {
                    "task_id": task_id,
                    "video_url": video_url,
                    "title": storyboard["title"],
                    "elapsed_seconds": round(elapsed, 1),
                },
            }

        except Exception as e:
            logger.error(f"漫剧生成失败: {e}")
            import traceback
            traceback.print_exc()
            yield {
                "event": "error",
                "data": {"message": f"生成失败: {str(e)}"},
            }

    # ==================== 分镜生成 ====================

    async def _generate_storyboard(self, user_input: str, style: str) -> dict:
        """调用Gemini生成分镜JSON"""
        prompt = get_storyboard_prompt(user_input, style)

        try:
            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                resp = await client.post(
                    f"{GEMINI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GEMINI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": GEMINI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.8,
                        "max_tokens": 4096,
                    },
                )
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                storyboard = self._parse_json_response(content)
                if storyboard and "scenes" in storyboard:
                    logger.info(f"分镜生成成功: {storyboard.get('title', '未知')}, {len(storyboard['scenes'])}幕")
                    return storyboard
        except Exception as e:
            logger.error(f"Gemini分镜生成失败: {e}")

        # 降级: 预置模板
        logger.warning("使用预置分镜模板")
        fallback = copy.deepcopy(FALLBACK_STORYBOARDS["default"])
        style_suffix = get_style_suffix(style)
        for scene in fallback["scenes"]:
            scene["visual_prompt"] = f"{scene['visual_prompt']}, {style_suffix}"
        return fallback

    def _parse_json_response(self, content: str) -> Optional[dict]:
        """解析LLM返回的JSON"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        brace_start = content.find("{")
        brace_end = content.rfind("}")
        if brace_start != -1 and brace_end != -1:
            try:
                return json.loads(content[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass
        logger.error(f"无法解析JSON: {content[:200]}")
        return None

    # ==================== 图片生成 ====================

    async def _generate_all_images(
        self, storyboard: dict, style: str, output_dir: str,
    ) -> List[tuple]:
        """
        全并行生成所有场景图片
        Returns: [(local_path, remote_url), ...]
        """
        scenes = storyboard["scenes"]
        char_desc = storyboard.get("character", {}).get("description", "")
        out_dir = Path(output_dir)
        sem = asyncio.Semaphore(6)

        async def gen_one(idx: int, scene: dict) -> tuple:
            prompt = scene["visual_prompt"]
            if char_desc and char_desc.lower() not in prompt.lower():
                prompt = f"{char_desc}. {prompt}"

            img_path = str(out_dir / f"scene_{idx+1:02d}.png")
            async with sem:
                for attempt in range(2):  # 重试一次
                    try:
                        urls = await self.image_client.generate_image(prompt, num_images=1)
                        if urls:
                            await self._download_image(urls[0], img_path)
                            return (img_path, urls[0])
                    except Exception as e:
                        logger.error(f"场景{idx+1}图片生成失败(尝试{attempt+1}): {e}")
                        if attempt == 0:
                            await asyncio.sleep(2)

            # fallback: 黑色占位图
            self._create_placeholder(img_path)
            return (img_path, None)

        tasks = [gen_one(i, s) for i, s in enumerate(scenes)]
        results = await asyncio.gather(*tasks)
        return list(results)

    # ==================== Kling图生视频 ====================

    async def _generate_videos_from_images(
        self,
        image_results: List[tuple],
        storyboard: dict,
        output_dir: str,
        task_id: str,
    ) -> List[Optional[str]]:
        """
        并行将所有图片通过Kling转为5s视频
        失败的场景返回None (FFmpeg会用zoompan图片fallback)
        """
        scenes = storyboard["scenes"]
        out_dir = Path(output_dir)
        sem = asyncio.Semaphore(6)

        async def convert_one(idx: int) -> Optional[str]:
            img_path, img_url = image_results[idx]
            scene = scenes[idx]
            video_path = str(out_dir / f"video_{idx+1:02d}.mp4")

            # 没有图片URL(占位图), 跳过
            if not img_url:
                logger.warning(f"场景{idx+1}无图片URL, 跳过Kling")
                return None

            # 准备image参数: 优先HTTP URL, 本地文件转base64
            if img_url.startswith("http"):
                image_for_api = img_url
            else:
                try:
                    with open(img_path, "rb") as f:
                        image_for_api = base64.b64encode(f.read()).decode()
                except Exception:
                    return None

            prompt = scene.get("visual_prompt", "")[:200]  # Kling prompt限制

            async with sem:
                for attempt in range(2):
                    try:
                        logger.info(f"[{task_id}] Kling开始: 场景{idx+1}" + (f" 重试{attempt}" if attempt else ""))
                        video_url = await self.video_client.generate_video(
                            image_url=image_for_api,
                            prompt=prompt,
                            duration=5,
                            model="kling-v1",
                            cfg_scale=0.5,
                        )
                        if video_url:
                            await self._download_video(video_url, video_path)
                            logger.info(f"[{task_id}] Kling完成: 场景{idx+1}")
                            return video_path
                    except Exception as e:
                        logger.error(f"[{task_id}] Kling失败 场景{idx+1}(尝试{attempt+1}): {e}")
                        if attempt == 0:
                            await asyncio.sleep(3)

            logger.warning(f"[{task_id}] 场景{idx+1} Kling失败, 将用图片zoompan替代")
            return None

        tasks = [convert_one(i) for i in range(len(image_results))]
        results = await asyncio.gather(*tasks)
        return list(results)

    # ==================== 工具方法 ====================

    async def _download_image(self, url: str, save_path: str):
        try:
            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                Path(save_path).write_bytes(resp.content)
        except Exception as e:
            logger.error(f"图片下载失败: {url}, {e}")
            self._create_placeholder(save_path)

    async def _download_video(self, url: str, save_path: str):
        try:
            async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                Path(save_path).write_bytes(resp.content)
        except Exception as e:
            logger.error(f"视频下载失败: {url}, {e}")
            raise

    def _create_placeholder(self, path: str):
        """用ffmpeg生成1920x1080黑色图片"""
        import subprocess
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i",
                 "color=c=0x1a1a2a:s=1920x1080:d=1",
                 "-frames:v", "1", path],
                capture_output=True, timeout=10,
            )
        except Exception:
            # 最小黑色PNG fallback
            import struct, zlib
            w, h = 1920, 1080
            sig = b'\x89PNG\r\n\x1a\n'
            ihdr_data = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
            ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
            ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
            raw = b''.join(b'\x00' + b'\x1a\x1a\x2a' * w for _ in range(h))
            compressed = zlib.compress(raw)
            idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
            idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
            iend_crc = zlib.crc32(b'IEND') & 0xffffffff
            iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
            Path(path).write_bytes(sig + ihdr + idat + iend)

    def _select_bgm(self, bgm_style: str) -> Optional[str]:
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

    @staticmethod
    def get_history() -> list:
        return _history

    @staticmethod
    def get_result(task_id: str) -> Optional[dict]:
        return _result_cache.get(task_id)
