# -*- coding: utf-8 -*-
"""
羽翼Pro 视频生成测试 - 整合最优方案
从脚本到最终视频的完整流水线

整合来源:
- MoneyPrinterTurbo: MoviePy合成 + BGM混音 + 渐进式拼接
- Edge-TTS: 逐字时间轴（用于字幕高亮）
- 自研: AI提示词工程 + 声画同步

用法: python test_video_pipeline.py
"""
import asyncio
import json
import os
import sys
import time
import math
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

# ==================== 配置 ====================
OUTPUT_DIR = Path("C:/Users/86187/Desktop/test_video_output")
ASPECT_RATIO = "9:16"  # 竖屏
WIDTH, HEIGHT = 1080, 1920
FPS = 30

# API配置（从羽翼Pro拿）
NANOBANANA_API_KEY = "Q0X6CV17w4th5qwBxxaKAcjatj"
NANOBANANA_BASE_URL = "https://api.wuyinkeji.com/api"
GEMINI_API_KEY = "sk-qnEWMTAuxto2gX0e0629De3d85Cd42559a9752Da1423254b"
GEMINI_BASE_URL = "https://api.apiyi.com/v1"
GEMINI_MODEL = "gemini-2.5-flash"

# TTS配置
TTS_VOICE = "zh-CN-YunxiNeural"  # 男声，清晰

# BGM（预设一个安静的BGM，如果没有就不加）
BGM_VOLUME = 0.15


# ==================== 数据结构 ====================
@dataclass
class ShotData:
    """单个镜头的所有数据"""
    shot_id: int
    narration: str  # 中文口播
    visual_description: str  # 中文场景描述
    shot_type: str = "scene"
    mood: str = "warm"
    camera_movement: str = "zoom_in"
    # 以下在流水线中填充
    english_prompt: str = ""
    image_path: str = ""
    audio_path: str = ""
    audio_duration: float = 0.0
    word_timings: list = field(default_factory=list)  # [{"word": "你好", "start": 0.0, "end": 0.3}]


# ==================== 测试脚本 ====================
TEST_SCRIPT = [
    ShotData(
        shot_id=1,
        narration="你有没有发现，现在越来越多的人开始用AI来做短视频了",
        visual_description="年轻人在咖啡店里用笔记本电脑工作，屏幕上显示着AI界面",
        shot_type="scene",
        mood="curious",
        camera_movement="zoom_in",
    ),
    ShotData(
        shot_id=2,
        narration="传统的视频制作，从拍摄到剪辑，至少需要三到五天",
        visual_description="传统视频制作工作室，多台显示器，时间线软件界面",
        shot_type="scene",
        mood="serious",
        camera_movement="pan_left",
    ),
    ShotData(
        shot_id=3,
        narration="但是用AI，三分钟就能搞定一条完整的短视频",
        visual_description="未来科技感的控制台，全息投影显示视频画面，蓝色光芒",
        shot_type="effect",
        mood="excited",
        camera_movement="zoom_out",
    ),
    ShotData(
        shot_id=4,
        narration="它会自动帮你写脚本、生成画面、配音、加字幕",
        visual_description="分屏展示四个步骤：脚本文字、AI生成的图片、音频波形、字幕效果",
        shot_type="product",
        mood="confident",
        camera_movement="static",
    ),
    ShotData(
        shot_id=5,
        narration="而且生成的效果，完全可以直接发到抖音上",
        visual_description="手机屏幕展示抖音界面，视频正在播放，点赞数在增长",
        shot_type="effect",
        mood="proud",
        camera_movement="zoom_in",
    ),
    ShotData(
        shot_id=6,
        narration="如果你也想试试，关注我，下期教你怎么用",
        visual_description="博主面对镜头微笑，背景是创意工作室，手指向关注按钮",
        shot_type="talking_head",
        mood="friendly",
        camera_movement="zoom_in",
    ),
]


