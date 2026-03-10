# -*- coding: utf-8 -*-
"""
测试热门百科API的视频模型调用方式
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

# 要测试的视频模型
VIDEO_MODELS_TO_TEST = [
    "sora-2",
    "sora-2-all",
    "veo3.1",
    "veo3.1-fast",
    "kling-video",
    "runwayml-gen3a_turbo-10",
    "grok-video-3",
]


async def test_video_model_via_chat(model: str):
    """测试通过聊天接口调用视频模型"""
    print(f"\n{'='*80}")
    print(f"🎬 测试模型: {model}")
    print(f"{'='*80}")
    print(f"方法: 通过 /v1/chat/completions 调用")

    # 尝试方式1: 直接用视频模型名
    try:
        async with httpx.AsyncClient(timeout=120, trust_env=False) as client:
            data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": "生成视频：一位年轻女性在现代办公室里微笑"}
                ],
            }

            print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")

            resp = await client.post(
                f"{BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json=data
            )

            print(f"状态码: {resp.status_code}")

            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ 成功!")
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)[:800]}")
                return True, result
            else:
                try:
                    error = resp.json()
                    print(f"❌ 失败: {json.dumps(error, ensure_ascii=False)}")
                except:
                    print(f"❌ 失败: {resp.text[:300]}")
                return False, None

    except Exception as e:
        print(f"❌ 异常: {e}")
        return False, None


async def test_image_generation(model: str = "dall-e-3"):
    """测试图像生成接口"""
    print(f"\n{'='*80}")
    print(f"🎨 测试图像生成: {model}")
    print(f"{'='*80}")

    # 尝试OpenAI标准图像端点
    try:
        async with httpx.AsyncClient(timeout=120, trust_env=False) as client:
            data = {
                "model": model,
                "prompt": "一位年轻女性在现代办公室里微笑",
                "n": 1,
                "size": "1024x1024"
            }

            print(f"端点: /v1/images/generations")
            print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")

            resp = await client.post(
                f"{BASE_URL}/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json=data
            )

            print(f"状态码: {resp.status_code}")

            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ 图像生成成功!")
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
                return True
            else:
                try:
                    error = resp.json()
                    print(f"❌ 失败: {json.dumps(error, ensure_ascii=False)}")
                except:
                    print(f"❌ 失败: {resp.text[:300]}")
                return False

    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


async def explore_api_structure():
    """探索API的其他可能端点"""
    print(f"\n{'='*80}")
    print(f"🔍 探索其他可能的API端点")
    print(f"{'='*80}")

    possible_endpoints = [
        "/v1/images/generations",
        "/v1/generations",
        "/v1/create",
        "/api/generate",
        "/api/v1/generate",
    ]

    for endpoint in possible_endpoints:
        print(f"\n>>> 测试端点: {endpoint}")
        try:
            async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
                resp = await client.post(
                    f"{BASE_URL}{endpoint}",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sora-2",
                        "prompt": "测试"
                    }
                )

                print(f"    状态码: {resp.status_code}")
                if resp.status_code != 404:
                    try:
                        print(f"    响应: {resp.json()}")
                    except:
                        print(f"    响应: {resp.text[:200]}")

        except Exception as e:
            print(f"    ❌ {e}")


async def main():
    """主测试"""
    print("="*80)
    print("🚀 热门百科API - 视频模型调用测试")
    print("="*80)
    print(f"🔑 API密钥: {API_KEY[:20]}...{API_KEY[-10:]}")
    print(f"📋 待测试模型: {len(VIDEO_MODELS_TO_TEST)} 个")
    print("="*80)

    # 测试图像生成（验证思路）
    print(f"\n\n{'#'*80}")
    print("第一步: 测试图像生成接口")
    print(f"{'#'*80}")

    image_success = await test_image_generation("dall-e-3")

    # 测试视频模型
    print(f"\n\n{'#'*80}")
    print("第二步: 测试视频模型")
    print(f"{'#'*80}")

    success_models = []
    failed_models = []

    for model in VIDEO_MODELS_TO_TEST:
        success, result = await test_video_model_via_chat(model)

        if success:
            success_models.append({"model": model, "result": result})
        else:
            failed_models.append(model)

        await asyncio.sleep(2)

    # 探索其他端点
    print(f"\n\n{'#'*80}")
    print("第三步: 探索其他可能的端点")
    print(f"{'#'*80}")

    await explore_api_structure()

    # 生成报告
    print(f"\n\n{'='*80}")
    print("📊 测试报告")
    print(f"{'='*80}")

    print(f"\n✅ 成功的模型 ({len(success_models)}):")
    for item in success_models:
        print(f"    🎯 {item['model']}")

    print(f"\n❌ 失败的模型 ({len(failed_models)}):")
    for model in failed_models:
        print(f"    ⛔ {model}")

    if image_success:
        print(f"\n✅ 图像生成接口可用: /v1/images/generations")

    # 建议
    print(f"\n\n{'='*80}")
    print("💡 建议")
    print(f"{'='*80}")

    print("\n由于视频端点都返回404，可能的情况:")
    print("1. 这个平台可能需要特殊的调用方式")
    print("2. 视频模型可能需要通过网页控制台使用，而非API")
    print("3. 需要查看平台的官方文档获取正确调用方法")
    print("\n建议操作:")
    print("1. 登录 https://api.remenbaike.com/console 查看文档")
    print("2. 查找是否有'视频生成'或'Video'相关的API文档")
    print("3. 联系平台客服询问视频API的正确使用方法")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
