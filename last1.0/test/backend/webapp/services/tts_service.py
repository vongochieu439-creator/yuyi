# -*- coding: utf-8 -*-
"""
TTS配音服务 - 基于Edge TTS（免费、无需API Key）
支持多音色、试听、按镜头批量配音、音频时长检测
"""
import asyncio
import concurrent.futures
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict
from loguru import logger


# 音色库：分类 + 推荐场景
VOICE_CATALOG = [
    {
        "id": "zh-CN-XiaoxiaoNeural",
        "name": "晓晓",
        "gender": "female",
        "style": "活泼亲切",
        "best_for": "美妆、母婴、生活种草",
    },
    {
        "id": "zh-CN-XiaoyiNeural",
        "name": "晓伊",
        "gender": "female",
        "style": "温柔知性",
        "best_for": "护肤科普、教育培训",
    },
    {
        "id": "zh-CN-XiaochenNeural",
        "name": "晓辰",
        "gender": "female",
        "style": "甜美少女",
        "best_for": "食品、甜品、少女风产品",
    },
    {
        "id": "zh-CN-XiaohanNeural",
        "name": "晓涵",
        "gender": "female",
        "style": "冷静专业",
        "best_for": "数码3C、评测、专业内容",
    },
    {
        "id": "zh-CN-XiaomoNeural",
        "name": "晓墨",
        "gender": "female",
        "style": "温暖故事",
        "best_for": "品牌故事、情感营销",
    },
    {
        "id": "zh-CN-XiaoshuangNeural",
        "name": "晓双",
        "gender": "female",
        "style": "童声可爱",
        "best_for": "母婴、儿童产品",
    },
    {
        "id": "zh-CN-YunxiNeural",
        "name": "云希",
        "gender": "male",
        "style": "温柔阳光",
        "best_for": "生活方式、旅行、轻松内容",
    },
    {
        "id": "zh-CN-YunjianNeural",
        "name": "云健",
        "gender": "male",
        "style": "沉稳有力",
        "best_for": "数码3C、汽车、商务内容",
    },
    {
        "id": "zh-CN-YunxiaNeural",
        "name": "云夏",
        "gender": "male",
        "style": "少年活力",
        "best_for": "运动、潮流、年轻化品牌",
    },
    {
        "id": "zh-CN-YunyangNeural",
        "name": "云扬",
        "gender": "male",
        "style": "新闻播报",
        "best_for": "知识分享、行业资讯",
    },
]

# 简写映射
VOICE_PRESETS = {
    "male": "zh-CN-YunxiNeural",
    "female": "zh-CN-XiaoxiaoNeural",
    "narrator": "zh-CN-YunjianNeural",
}


