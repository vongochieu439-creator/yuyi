# -*- coding: utf-8 -*-
"""
电影级FFmpeg合成器 V2
- 优先使用Kling生成的真实视频片段
- 图片zoompan作为fallback
- 转场 + 字幕 + 配音 + BGM + 调色
"""
import asyncio
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger


# 运镜预设 (zoompan - 仅用于图片fallback)
CAMERA_PRESETS = {
    "zoom_in": "zoompan=z='min(zoom+0.002,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
    "zoom_out": "zoompan=z='if(eq(on,0),1.3,max(zoom-0.002,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
    "pan_left": "zoompan=z='1.2':x='if(eq(on,0),iw*0.2,max(x-iw*0.0015,0))':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
    "pan_right": "zoompan=z='1.2':x='if(eq(on,0),0,min(x+iw*0.0015,iw*0.2))':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
    "slow_up": "zoompan=z='1.2':x='iw/2-(iw/zoom/2)':y='if(eq(on,0),ih*0.2,max(y-ih*0.0015,0))':d={frames}:s=1920x1080:fps=30",
    "slow_down": "zoompan=z='1.2':x='iw/2-(iw/zoom/2)':y='if(eq(on,0),0,min(y+ih*0.0015,ih*0.2))':d={frames}:s=1920x1080:fps=30",
    "diagonal": "zoompan=z='min(zoom+0.0015,1.2)':x='if(eq(on,0),0,min(x+iw*0.001,iw*0.2))':y='if(eq(on,0),0,min(y+ih*0.001,ih*0.2))':d={frames}:s=1920x1080:fps=30",
    "shake": "zoompan=z='1.15+0.03*sin(on*0.5)':x='iw/2-(iw/zoom/2)+4*sin(on*0.8)':y='ih/2-(ih/zoom/2)+4*cos(on*0.6)':d={frames}:s=1920x1080:fps=30",
    "breathe": "zoompan=z='1.08+0.04*sin(on*0.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
    "focus_in": "zoompan=z='min(zoom+0.003,1.4)':x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
    "focus_out": "zoompan=z='if(eq(on,0),1.4,max(zoom-0.003,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
    "static": "zoompan=z='1.08':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30",
}

TRANSITIONS = ["fade", "wipeleft", "slideright", "circleopen", "dissolve", "slideleft"]


