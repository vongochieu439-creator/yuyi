# -*- coding: utf-8 -*-
"""直接从已有素材合成最终视频"""
import asyncio
import json
import sys
sys.path.insert(0, ".")

from webapp.services.tts_service import TTSService
from webapp.services.ffmpeg_composer import CinematicComposer
from pathlib import Path

PROJECT_DIR = Path("outputs/comic_drama/sb_1772644777_5776fa")

async def main():
    # 加载分镜
    sb = json.loads((PROJECT_DIR / "storyboard.json").read_text(encoding="utf-8"))
    frames = sb.get("frames", [])
    print(f"加载分镜: {sb.get('title')}, {len(frames)}帧")

    # TTS
    tts = TTSService()
    narration_text = "。".join(f.get("narration", "") for f in frames if f.get("narration"))
    narration_path = str(PROJECT_DIR / "narration.mp3")
    print(f"生成配音: {narration_text[:50]}...")
    await tts.generate_full_narration(narration_text, narration_path)
    print(f"配音完成: {narration_path}")

    # 构建场景列表
    scenes = []
    for f in frames:
        fid = f["frame_id"]
        vpath = PROJECT_DIR / f"video_{fid:02d}.mp4"
        ipath = PROJECT_DIR / f"frame_{fid:02d}.png"
        scenes.append({
            "video_path": str(vpath) if vpath.exists() else None,
            "image_path": str(ipath) if ipath.exists() else None,
            "duration": f.get("duration", 5.0),
            "camera": f.get("camera_movement", "static"),
            "narration": f.get("narration", ""),
            "mood": f.get("mood", "epic"),
        })
        print(f"  帧{fid}: video={'有' if vpath.exists() else '无'}, image={'有' if ipath.exists() else '无'}")

    # BGM
    bgm_dir = Path("webapp/static/bgm")
    bgm_path = None
    for f in bgm_dir.glob("*.mp3"):
        bgm_path = str(f)
        break

    # 合成
    composer = CinematicComposer(fps=30)
    output = str(PROJECT_DIR / "final.mp4")
    print(f"\n开始FFmpeg合成...")
    await composer.compose(
        scenes=scenes,
        narration_audio=narration_path,
        bgm_path=bgm_path,
        output_path=output,
        style="cinematic",
    )

    size_mb = Path(output).stat().st_size / 1024 / 1024
    print(f"\n合成完成!")
    print(f"  文件: {output}")
    print(f"  大小: {size_mb:.1f}MB")
    print(f"  浏览器访问: http://localhost:8082/comic-drama/output/sb_1772644777_5776fa/final.mp4")

asyncio.run(main())