class TTSService:
    """TTS配音服务"""

    def __init__(self, default_voice: str = "zh-CN-YunxiNeural"):
        self.default_voice = default_voice

    @staticmethod
    def get_voice_catalog() -> List[Dict]:
        """获取所有可用音色"""
        return VOICE_CATALOG

    @staticmethod
    def get_voice_by_industry(industry: str) -> str:
        """根据行业推荐音色"""
        mapping = {
            "美妆护肤": "zh-CN-XiaoxiaoNeural",
            "食品保健": "zh-CN-XiaochenNeural",
            "数码3C": "zh-CN-YunjianNeural",
            "服装鞋包": "zh-CN-XiaoxiaoNeural",
            "家居生活": "zh-CN-XiaoyiNeural",
            "教育培训": "zh-CN-XiaoyiNeural",
            "母婴": "zh-CN-XiaoshuangNeural",
        }
        return mapping.get(industry, "zh-CN-XiaoxiaoNeural")

    async def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> str:
        """生成语音文件（在独立线程+SelectorEventLoop中运行，兼容 uvicorn ProactorEventLoop）"""
        import edge_tts

        voice = voice or self.default_voice
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"TTS生成: voice={voice}, text={text[:30]}...")

        def _run_in_selector_loop():
            """在新线程中用 SelectorEventLoop 运行 edge_tts，绕过 ProactorEventLoop 兼容性问题"""
            if sys.platform == "win32":
                loop = asyncio.SelectorEventLoop()
            else:
                loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
                loop.run_until_complete(communicate.save(str(output)))
            finally:
                loop.close()

        try:
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                await loop.run_in_executor(executor, _run_in_selector_loop)
            logger.info(f"TTS完成: {output}")
            return str(output)
        except Exception as e:
            logger.error(f"TTS生成失败: {e}")
            raise

    async def preview_voice(self, voice_id: str, text: Optional[str] = None) -> str:
        """
        生成音色试听音频

        Returns:
            试听音频文件路径
        """
        from ..config import OUTPUTS_DIR
        preview_text = text or "这款产品真的让我眼前一亮，用了之后效果太明显了"
        preview_dir = Path(OUTPUTS_DIR) / "_tts_preview"
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_path = preview_dir / f"preview_{voice_id}.mp3"

        # 有缓存直接返回
        if preview_path.exists() and not text:
            return str(preview_path)

        await self.generate_speech(
            text=preview_text,
            output_path=str(preview_path),
            voice=voice_id,
            rate="-5%",
        )
        return str(preview_path)

    async def generate_project_narrations(
        self,
        project_id: str,
        voice: Optional[str] = None,
        rate: str = "-5%",
    ) -> Dict:
        """
        为整个项目的所有镜头生成配音

        读取项目metadata.json中的shots，为每个有narration的镜头生成mp3

        Returns:
            {narrations: [{shot_id, audio_path, audio_url, text, duration}], total_duration}
        """
        from ..config import OUTPUTS_DIR

        project_dir = Path(OUTPUTS_DIR) / project_id
        metadata_path = project_dir / "metadata.json"

        if not metadata_path.exists():
            raise ValueError(f"项目不存在: {project_id}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        shots = metadata.get("shots", [])
        if not shots:
            raise ValueError(f"项目没有镜头数据: {project_id}")

        # 根据行业推荐音色
        if not voice:
            industry = metadata.get("industry", "")
            voice = self.get_voice_by_industry(industry)

        narration_dir = project_dir / "narrations"
        narration_dir.mkdir(parents=True, exist_ok=True)

        results = []
        total_duration = 0.0

        for shot in shots:
            shot_id = shot.get("shot_id", shot.get("id", 0))
            text = shot.get("narration", "").strip()

            if not text:
                results.append({
                    "shot_id": shot_id,
                    "audio_path": None,
                    "audio_url": None,
                    "text": "",
                    "duration": 0,
                })
                continue

            audio_filename = f"shot_{shot_id:02d}.mp3"
            audio_path = narration_dir / audio_filename

            try:
                await self.generate_speech(
                    text=text,
                    output_path=str(audio_path),
                    voice=voice,
                    rate=rate,
                )

                # 检测音频时长
                duration = await self._get_audio_duration(str(audio_path))
                audio_url = f"/outputs/{project_id}/narrations/{audio_filename}"

                results.append({
                    "shot_id": shot_id,
                    "audio_path": str(audio_path),
                    "audio_url": audio_url,
                    "text": text,
                    "duration": round(duration, 2),
                })
                total_duration += duration

            except Exception as e:
                logger.error(f"镜头{shot_id}配音失败: {e}")
                results.append({
                    "shot_id": shot_id,
                    "audio_path": None,
                    "audio_url": None,
                    "text": text,
                    "duration": 0,
                    "error": str(e),
                })

        # 更新metadata
        metadata["narration_voice"] = voice
        metadata["narrations"] = results
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"项目{project_id}配音完成: {len(results)}个镜头, 总时长{total_duration:.1f}s, 音色={voice}")

        return {
            "narrations": results,
            "total_duration": round(total_duration, 2),
            "voice": voice,
            "voice_name": next((v["name"] for v in VOICE_CATALOG if v["id"] == voice), voice),
        }

    @staticmethod
    async def _get_audio_duration(audio_path: str) -> float:
        """获取音频时长(秒)"""
        try:
            from mutagen.mp3 import MP3
            audio = MP3(audio_path)
            return audio.info.length
        except ImportError:
            # fallback: 用edge_tts的SubMaker或文件大小估算
            # MP3 ~16kbps for speech → 2KB/s
            import os
            size = os.path.getsize(audio_path)
            return size / 2000.0
        except Exception:
            return 0.0

    # === 兼容旧接口 ===

    async def generate_narrations(
        self, narrations: list, output_dir: str,
        voice: Optional[str] = None, rate: str = "-10%",
    ) -> list:
        """批量生成旁白音频（兼容旧接口）"""
        results = []
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        for item in narrations:
            scene_id = item["scene_id"]
            text = item["text"]
            audio_path = out_dir / f"narration_{scene_id:02d}.mp3"
            try:
                await self.generate_speech(
                    text=text, output_path=str(audio_path),
                    voice=voice, rate=rate,
                )
                results.append({"scene_id": scene_id, "audio_path": str(audio_path), "text": text})
            except Exception as e:
                logger.error(f"场景{scene_id}旁白生成失败: {e}")
                results.append({"scene_id": scene_id, "audio_path": None, "text": text})
        return results

    async def generate_full_narration(
        self, full_text: str, output_path: str, voice: Optional[str] = None,
    ) -> str:
        """生成完整旁白（兼容旧接口）"""
        return await self.generate_speech(
            text=full_text, output_path=output_path,
            voice=voice, rate="-5%", pitch="-2Hz",
        )
