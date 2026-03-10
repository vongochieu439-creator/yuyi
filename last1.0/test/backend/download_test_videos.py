# -*- coding: utf-8 -*-
"""
下载测试视频到桌面
"""

import sys
import io
import asyncio
import httpx
from pathlib import Path

# 设置Windows输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 桌面路径
DESKTOP = Path(r"C:\Users\86187\Desktop")

# 要下载的视频
VIDEOS = [
    {
        "name": "veo3.1-fast_测试视频.mp4",
        "url": "https://pro.filesystem.site/cdn/20260208/e630c4f8f9d5a1ade32af0393245d2.mp4",
        "platform": "Veo 3.1 Fast",
        "description": "生成时间177秒，高质量"
    },
    {
        "name": "kling-v2.5-turbo_测试视频.mp4",
        "url": "https://v1-fdl.kechuangai.com/ksc2/HBTe0tf4CfL4a8C2HTWR7DEufUKIvVeqgPsYiMrUJCAEuSHXzWneL_XaeQy1eH5HUqMj4O49SlJFfnG19Jpwf4YLtPIaShuIWcga1HKY_vkJbj6kkvrFVoWWaKVobYGwh__gkB2OcBVyUN9QzMxkSjemuuWMwNNMxT6-nVaV9TjAHLsGoLqm7BPizT1kfUQeSy_9GudvST3sjnabAwPR6w.mp4?cacheKey=ChtzZWN1cml0eS5rbGluZy5tZXRhX2VuY3J5cHQSsAGzJQz0nCSYg1qSHunXkA9n2hDKNtiKu81vM1C2kLj4nZeJ7hnMfnV9zyPqW5ypDFbDQeie-38RF85Cu4aWJ2HXaIMyWUETB17aQQYUMApY22YG0iZNjiMsl8K90VX91rZmVuoMquWfRh6cuaZ6e9UGiqRfzTJyyqcuV5JAZcy05cNcvkTDkGceG4l1kIup9iLqD_hEi7jhx81Sxz7bZIIIbMfUXRbojRrwT47wiga9exoSOFvh80_9xnI_XufDmu_AA0PdIiDDvVVcAF5kKHwfSYRPCDDrZsc_cHvRQrEJGjhdQFobMCgFMAE&x-kcdn-pid=112757&pkey=AAXIQPmPTaiZIGlxF2xJJeLE23HLgwDAwy181ARvWZPd__FJAfJ_o1Eau2ZbY7eT9ugFstA3DN2-kwYtmqMpf7jGImdqdI1U1su7oHGmM9G8as--wpC1TWVLauE-BOIxebE",
        "platform": "Kling v2.5 Turbo",
        "description": "生成时间76秒，最快"
    },
    {
        "name": "grok-video-3_测试视频.mp4",
        "url": "https://soruxgpt-saas-yimeng.soruxgpt.com/file_download/0fbbfe73-9e7f-4ffa-9000-d56f801d6232.mp4",
        "platform": "Grok Video 3",
        "description": "生成时间120秒，实时进度"
    }
]


async def download_video(video_info: dict):
    """下载单个视频"""
    name = video_info["name"]
    url = video_info["url"]
    platform = video_info["platform"]
    description = video_info["description"]

    output_path = DESKTOP / name

    print(f"\n{'='*80}")
    print(f"📹 下载: {platform}")
    print(f"{'='*80}")
    print(f"文件名: {name}")
    print(f"说明: {description}")
    print(f"保存到: {output_path}")

    try:
        async with httpx.AsyncClient(timeout=120, trust_env=False, follow_redirects=True) as client:
            print(f"\n开始下载...")

            # 流式下载
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                # 获取文件大小
                total_size = int(response.headers.get("content-length", 0))
                if total_size:
                    print(f"文件大小: {total_size / 1024 / 1024:.2f} MB")

                # 下载并保存
                downloaded = 0
                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 显示进度
                        if total_size:
                            progress = (downloaded / total_size) * 100
                            print(f"\r进度: {progress:.1f}% ({downloaded / 1024 / 1024:.2f}/{total_size / 1024 / 1024:.2f} MB)", end="", flush=True)

                print(f"\n✅ 下载成功!")
                return True, output_path

    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def main():
    """主函数"""
    print("="*80)
    print("🎬 下载测试视频到桌面")
    print("="*80)
    print(f"目标文件夹: {DESKTOP}")
    print(f"视频数量: {len(VIDEOS)}")
    print("="*80)

    results = []

    for i, video_info in enumerate(VIDEOS, 1):
        print(f"\n[{i}/{len(VIDEOS)}]")
        success, path = await download_video(video_info)
        results.append({
            "name": video_info["name"],
            "platform": video_info["platform"],
            "success": success,
            "path": path
        })

        # 避免请求过快
        if i < len(VIDEOS):
            await asyncio.sleep(1)

    # 生成报告
    print(f"\n\n{'='*80}")
    print("📊 下载报告")
    print(f"{'='*80}")

    success_count = sum(1 for r in results if r["success"])

    print(f"\n✅ 成功下载: {success_count}/{len(results)}")
    for r in results:
        if r["success"]:
            print(f"\n  🎬 {r['platform']}")
            print(f"     文件: {r['name']}")
            print(f"     路径: {r['path']}")

    if success_count < len(results):
        print(f"\n❌ 失败: {len(results) - success_count}")
        for r in results:
            if not r["success"]:
                print(f"  ⛔ {r['platform']} - {r['name']}")

    print(f"\n{'='*80}")
    print(f"✅ 所有视频已保存到桌面!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