class CinematicComposer:
    """电影级合成器 V2"""

    def __init__(self, fps: int = 30):
        self.fps = fps
        self.transition_duration = 0.5

    async def compose(
        self,
        scenes: List[Dict],
        narration_audio: Optional[str] = None,
        bgm_path: Optional[str] = None,
        output_path: str = "output.mp4",
        style: str = "cinematic",
    ) -> str:
        """
        合成完整漫剧视频

        Args:
            scenes: [{"video_path": str|None, "image_path": str|None, "duration": float,
                       "camera": str, "narration": str, "mood": str}, ...]
            narration_audio: 旁白音频
            bgm_path: BGM音频
            output_path: 输出路径
            style: 视觉风格
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(prefix="comic_drama_"))

        try:
            # Step 1: 准备每个场景的视频片段 (Kling视频 或 zoompan图片)
            logger.info(f"开始合成: {len(scenes)}个场景")
            scene_videos = []
            for i, scene in enumerate(scenes):
                scene_video = temp_dir / f"scene_{i:02d}.mp4"
                await self._prepare_scene_clip(scene, str(scene_video))
                scene_videos.append(str(scene_video))
                logger.info(f"场景{i+1}片段就绪 ({'视频' if scene.get('video_path') else '图片'})")

            # Step 2: 转场拼接
            merged_video = temp_dir / "merged.mp4"
            await self._merge_with_transitions(scene_videos, str(merged_video), scenes)
            logger.info("转场合并完成")

            # Step 3: ASS字幕
            subtitle_file = temp_dir / "subtitles.ass"
            self._generate_ass_subtitles(scenes, str(subtitle_file))

            # Step 4: 最终混合
            await self._final_mix(
                video_path=str(merged_video),
                narration_path=narration_audio,
                bgm_path=bgm_path,
                subtitle_path=str(subtitle_file),
                output_path=str(output),
                style=style,
            )
            logger.info(f"最终合成完成: {output}")
            return str(output)

        except Exception as e:
            logger.error(f"合成失败: {e}")
            raise
        finally:
            try:
                shutil.rmtree(str(temp_dir), ignore_errors=True)
            except Exception:
                pass

    async def _prepare_scene_clip(self, scene: Dict, output_path: str):
        """
        准备单个场景片段:
        - 有video_path → 统一格式 (缩放+帧率)
        - 无video_path → 图片zoompan
        """
        video_path = scene.get("video_path")
        duration = scene.get("duration", 5.0)
        keep_audio = scene.get("keep_audio", False)

        if video_path and Path(video_path).exists() and Path(video_path).stat().st_size > 1000:
            # 有视频: 统一到1920x1080, 30fps
            # Seedance原生音频可选保留
            await self._normalize_video(video_path, output_path, duration, keep_audio=keep_audio)
        elif scene.get("image_path") and Path(scene["image_path"]).exists():
            # 图片fallback: zoompan运镜
            await self._create_scene_from_image(
                scene["image_path"], duration,
                scene.get("camera", "static"), output_path,
            )
        else:
            # 黑屏
            await self._create_black_clip(output_path, duration)

    async def _normalize_video(self, input_path: str, output_path: str, duration: float, keep_audio: bool = False):
        """统一视频格式（支持保留Seedance原生音频）"""
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30",
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        ]

        if not keep_audio:
            cmd.append("-an")  # 去掉原始音频
        else:
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])

        cmd.extend([
            "-pix_fmt", "yuv420p",
            "-r", str(self.fps),
            output_path,
        ])
        await self._run_ffmpeg(cmd, f"统一视频: {Path(input_path).name}")

    async def _create_scene_from_image(
        self, image_path: str, duration: float, camera: str, output_path: str,
    ):
        """从图片创建zoompan运镜视频 (fallback)"""
        frames = int(duration * self.fps)
        camera_filter = CAMERA_PRESETS.get(camera, CAMERA_PRESETS["static"])
        camera_filter = camera_filter.format(frames=frames)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-vf", f"{camera_filter},format=yuv420p",
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(self.fps),
            output_path,
        ]
        await self._run_ffmpeg(cmd, f"zoompan: {Path(image_path).name}")

    async def _create_black_clip(self, output_path: str, duration: float):
        """创建黑色视频片段"""
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=0x0a0a1a:s=1920x1080:d={duration}:r=30",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            output_path,
        ]
        await self._run_ffmpeg(cmd, "黑色片段")

    async def _merge_with_transitions(
        self, scene_videos: List[str], output_path: str, scenes: List[Dict],
    ):
        """使用xfade转场拼接场景"""
        if len(scene_videos) == 1:
            shutil.copy2(scene_videos[0], output_path)
            return

        n = len(scene_videos)
        inputs = []
        for v in scene_videos:
            inputs.extend(["-i", v])

        filter_parts = []
        current_offset = 0.0
        td = self.transition_duration

        for i in range(n - 1):
            transition = TRANSITIONS[i % len(TRANSITIONS)]
            duration_i = scenes[i].get("duration", 5.0)

            src1 = "[0]" if i == 0 else f"[v{i-1:02d}]"
            src2 = f"[{i+1}]"

            if i == 0:
                current_offset = duration_i - td
            else:
                current_offset = current_offset + duration_i - td

            out_label = "[vout]" if i == n - 2 else f"[v{i:02d}]"

            filter_parts.append(
                f"{src1}{src2}xfade=transition={transition}:duration={td}:offset={current_offset:.2f}{out_label}"
            )

        filter_complex = ";".join(filter_parts)

        cmd = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(self.fps),
            output_path,
        ]
        await self._run_ffmpeg(cmd, "转场合并")

    def _generate_ass_subtitles(self, scenes: List[Dict], output_path: str):
        """生成ASS字幕 (底部居中, 描边白字, 渐入渐出)"""
        header = """[Script Info]