# ==================== Step 1: AI提示词工程 ====================
async def generate_english_prompts(shots: List[ShotData]) -> List[ShotData]:
    """用 Gemini 批量生成英文生图提示词"""
    import httpx

    print("\n[Step 1] 生成英文提示词...")
    start = time.time()

    # 构建批量请求
    shots_info = []
    for s in shots:
        shots_info.append({
            "id": s.shot_id,
            "scene": s.visual_description,
            "narration": s.narration,
            "type": s.shot_type,
            "mood": s.mood,
            "camera": s.camera_movement,
        })

    prompt = f"""你是专业的AI生图提示词工程师。将以下中文场景描述转换为英文生图提示词。

要求：
- 每条提示词100-150词
- 包含：主体、构图（竖构图9:16）、光线、色调、质感
- 风格统一为：cinematic commercial photography, warm color palette
- 不要出现任何中文
- 直接输出JSON数组，不要其他文字

场景列表：
{json.dumps(shots_info, ensure_ascii=False, indent=2)}

输出格式（严格JSON）：
[
  {{"id": 1, "prompt": "english prompt here..."}},
  ...
]"""

    try:
        async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
            resp = await client.post(
                f"{GEMINI_BASE_URL}/chat/completions",
                json={
                    "model": GEMINI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
                headers={
                    "Authorization": f"Bearer {GEMINI_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # 提取JSON（可能被```json包裹）
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            prompts = json.loads(content.strip())
            prompt_map = {p["id"]: p["prompt"] for p in prompts}

            for shot in shots:
                shot.english_prompt = prompt_map.get(shot.shot_id, shot.visual_description)
                print(f"  镜头{shot.shot_id}: {shot.english_prompt[:60]}...")

    except Exception as e:
        print(f"  Gemini调用失败，使用简单翻译: {e}")
        for shot in shots:
            shot.english_prompt = (
                f"{shot.visual_description}, vertical composition 9:16 aspect ratio, "
                f"cinematic lighting, warm tones, professional photography, 4K, detailed"
            )

    print(f"  完成! 耗时 {time.time()-start:.1f}s")
    return shots


# ==================== Step 2: 图片生成 ====================
async def generate_images(shots: List[ShotData]) -> List[ShotData]:
    """并发调用 NanoBanana 生成图片"""
    import httpx

    print("\n[Step 2] 生成分镜图片...")
    start = time.time()

    images_dir = OUTPUT_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(3)

    async def gen_one(shot: ShotData):
        async with semaphore:
            try:
                async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                    # 提交
                    resp = await client.post(
                        f"{NANOBANANA_BASE_URL}/img/draw",
                        json={
                            "model": "sora-image",
                            "prompt": shot.english_prompt,
                            "size": "auto",
                        },
                        headers={
                            "Authorization": NANOBANANA_API_KEY,
                            "Content-Type": "application/json",
                        },
                    )
                    data = resp.json()
                    if data.get("code") != 200:
                        raise RuntimeError(f"提交失败: {data}")
                    task_id = data["data"]["id"]

                    # 轮询
                    for attempt in range(60):
                        await asyncio.sleep(3)
                        resp = await client.get(
                            f"{NANOBANANA_BASE_URL}/img/drawDetail",
                            params={"key": NANOBANANA_API_KEY, "id": task_id},
                        )
                        result = resp.json()
                        if result.get("code") == 200:
                            status = result["data"].get("status", -1)
                            if status == 2:
                                image_url = result["data"]["image_url"]
                                # 下载
                                img_resp = await client.get(image_url, timeout=60.0)
                                save_path = images_dir / f"shot_{shot.shot_id:02d}.jpg"
                                with open(save_path, "wb") as f:
                                    f.write(img_resp.content)
                                shot.image_path = str(save_path)
                                print(f"  镜头{shot.shot_id} 图片生成成功")
                                return
                            elif status == 3:
                                raise RuntimeError(f"生成失败: {result['data'].get('fail_reason')}")
                    raise RuntimeError("轮询超时")

            except Exception as e:
                print(f"  镜头{shot.shot_id} 图片生成失败: {e}")
                # 生成纯色占位图
                await _create_placeholder_image(shot)

    tasks = [gen_one(s) for s in shots]
    await asyncio.gather(*tasks)

    print(f"  完成! 耗时 {time.time()-start:.1f}s")
    return shots


async def _create_placeholder_image(shot: ShotData):
    """生成占位图片（API失败时使用）"""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (WIDTH, HEIGHT), color=(30, 30, 40))
    draw = ImageDraw.Draw(img)

    # 尝试使用中文字体
    try:
        font = ImageFont.truetype("msyh.ttc", 48)
    except Exception:
        font = ImageFont.load_default()

    text = f"镜头 {shot.shot_id}\n{shot.visual_description}"
    # 简单居中
    draw.text((WIDTH // 2, HEIGHT // 2), text, fill="white", font=font, anchor="mm")

    save_path = OUTPUT_DIR / "images" / f"shot_{shot.shot_id:02d}.jpg"
    img.save(str(save_path), quality=95)
    shot.image_path = str(save_path)


# ==================== Step 3: TTS 逐镜头配音 ====================
async def generate_tts(shots: List[ShotData]) -> List[ShotData]:
    """Edge-TTS 逐镜头生成配音，获取逐字时间轴"""
    print("\n[Step 3] 生成配音...")
    start = time.time()

    audio_dir = OUTPUT_DIR / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(5)

    async def gen_one(shot: ShotData):
        async with semaphore:
            try:
                import edge_tts

                audio_path = audio_dir / f"shot_{shot.shot_id:02d}.mp3"
                communicate = edge_tts.Communicate(shot.narration, TTS_VOICE)

                # 收集音频和逐字时间轴
                word_timings = []
                audio_data = b""

                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data += chunk["data"]
                    elif chunk["type"] == "WordBoundary":
                        word_timings.append({
                            "word": chunk["text"],
                            "start": chunk["offset"] / 10_000_000,  # 100ns -> seconds
                            "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                        })

                with open(audio_path, "wb") as f:
                    f.write(audio_data)

                shot.audio_path = str(audio_path)
                shot.word_timings = word_timings

                # 获取音频实际时长
                shot.audio_duration = await _get_audio_duration(str(audio_path))
                print(f"  镜头{shot.shot_id} 配音完成: {shot.audio_duration:.1f}s, {len(word_timings)}个词")

            except Exception as e:
                print(f"  镜头{shot.shot_id} 配音失败: {e}")
                # 用字数估算时长
                shot.audio_duration = max(2.0, len(shot.narration) / 3.5)

    tasks = [gen_one(s) for s in shots]
    await asyncio.gather(*tasks)

    print(f"  完成! 耗时 {time.time()-start:.1f}s")
    return shots


async def _get_audio_duration(audio_path: str) -> float:
    """用ffprobe获取音频时长"""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-show_entries",
                "format=duration", "-of", "csv=p=0", audio_path
            ],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 5.0


# ==================== Step 4: FFmpeg 合成 ====================
async def compose_video(shots: List[ShotData]) -> str:
    """
    FFmpeg 一次性合成最终视频
    - 图片 Ken Burns 运镜
    - 逐镜头配音精确对齐
    - 逐字高亮字幕（ASS格式）
    - BGM 混音
    """
    print("\n[Step 4] 合成最终视频...")
    start = time.time()

    # 4.1 为每个镜头生成带运镜的视频片段
    clips_dir = OUTPUT_DIR / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    clip_paths = []
    for shot in shots:
        if not shot.image_path or not Path(shot.image_path).exists():
            continue

        clip_path = clips_dir / f"clip_{shot.shot_id:02d}.mp4"
        duration = max(shot.audio_duration + 0.3, 2.0)  # 比配音多0.3秒留白

        # Ken Burns 运镜参数
        zoompan = _get_zoompan_filter(shot.camera_movement, duration, FPS)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", shot.image_path,
            "-t", f"{duration:.2f}",
            "-vf", f"scale={WIDTH*2}:{HEIGHT*2},format=yuv420p,{zoompan}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-r", str(FPS),
            clip_path,
        ]

        subprocess.run(cmd, capture_output=True, timeout=30)
        if clip_path.exists():
            clip_paths.append((shot, str(clip_path)))
            print(f"  镜头{shot.shot_id} 运镜片段: {duration:.1f}s")

    if not clip_paths:
        print("  错误: 没有生成任何片段!")
        return ""

    # 4.2 生成 ASS 字幕文件（逐字高亮）
    ass_path = OUTPUT_DIR / "subtitles.ass"
    _generate_ass_subtitles(shots, str(ass_path))

    # 4.3 拼接所有片段 + 叠加配音
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for _, path in clip_paths:
            f.write(f"file '{path}'\n")

    # 先拼接视频
    merged_video = OUTPUT_DIR / "merged.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(merged_video),
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)

    # 4.4 合并所有配音为一条音轨（按时间偏移精确放置）
    narration_path = OUTPUT_DIR / "narration.mp3"
    await _merge_audio_tracks(shots, str(narration_path))

    # 4.5 最终合成：视频 + 字幕 + 配音 + BGM
    final_path = OUTPUT_DIR / "final_video.mp4"

    # 检查是否有BGM
    bgm_path = _find_bgm()

    filter_complex = f"ass='{str(ass_path).replace(chr(92), '/')}'"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(merged_video),
        "-i", str(narration_path),
    ]

    if bgm_path:
        cmd.extend(["-i", bgm_path])
        # 混音：配音100% + BGM 15%
        cmd.extend([
            "-filter_complex",
            f"[0:v]{filter_complex}[v];"
            f"[2:a]volume={BGM_VOLUME},afade=t=out:st={_total_duration(shots)-3}:d=3[bgm];"
            f"[1:a][bgm]amix=inputs=2:duration=first[a]",
            "-map", "[v]", "-map", "[a]",
        ])
    else:
        cmd.extend([
            "-vf", filter_complex,
            "-map", "0:v", "-map", "1:a",
        ])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_path),
    ])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  FFmpeg错误: {result.stderr[-500:]}")
        # 降级：不加字幕再试一次
        cmd_simple = [
            "ffmpeg", "-y",
            "-i", str(merged_video),
            "-i", str(narration_path),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-shortest",
            str(final_path),
        ]
        subprocess.run(cmd_simple, capture_output=True, timeout=120)

    elapsed = time.time() - start
    print(f"  完成! 耗时 {elapsed:.1f}s")

    if final_path.exists():
        size_mb = final_path.stat().st_size / 1024 / 1024
        total_dur = _total_duration(shots)
        print(f"\n{'='*50}")
        print(f"最终视频: {final_path}")
        print(f"时长: {total_dur:.1f}s | 文件大小: {size_mb:.1f}MB")
        print(f"分辨率: {WIDTH}x{HEIGHT} ({ASPECT_RATIO})")
        print(f"{'='*50}")
        return str(final_path)

    return ""


