# -*- coding: utf-8 -*-
"""
测试所有视频模型通过聊天接口调用
"""

import sys
import io
import asyncio
import httpx
import json

# 设置Windows输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_KEY = "sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq"
BASE_URL = "https://api.remenbaike.com"

# 从模型列表中提取的所有视频模型
ALL_VIDEO_MODELS = [
    "sora-2", "sora-2-all", "sora-2-pro-all", "sora-2-characters", "sora_image",
    "veo2", "veo2-pro", "veo2-fast", "veo2-pro-components", "veo2-fast-components", "veo2-fast-frames",
    "veo3", "veo3-pro", "veo3-fast", "veo3-frames", "veo3-fast-frames", "veo3-pro-frames",
    "veo3.1", "veo3.1-pro", "veo3.1-fast", "veo3.1-4k", "veo3.1-pro-4k", "veo3.1-components", "veo3.1-components-4k", "veo3.1-fast-components",
    "veo_3_1", "veo_3_1-4K", "veo_3_1-fast", "veo_3_1-fast-4K", "veo_3_1-fast-components-4K", "veo_3_1-components", "veo_3_1-components-4K",
    "kling-video", "kling-omni-video", "kling-avatar-image2video", "kling-video-extend", "kling-effects", "kling-advanced-lip-sync",
    "kling-motion-control", "kling-multi-elements", "kling-custom-elements", "kling-custom-voices", "kling-audio",
    "runwayml-gen3a_turbo-5", "runwayml-gen3a_turbo-10", "runwayml-gen4_turbo-5", "runwayml-gen4_turbo-10",
    "grok-video-3", "grok-video-3-10s",
    "aigc-video-kling", "aigc-video-vidu", "aigc-video-hailuo",
    "mj_video",
]


async def quick_test_model(model: str):
    """快速测试单个模型"""
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            resp = await client.post(
                f"{BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "生成5秒视频：一个人微笑"}],
                    "stream": False
                }
            )

            if resp.status_code == 200:
                result = resp.json()
                # 检查是否真的生成了视频
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if "mp4" in content.lower() or "video" in content.lower() or "视频" in content:
                    return "SUCCESS", content
                else:
                    return "TEXT_ONLY", content[:100]
            elif resp.status_code == 500:
                error = resp.json()
                error_msg = error.get("error", {}).get("message", "")
                if "task-based operations" in error_msg:
                    return "NEED_TASK_API", error_msg
                else:
                    return "ERROR_500", error_msg[:100]
            elif resp.status_code == 429:
                return "OVERLOAD", "负载饱和"
            else:
                return f"HTTP_{resp.status_code}", resp.text[:100]

    except asyncio.TimeoutError:
        return "TIMEOUT", "请求超时"
    except Exception as e:
        return "EXCEPTION", str(e)[:100]


async def main():
    """主测试"""
    print("="*80)
    print("🚀 测试所有视频模型")
    print("="*80)
    print(f"总计: {len(ALL_VIDEO_MODELS)} 个视频模型")
    print("="*80)

    # 分类结果
    success_models = []  # 可以生成视频
    text_only_models = []  # 返回文本但不是视频
    need_task_api = []  # 需要task-based API
    overload_models = []  # 负载饱和
    error_models = []  # 其他错误

    print("\n开始快速测试...\n")

    for i, model in enumerate(ALL_VIDEO_MODELS, 1):
        print(f"[{i}/{len(ALL_VIDEO_MODELS)}] {model:40s} ", end="", flush=True)

        status, info = await quick_test_model(model)

        if status == "SUCCESS":
            print(f"✅ 成功")
            success_models.append((model, info))
        elif status == "TEXT_ONLY":
            print(f"⚪ 返回文本")
            text_only_models.append((model, info))
        elif status == "NEED_TASK_API":
            print(f"🔧 需要任务API")
            need_task_api.append(model)
        elif status == "OVERLOAD":
            print(f"⏳ 负载饱和")
            overload_models.append(model)
        else:
            print(f"❌ {status}")
            error_models.append((model, status, info))

        # 避免请求过快
        await asyncio.sleep(0.5)

    # 生成报告
    print(f"\n\n{'='*80}")
    print("📊 测试报告")
    print(f"{'='*80}")

    print(f"\n✅ 可用模型 ({len(success_models)}):")
    for model, info in success_models:
        print(f"    🎬 {model}")
        # 提取视频链接
        if "mp4" in info:
            import re
            urls = re.findall(r'https?://[^\s\)]+\.mp4', info)
            if urls:
                print(f"       视频: {urls[0]}")

    if overload_models:
        print(f"\n⏳ 负载饱和的模型 ({len(overload_models)}):")
        for model in overload_models:
            print(f"    ⌛ {model}")

    if need_task_api:
        print(f"\n🔧 需要特殊任务API的模型 ({len(need_task_api)}):")
        for model in need_task_api:
            print(f"    🛠️ {model}")

    if text_only_models:
        print(f"\n⚪ 仅返回文本的模型 ({len(text_only_models)}):")
        for model, _ in text_only_models[:5]:
            print(f"    📝 {model}")
        if len(text_only_models) > 5:
            print(f"    ... 还有 {len(text_only_models) - 5} 个")

    if error_models:
        print(f"\n❌ 错误的模型 ({len(error_models)}):")
        for model, status, _ in error_models[:5]:
            print(f"    ⛔ {model} - {status}")
        if len(error_models) > 5:
            print(f"    ... 还有 {len(error_models) - 5} 个")

    # 使用建议
    print(f"\n\n{'='*80}")
    print("💡 羽翼Pro项目配置建议")
    print(f"{'='*80}")

    if success_models:
        print("\n可用的视频生成模型（通过聊天接口调用）:\n")
        print("VIDEO_MODELS = {")
        for model, _ in success_models:
            print(f'''    "{model}": {{
        "provider": "remenbaike",
        "endpoint": "{BASE_URL}/v1/chat/completions",
        "method": "chat",
        "api_key": "{API_KEY[:20]}...",
        "cost_per_video": 1.0,  # 需要根据实际计费确认
    }},''')
        print("}")
    else:
        print("\n❌ 没有找到通过聊天接口可用的视频模型")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
