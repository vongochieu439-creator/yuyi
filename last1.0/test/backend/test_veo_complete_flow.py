# -*- coding: utf-8 -*-
"""
测试Veo视频生成完整流程
"""

import sys
import io
import asyncio
import httpx
import json
import time

# 设置Windows输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_KEY = "sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq"
BASE_URL = "https://api.remenbaike.com"


async def create_veo_video(prompt: str, model: str = "veo3.1-fast"):
    """创建Veo视频任务"""
    print(f"\n{'='*80}")
    print(f"🎬 创建视频任务")
    print(f"{'='*80}")
    print(f"模型: {model}")
    print(f"提示词: {prompt}")

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.post(
                f"{BASE_URL}/v1/video/create",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json={
                    "model": model,
                    "prompt": prompt,
                    "enhance_prompt": True,  # 中文自动转英文
                    "aspect_ratio": "9:16"   # 竖屏视频
                }
            )

            print(f"\n状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 任务创建成功!")
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

                task_id = result.get("id")
                status = result.get("status")
                enhanced_prompt = result.get("enhanced_prompt")

                print(f"\n📋 任务信息:")
                print(f"  任务ID: {task_id}")
                print(f"  状态: {status}")
                if enhanced_prompt:
                    print(f"  增强提示词: {enhanced_prompt[:100]}...")

                return task_id, result
            else:
                print(f"❌ 创建失败: HTTP {response.status_code}")
                print(f"响应: {response.text}")
                return None, None

    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def query_video_status(task_id: str):
    """查询视频生成状态"""
    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.get(
                f"{BASE_URL}/v1/video/query",
                params={"id": task_id},
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result
            else:
                print(f"❌ 查询失败: HTTP {response.status_code}")
                print(f"响应: {response.text}")
                return None

    except Exception as e:
        print(f"❌ 查询异常: {e}")
        return None


async def wait_for_video_completion(task_id: str, max_wait_seconds: int = 600):
    """等待视频生成完成"""
    print(f"\n{'='*80}")
    print(f"⏳ 等待视频生成完成...")
    print(f"{'='*80}")
    print(f"任务ID: {task_id}")
    print(f"最大等待时间: {max_wait_seconds}秒")

    start_time = time.time()
    attempt = 0

    while True:
        attempt += 1
        elapsed = int(time.time() - start_time)

        print(f"\n[尝试 {attempt}] 查询状态... (已等待 {elapsed}秒)")

        result = await query_video_status(task_id)

        if result:
            status = result.get("status")
            video_url = result.get("video_url")

            print(f"  状态: {status}")

            if status == "completed" or status == "success" or video_url:
                print(f"  ✅ 视频生成完成!")
                print(f"  视频URL: {video_url}")
                return result

            elif status == "failed" or status == "error":
                print(f"  ❌ 视频生成失败!")
                error_msg = result.get("error", result.get("message", "未知错误"))
                print(f"  错误信息: {error_msg}")
                return result

            else:
                print(f"  ⏳ 继续等待... ({status})")

        # 检查是否超时
        if elapsed >= max_wait_seconds:
            print(f"\n❌ 超时! 已等待 {elapsed}秒")
            return None

        # 等待后继续查询
        await asyncio.sleep(10)  # 每10秒查询一次


async def test_veo_models():
    """测试多个Veo模型"""
    print("="*80)
    print("🚀 Veo视频生成完整流程测试")
    print("="*80)

    # 测试的模型列表
    test_cases = [
        {
            "model": "veo3.1-fast",
            "prompt": "一位年轻女性在现代办公室里微笑，自然光线",
            "description": "Veo 3.1 Fast - 快速版本"
        },
        # 可以添加更多测试用例
        # {
        #     "model": "veo3.1-pro",
        #     "prompt": "测试提示词",
        #     "description": "Veo 3.1 Pro - 高质量版本"
        # },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#'*80}")
        print(f"测试 {i}/{len(test_cases)}: {test_case['description']}")
        print(f"{'#'*80}")

        # 步骤1: 创建任务
        task_id, create_result = await create_veo_video(
            prompt=test_case["prompt"],
            model=test_case["model"]
        )

        if not task_id:
            print(f"❌ 任务创建失败，跳过此测试")
            results.append({
                "model": test_case["model"],
                "status": "create_failed",
                "error": "任务创建失败"
            })
            continue

        # 步骤2: 等待完成
        final_result = await wait_for_video_completion(task_id, max_wait_seconds=300)

        if final_result:
            results.append({
                "model": test_case["model"],
                "task_id": task_id,
                "status": final_result.get("status"),
                "video_url": final_result.get("video_url"),
                "result": final_result
            })
        else:
            results.append({
                "model": test_case["model"],
                "task_id": task_id,
                "status": "timeout",
                "error": "等待超时"
            })

        # 避免请求过快
        if i < len(test_cases):
            await asyncio.sleep(5)

    # 生成测试报告
    print(f"\n\n{'='*80}")
    print("📊 测试报告")
    print(f"{'='*80}")

    success_count = 0
    failed_count = 0

    for result in results:
        model = result["model"]
        status = result.get("status")
        video_url = result.get("video_url")

        if status in ["completed", "success"] and video_url:
            success_count += 1
            print(f"\n✅ {model}")
            print(f"   状态: {status}")
            print(f"   视频: {video_url}")
        else:
            failed_count += 1
            print(f"\n❌ {model}")
            print(f"   状态: {status}")
            error = result.get("error", "未知错误")
            print(f"   错误: {error}")

    print(f"\n{'='*80}")
    print(f"总计: {len(results)} 个测试")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    print(f"{'='*80}\n")

    return results


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(test_veo_models())