def _get_zoompan_filter(camera: str, duration: float, fps: int) -> str:
    """获取 zoompan 滤镜参数"""
    frames = int(duration * fps)
    w, h = WIDTH, HEIGHT

    presets = {
        "zoom_in": f"zoompan=z='min(zoom+0.0015,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps}",
        "zoom_out": f"zoompan=z='if(eq(on,0),1.25,max(zoom-0.0015,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps}",
        "pan_left": f"zoompan=z='1.15':x='if(eq(on,0),iw*0.15,max(x-iw*0.001,0))':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps}",
        "pan_right": f"zoompan=z='1.15':x='if(eq(on,0),0,min(x+iw*0.001,iw*0.15))':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps}",
        "static": f"zoompan=z='1.08':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps}",
        "breathe": f"zoompan=z='1.06+0.03*sin(on*0.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps}",
    }

    return presets.get(camera, presets["zoom_in"])


def _generate_ass_subtitles(shots: List[ShotData], output_path: str):
    """生成 ASS 字幕文件（逐行显示，大字居中）"""
    # ASS头部 - 抖音风格大字幕
    header = """[Script Info]
Title: YuyiPro Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,68,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,2,0,1,3,1,2,30,30,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    time_offset = 0.0

    for shot in shots:
        if not shot.narration:
            time_offset += shot.audio_duration
            continue

        if shot.word_timings:
            # 按短语分组（每5-8个字一行）
            words = shot.word_timings
            phrase = ""
            phrase_start = None

            for i, w in enumerate(words):
                if phrase_start is None:
                    phrase_start = w["start"]
                phrase += w["word"]

                # 遇到标点或达到8字就换行
                is_punct = w["word"] in "，。！？、；：,.!?;:"
                is_end = (i == len(words) - 1)
                is_long = len(phrase) >= 8

                if is_punct or is_end or is_long:
                    phrase_end = w["end"]
                    start_time = time_offset + phrase_start
                    end_time = time_offset + phrase_end + 0.1  # 多留0.1秒

                    events.append(
                        f"Dialogue: 0,{_format_ass_time(start_time)},{_format_ass_time(end_time)},"
                        f"Default,,0,0,0,,{phrase.strip('，。！？、；：,.!?;:')}"
                    )
                    phrase = ""
                    phrase_start = None
        else:
            # 没有逐字时间轴，整句显示
            events.append(
                f"Dialogue: 0,{_format_ass_time(time_offset)},{_format_ass_time(time_offset + shot.audio_duration)},"
                f"Default,,0,0,0,,{shot.narration}"
            )

        time_offset += shot.audio_duration

    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(header)
        f.write("\n".join(events))


def _format_ass_time(seconds: float) -> str:
    """秒数转 ASS 时间格式 H:MM:SS.CC"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


