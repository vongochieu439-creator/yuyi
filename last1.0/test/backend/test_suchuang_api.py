# -*- coding: utf-8 -*-
"""
速创API完整测试脚本
测试所有视频生成模型的可用性
"""

import sys
import io
import asyncio
import httpx
from typing import Dict, List, Tuple

# 设置Windows输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# API配置
API_KEY = "Q0X6CV17w4th5qwBxxaKAcjatj"
BASE_URL = "https://api.wuyinkeji.com/api"

# 测试的模型列表（基于文档已知的模型）
TEST_MODELS = [
    {
        "id": "sora2",
        "name": "Sora2",
        "submit_url": f"{BASE_URL}/sora2/submit",
        "query_url": f"{BASE_URL}/sora2/detail",
        "doc": "35",
    },
    {
        "id": "sora2-new",
        "name": "Sora2 New",
        "submit_url": f"{BASE_URL}/sora2-new/submit",
        "query_url": f"{BASE_URL}/sora2-new/detail",
        "doc": "60",
    },
    {
        "id": "sora2-pro",
        "name": "Sora2 Pro",
        "submit_url": f"{BASE_URL}/sora2-pro/submit",
        "query_url": f"{BASE_URL}/sora2-pro/detail",
        "doc": "40",
    },
    {
        "id": "grok-imagine",
        "name": "Grok Imagine",
        "submit_url": f"{BASE_URL}/grok-imagine/submit",
        "query_url": f"{BASE_URL}/grok-imagine/detail",
        "doc": "62",
    },
    {
        "id": "wan2.6",
        "name": "Wan2.6",
        "submit_url": f"{BASE_URL}/wan2.6/submit",
        "query_url": f"{BASE_URL}/wan2.6/detail",
        "doc": "47",
    },
    {
        "id": "veo3.1",
        "name": "Veo 3.1",
        "submit_url": f"{BASE_URL}/veo3.1/submit",
        "query_url": f"{BASE_URL}/veo3.1/detail",
        "doc": "未知",
    },
    {
        "id": "veo3.1-fast",
        "name": "Veo 3.1 Fast",
        "submit_url": f"{BASE_URL}/veo3.1-fast/submit",
        "query_url": f"{BASE_URL}/veo3.1-fast/detail",
        "doc": "未知",
    },
    {
        "id": "veo3.1-pro",
        "name": "Veo 3.1 Pro",
        "submit_url": f"{BASE_URL}/veo3.1-pro/submit",
        "query_url": f"{BASE_URL}/veo3.1-pro/detail",
        "doc": "未知",
    },
    {
        "id": "jimeng",
        "name": "即梦AI",
        "submit_url": f"{BASE_URL}/jimeng/submit",
        "query_url": f"{BASE_URL}/jimeng/detail",
        "doc": "28",
    },
    {
        "id": "runway",
        "name": "Runway",
        "submit_url": f"{BASE_URL}/runway/submit",
        "query_url": f"{BASE_URL}/runway/detail",
        "doc": "未知",
    },
    {
        "id": "kling",
        "name": "可灵Kling",
        "submit_url": f"{BASE_URL}/kling/submit",
        "query_url": f"{BASE_URL}/kling/detail",
        "doc": "未知",
    },
]


