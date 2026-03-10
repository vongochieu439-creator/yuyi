# -*- coding: utf-8 -*-
"""
测试Kling视频生成完整流程
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


async def create_kling_video(prompt: str, model_name: str = "kling-v2-5-turbo", **kwargs):
    """创建Kling视频任务"""
    print(f"\n{'='*80}")
    print(f"🎬 创建Kling视频任务")
    print(f"{'='*80}")
    print(f"模型: {model_name}")
    print(f"提示词: {prompt}")

    # 构建请求参数
    request_data = {
        "model_name": model_name,
        "prompt": prompt,
    }

    # 合并额外参数
    request_data.update(kwargs)

    print(f"请求参数: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.post(
                f"{BASE_URL}/kling/v1/videos/text2video",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=request_data
            )

            print(f"\n状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 任务创建成功!")
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

                code = result.get("code")
                message = result.get("message")
                data = result.get("data", {})

                if code == 0:
                    task_id = data.get("task_id")
                    task_status = data.get("task_status")

                    print(f"\n📋 任务信息:")
                    print(f"  任务ID: {task_id}")
                    print(f"  状态: {task_status}")

                    return task_id, result
                else:
                    print(f"❌ API返回错误: code={code}, message={message}")
                    return None, result
            else:
                print(f"❌ 创建失败: HTTP {response.status_code}")
                print(f"响应: {response.text}")
                return None, None

    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def query_kling_video_status(task_id: str, action2: str = "text2video"):
    """查询Kling视频生成状态"""
    try:
        # 构建URL: /kling/v1/videos/text2video/{task_id}
        url = f"{BASE_URL}/kling/v1/videos/{action2}/{task_id}"

        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.get(
                url,
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


async def wait_for_kling_completion(task_id: str, action2: str = "text2video", max_wait_seconds: int = 600):
    """等待Kling视频生成完成"""
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

        result = await query_kling_video_status(task_id, action2)

        if result:
            code = result.get("code")
            data = result.get("data", {})
            task_status = data.get("task_status")

            print(f"  Code: {code}")
            print(f"  状态: {task_status}")

            if task_status == "succeed":
                task_result = data.get("task_result", {})
                videos = task_result.get("videos", [])

                if videos:
                    video_url = videos[0].get("url")
                    print(f"  ✅ 视频生成完成!")
                    print(f"  视频URL: {video_url}")
                    return result
                else:
                    print(f"  ⚠️ 状态为成功但没有视频URL")

            elif task_status == "failed":
                print(f"  ❌ 视频生成失败!")
                error_msg = data.get("task_status_msg", "未知错误")
                print(f"  错误信息: {error_msg}")
                return result

            else:
                print(f"  ⏳ 继续等待... ({task_status})")

        # 检查是否超时
        if elapsed >= max_wait_seconds:
            print(f"\n❌ 超时! 已等待 {elapsed}秒")
            return None

        # 等待后继续查询
        await asyncio.sleep(10)  # 每10秒查询一次


async def test_kling_models():
    """测试Kling模型"""
    print("="*80)
    print("🚀 Kling视频生成完整流程测试")
    print("="*80)

    # 测试用例
    test_cases = [
        {
            "model_name": "kling-v2-5-turbo",
            "prompt": "一位年轻女性在现代办公室里微笑，阳光明媚",
            "duration": 5,
            "aspect_ratio": "9:16",
            "description": "Kling v2.5 Turbo - 最新快速版"
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#'*80}")
        print(f"测试 {i}/{len(test_cases)}: {test_case['description']}")
        print(f"{'#'*80}")

        # 提取描述字段
        description = test_case.pop("description")

        # 步骤1: 创建任务
        task_id, create_result = await create_kling_video(**test_case)

        if not task_id:
            print(f"❌ 任务创建失败，跳过此测试")
            results.append({
                "model": test_case["model_name"],
                "status": "create_failed",
                "error": "任务创建失败"
            })
            continue

        # 步骤2: 等待完成
        final_result = await wait_for_kling_completion(task_id, action2="text2video", max_wait_seconds=300)

        if final_result:
            data = final_result.get("data", {})
            task_result = data.get("task_result", {})
            videos = task_result.get("videos", [])
            video_url = videos[0].get("url") if videos else None

            results.append({
                "model": test_case["model_name"],
                "task_id": task_id,
                "status": data.get("task_status"),
                "video_url": video_url,
                "result": final_result
            })
        else:
            results.append({
                "model": test_case["model_name"],
                "task_id": task_id,
                "status": "timeout",
                "error": "等待超时"
            })

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

        if status == "succeed" and video_url:
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

    asyncio.run(test_kling_models())
