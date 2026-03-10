# -*- coding: utf-8 -*-
"""
测试Luma视频生成完整流程
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


async def create_luma_video(user_prompt: str, model_name: str = "ray-v2", **kwargs):
    """创建Luma视频任务"""
    print(f"\n{'='*80}")
    print(f"🎬 创建Luma视频任务")
    print(f"{'='*80}")
    print(f"模型: {model_name}")
    print(f"提示词: {user_prompt}")

    # 构建请求参数
    request_data = {
        "user_prompt": user_prompt,
        "model_name": model_name,
    }

    # 合并额外参数
    request_data.update(kwargs)

    print(f"请求参数: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.post(
                f"{BASE_URL}/luma/generations",
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

                # 尝试不同的响应格式
                # 格式1: 标准格式 {code, data: {task_id}}
                code = result.get("code")
                if code is not None:
                    data = result.get("data", {})
                    task_id = data.get("task_id")
                    task_status = data.get("task_status")
                else:
                    # 格式2: 直接格式 {id, state}
                    task_id = result.get("id")
                    task_status = result.get("state") or result.get("status")

                print(f"\n📋 任务信息:")
                print(f"  任务ID: {task_id}")
                print(f"  状态: {task_status}")

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


async def query_luma_video_status(task_id: str):
    """查询Luma视频生成状态"""
    try:
        # 尝试官方格式的端点
        url = f"{BASE_URL}/luma/generations/{task_id}"

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


async def wait_for_luma_completion(task_id: str, max_wait_seconds: int = 600):
    """等待Luma视频生成完成"""
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

        result = await query_luma_video_status(task_id)

        if result:
            # 尝试不同的响应格式
            # 格式1: {code, data: {task_status}}
            code = result.get("code")
            if code is not None:
                data = result.get("data", {})
                task_status = data.get("task_status")
                task_result = data.get("task_result", {})
                video_url = task_result.get("video") or task_result.get("video_url")
            else:
                # 格式2: {state, video}
                task_status = result.get("state") or result.get("status")
                video_url = result.get("video") or result.get("video_url") or result.get("video_raw")

            print(f"  状态: {task_status}")

            # 检查是否完成
            if task_status in ["completed", "succeed", "success"] or video_url:
                if video_url:
                    print(f"  ✅ 视频生成完成!")
                    print(f"  视频URL: {video_url}")
                    return result
                else:
                    print(f"  ⚠️ 状态为完成但没有视频URL")

            elif task_status in ["failed", "error"]:
                print(f"  ❌ 视频生成失败!")
                error_msg = result.get("error", result.get("message", "未知错误"))
                print(f"  错误信息: {error_msg}")
                return result

            else:
                print(f"  ⏳ 继续等待... ({task_status})")

        # 检查是否超时
        if elapsed >= max_wait_seconds:
            print(f"\n❌ 超时! 已等待 {elapsed}秒")
            return None

        # 等待后继续查询
        await asyncio.sleep(10)


async def test_luma_models():
    """测试Luma模型"""
    print("="*80)
    print("🚀 Luma视频生成完整流程测试")
    print("="*80)

    # 测试用例
    test_cases = [
        {
            "user_prompt": "一位年轻女性在海滩上漫步，夕阳西下，海浪轻拍沙滩",
            "model_name": "ray-v2",
            "duration": "5s",
            "resolution": "720p",
            "description": "Luma Ray v2 - 最新版本"
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
        task_id, create_result = await create_luma_video(**test_case)

        if not task_id:
            print(f"❌ 任务创建失败，跳过此测试")
            results.append({
                "model": test_case.get("model_name", "ray-v2"),
                "status": "create_failed",
                "error": "任务创建失败"
            })
            continue

        # 步骤2: 等待完成
        final_result = await wait_for_luma_completion(task_id, max_wait_seconds=300)

        if final_result:
            # 提取视频URL
            code = final_result.get("code")
            if code is not None:
                data = final_result.get("data", {})
                task_status = data.get("task_status")
                task_result = data.get("task_result", {})
                video_url = task_result.get("video") or task_result.get("video_url")
            else:
                task_status = final_result.get("state") or final_result.get("status")
                video_url = final_result.get("video") or final_result.get("video_url") or final_result.get("video_raw")

            results.append({
                "model": test_case.get("model_name", "ray-v2"),
                "task_id": task_id,
                "status": task_status,
                "video_url": video_url,
                "result": final_result
            })
        else:
            results.append({
                "model": test_case.get("model_name", "ray-v2"),
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

        if status in ["completed", "succeed", "success"] and video_url:
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

    asyncio.run(test_luma_models())