async def _merge_audio_tracks(shots: List[ShotData], output_path: str):
    """将所有镜头配音按时间偏移合并为一条音轨"""
    # 生成一段静音作为基底
    total_dur = _total_duration(shots)

    # 使用 ffmpeg 的 adelay 滤镜精确放置每段音频
    inputs = []
    filter_parts = []
    valid_count = 0
    time_offset = 0.0

    for shot in shots:
        if shot.audio_path and Path(shot.audio_path).exists():
            inputs.extend(["-i", shot.audio_path])
            delay_ms = int(time_offset * 1000)
            filter_parts.append(f"[{valid_count}:a]adelay={delay_ms}|{delay_ms}[a{valid_count}]")
            valid_count += 1
        time_offset += shot.audio_duration

    if valid_count == 0:
        # 生成静音
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"anullsrc=r=44100:cl=stereo:d={total_dur}",
            "-c:a", "mp3", output_path,
        ], capture_output=True, timeout=30)
        return

    # amix 合并所有延迟后的音频
    mix_inputs = "".join(f"[a{i}]" for i in range(valid_count))
    filter_complex = ";".join(filter_parts) + f";{mix_inputs}amix=inputs={valid_count}:duration=longest[out]"

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "mp3",
        "-ar", "44100",
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, timeout=60)