async def test_model_submit(model: Dict) -> Tuple[bool, str, any]:
    """
    测试模型提交接口

    Returns:
        (是否可用, 错误信息, 响应数据)
    """
    print(f"\n{'='*60}")
    print(f"测试模型: {model['name']} ({model['id']})")
    print(f"文档编号: {model['doc']}")
    print(f"提交接口: {model['submit_url']}")
    print(f"{'='*60}")

    # 测试数据
    test_data = {
        "prompt": "一位年轻女性在现代办公室里微笑",
        "duration": "10",
        "aspectRatio": "9:16",
        "size": "small"
    }

    # 测试方法1: 使用Authorization头
    print(f"\n>>> 测试方法1: Authorization头 (标准方法)")
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            resp = await client.post(
                model['submit_url'],
                data=test_data,
                headers=headers
            )

            print(f"    状态码: {resp.status_code}")
            print(f"    响应: {resp.text[:200]}")

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    code = data.get("code")
                    msg = data.get("msg", "")

                    if code == 200:
                        print(f"    ✅ 成功! 模型可用")
                        return True, None, data
                    else:
                        print(f"    ❌ API错误: code={code}, msg={msg}")
                        return False, f"code={code}, msg={msg}", data
                except:
                    print(f"    ❌ 响应解析失败")
                    return False, "JSON解析失败", None
            else:
                print(f"    ❌ HTTP错误: {resp.status_code}")

                # 测试方法2: 使用URL参数key
                print(f"\n>>> 测试方法2: URL参数key")
                url_with_key = f"{model['submit_url']}?key={API_KEY}"

                resp2 = await client.post(url_with_key, data=test_data)
                print(f"    状态码: {resp2.status_code}")
                print(f"    响应: {resp2.text[:200]}")

                if resp2.status_code == 200:
                    try:
                        data2 = resp2.json()
                        code2 = data2.get("code")
                        msg2 = data2.get("msg", "")

                        if code2 == 200:
                            print(f"    ✅ 成功! 模型可用 (使用URL参数)")
                            return True, None, data2
                        else:
                            print(f"    ❌ API错误: code={code2}, msg={msg2}")
                            return False, f"code={code2}, msg={msg2}", data2
                    except:
                        print(f"    ❌ 响应解析失败")
                        return False, "JSON解析失败", None

                return False, f"HTTP {resp2.status_code}", None

    except Exception as e:
        print(f"    ❌ 异常: {e}")
        return False, str(e), None


async def test_all_models():
    """测试所有模型"""
    print("="*60)
    print("速创API - 视频生成模型完整测试")
    print("="*60)
    print(f"API密钥: {API_KEY}")
    print(f"测试模型数量: {len(TEST_MODELS)}")
    print("="*60)

    results = []

    for model in TEST_MODELS:
        success, error, data = await test_model_submit(model)

        results.append({
            "id": model["id"],
            "name": model["name"],
            "doc": model["doc"],
            "success": success,
            "error": error,
            "data": data
        })

        # 避免请求过快
        await asyncio.sleep(2)

    # 生成测试报告
    print("\n" + "="*60)
    print("测试报告")
    print("="*60)

    available_models = [r for r in results if r["success"]]
    unavailable_models = [r for r in results if not r["success"]]

    print(f"\n✅ 可用模型 ({len(available_models)}/{len(results)}):")
    for r in available_models:
        print(f"    - {r['name']} ({r['id']}) [doc:{r['doc']}]")

    print(f"\n❌ 不可用模型 ({len(unavailable_models)}/{len(results)}):")
    for r in unavailable_models:
        print(f"    - {r['name']} ({r['id']}) [doc:{r['doc']}]")
        print(f"      错误: {r['error']}")

    # 生成配置文件建议
    print("\n" + "="*60)
    print("配置文件建议")
    print("="*60)

    if available_models:
        print("\n可用的模型配置代码:\n")
        print("VIDEO_MODELS = {")
        for r in available_models:
            model_id = r['id']
            model_name = r['name']
            submit_url = f"{BASE_URL}/{model_id}/submit"
            query_url = f"{BASE_URL}/{model_id}/detail"

            print(f'''    "{model_id}": {{
        "name": "{model_name}",
        "provider": "suchuang",
        "endpoint": "{submit_url}",
        "query_endpoint": "{query_url}",
        "cost_per_video": 2.0,  # 需要根据实际定价调整
        "duration_options": [10, 15],
        "strengths": ["待补充"],
        "best_for": ["talking_head", "scene"],
        "quality_score": 85,
        "speed_score": 80,
    }},''')
        print("}")

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(test_all_models())