Title: Comic Drama Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Style: Default,Microsoft YaHei,54,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,3.5,1.5,2,30,30,50,1
Style: Title,Microsoft YaHei,80,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,5,2,2,30,30,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        current_time = 0.0
        td = self.transition_duration

        for i, scene in enumerate(scenes):
            duration = scene.get("duration", 5.0)
            narration = scene.get("narration", "")
            if not narration:
                current_time += duration - (td if i < len(scenes) - 1 else 0)
                continue

            start = self._format_ass_time(current_time + 0.5)
            end = self._format_ass_time(current_time + duration - 0.8)
            text = narration.replace("\n", "\\N")
            effect_text = f"{{\\fad(500,400)}}{text}"
            events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{effect_text}")
            current_time += duration - (td if i < len(scenes) - 1 else 0)

        content = header + "\n".join(events) + "\n"
        Path(output_path).write_text(content, encoding="utf-8")

    def _format_ass_time(self, seconds: float) -> str:
        seconds = max(0, seconds)
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    async def _final_mix(
        self,
        video_path: str,
        narration_path: Optional[str],
        bgm_path: Optional[str],
        subtitle_path: str,
        output_path: str,
        style: str = "cinematic",
        mix_scene_audio: bool = False,
    ):
        """最终混合: 视频+字幕+配音+BGM+调色 (支持Seedance原生音频混入)"""
        inputs = ["-i", video_path]
        filter_parts = []
        audio_streams = []

        # 字幕 + 调色 + 电影黑边
        sub_escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")
        vf = f"[0:v]ass='{sub_escaped}'"

        color_map = {
            "cinematic": ",eq=brightness=0.02:contrast=1.1:saturation=1.15",
            "ink_wash": ",eq=brightness=0.03:contrast=1.05:saturation=0.6",
            "anime": ",eq=brightness=0.03:contrast=1.15:saturation=1.3",
            "comedy": ",eq=brightness=0.05:contrast=1.1:saturation=1.4",
        }
        vf += color_map.get(style, "")

        # 电影2.35:1黑边
        vf += ",crop=1920:816:0:132,pad=1920:1080:0:132:black"
        vf += "[vfinal]"
        filter_parts.append(vf)

        # 音频
        audio_idx = 1
        if narration_path and Path(narration_path).exists():
            inputs.extend(["-i", narration_path])
            audio_streams.append(f"[{audio_idx}:a]aresample=44100[narr]")
            audio_idx += 1

        if bgm_path and Path(bgm_path).exists():
            inputs.extend(["-i", bgm_path])
            audio_streams.append(f"[{audio_idx}:a]volume=0.15,aloop=loop=-1:size=2e+09,aresample=44100[bgm]")
            audio_idx += 1

        # 混音
        if len(audio_streams) == 2:
            filter_parts.extend(audio_streams)
            filter_parts.append("[narr][bgm]amix=inputs=2:duration=first:dropout_transition=2[afinal]")
            audio_map = ["-map", "[afinal]"]
        elif len(audio_streams) == 1:
            filter_parts.append(audio_streams[0].replace("[narr]", "[afinal]").replace("[bgm]", "[afinal]"))
            audio_map = ["-map", "[afinal]"]
        else:
            filter_parts.append("anullsrc=r=44100:cl=stereo[afinal]")
            audio_map = ["-map", "[afinal]"]

        filter_complex = ";".join(filter_parts)

        cmd = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", "[vfinal]", *audio_map,
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            output_path,
        ]
        await self._run_ffmpeg(cmd, "最终合成")

    async def _run_ffmpeg(self, cmd: List[str], description: str = ""):
        """异步执行FFmpeg"""
        logger.debug(f"FFmpeg [{description}]: {' '.join(cmd[:10])}...")
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd, capture_output=True, text=True,
                    timeout=300, encoding="utf-8", errors="replace",
                ),
            )
            if result.returncode != 0:
                stderr = result.stderr[-800:] if result.stderr else "无输出"
                logger.error(f"FFmpeg失败 [{description}]: {stderr}")
                raise RuntimeError(f"FFmpeg {description} 失败: {stderr}")
            logger.debug(f"FFmpeg [{description}] 完成")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg未安装。请下载: https://ffmpeg.org/download.html")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"FFmpeg {description} 超时(300秒)")