def _total_duration(shots: List[ShotData]) -> float:
    return sum(max(s.audio_duration + 0.3, 2.0) for s in shots)


def _find_bgm() -> Optional[str]:
    """查找可用的BGM文件"""
    bgm_dirs = [
        OUTPUT_DIR / "bgm",
        Path("C:/Users/86187/Desktop/yuyi_pro_complete/backend/bgm"),
    ]
    for d in bgm_dirs:
        if d.exists():
            for f in d.glob("*.mp3"):
                return str(f)
    return None


# ==================== 主流程 ====================
async def main():
    print("=" * 50)
    print("羽翼Pro 视频生成测试")
    print("=" * 50)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total_start = time.time()

    shots = TEST_SCRIPT.copy()

    # Step 1: AI提示词（~8s）
    shots = await generate_english_prompts(shots)

    # Step 2 & 3: 图片生成 和 TTS 并行执行（~40s）
    print("\n[Step 2+3] 图片生成 & TTS 配音 并行执行...")
    parallel_start = time.time()
    image_task = asyncio.create_task(generate_images(shots))
    tts_task = asyncio.create_task(generate_tts(shots))
    await asyncio.gather(image_task, tts_task)
    print(f"  并行完成! 耗时 {time.time()-parallel_start:.1f}s")

    # 输出时长统计
    total_dur = sum(s.audio_duration for s in shots)
    print(f"\n  视频总时长: {total_dur:.1f}s ({total_dur/60:.1f}分钟)")
    for s in shots:
        print(f"    镜头{s.shot_id}: {s.audio_duration:.1f}s - {s.narration[:20]}...")

    # Step 4: FFmpeg 合成（~20s）
    final_path = await compose_video(shots)

    total_elapsed = time.time() - total_start
    print(f"\n总耗时: {total_elapsed:.0f}s ({total_elapsed/60:.1f}分钟)")

    if final_path:
        print(f"\n请查看视频: {final_path}")


if __name__ == "__main__":
    asyncio.run(main())
