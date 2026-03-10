# -*- coding: utf-8 -*-
"""
热门百科API (remenbaike.com) 完整测试
测试所有可能的视频生成接口
"""

import sys
import io
import asyncio
import httpx
import json
from typing import Dict, List, Optional

# 设置Windows输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# API配置
API_KEY = "sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq"
BASE_URL = "https://api.remenbaike.com"

# 可能的端点列表（基于OpenAI兼容格式和常见视频API）
TEST_ENDPOINTS = [
    # OpenAI兼容格式
    {
        "name": "模型列表 (OpenAI格式)",
        "method": "GET",
        "endpoint": "/v1/models",
        "headers": {"Authorization": f"Bearer {API_KEY}"},
        "data": None,
    },
    {
        "name": "聊天测试 (验证API密钥)",
        "method": "POST",
        "endpoint": "/v1/chat/completions",
        "headers": {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        "data": {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "你好"}],
            "max_tokens": 10
        },
    },
    # 视频生成可能的端点
    {
        "name": "Sora视频生成 (OpenAI格式)",
        "method": "POST",
        "endpoint": "/v1/videos/generations",
        "headers": {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        "data": {
            "prompt": "一位年轻女性在现代办公室里微笑",
            "model": "sora-1.0",
        },
    },
    {
        "name": "Sora视频生成 (备用端点1)",
        "method": "POST",
        "endpoint": "/v1/sora/generations",
        "headers": {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        "data": {
            "prompt": "一位年轻女性在现代办公室里微笑",
        },
    },
    {
        "name": "视频生成 (通用端点)",
        "method": "POST",
        "endpoint": "/v1/video/generate",
        "headers": {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        "data": {
            "prompt": "一位年轻女性在现代办公室里微笑",
        },
    },
    # 可能的自定义格式
    {
        "name": "视频生成 (API密钥参数)",
        "method": "POST",
        "endpoint": "/api/video/generate",
        "headers": {"Content-Type": "application/json"},
        "data": {
            "api_key": API_KEY,
            "prompt": "一位年轻女性在现代办公室里微笑",
        },
    },
]


async def test_endpoint(endpoint_info: Dict) -> Dict:
    """测试单个端点"""
    print(f"\n{'='*80}")
    print(f"🧪 测试: {endpoint_info['name']}")
    print(f"{'='*80}")
    print(f"方法: {endpoint_info['method']}")
    print(f"端点: {BASE_URL}{endpoint_info['endpoint']}")

    result = {
        "name": endpoint_info["name"],
        "endpoint": endpoint_info["endpoint"],
        "success": False,
        "status_code": None,
        "response": None,
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=60, trust_env=False) as client:
            url = f"{BASE_URL}{endpoint_info['endpoint']}"

            if endpoint_info["method"] == "GET":
                resp = await client.get(url, headers=endpoint_info["headers"])
            else:  # POST
                if endpoint_info["data"]:
                    print(f"请求数据: {json.dumps(endpoint_info['data'], ensure_ascii=False, indent=2)}")
                    resp = await client.post(
                        url,
                        headers=endpoint_info["headers"],
                        json=endpoint_info["data"]
                    )
                else:
                    resp = await client.post(url, headers=endpoint_info["headers"])

            result["status_code"] = resp.status_code
            print(f"\n状态码: {resp.status_code}")

            # 尝试解析JSON
            try:
                response_data = resp.json()
                result["response"] = response_data
                print(f"响应: {json.dumps(response_data, ensure_ascii=False, indent=2)[:500]}")

                # 判断成功
                if resp.status_code == 200:
                    result["success"] = True
                    print(f"✅ 成功!")
                elif resp.status_code in [201, 202]:
                    result["success"] = True
                    print(f"✅ 已接受!")
                else:
                    print(f"⚠️ 状态码异常")

            except:
                # 非JSON响应
                text = resp.text[:500]
                result["response"] = text
                print(f"响应文本: {text}")

                if resp.status_code == 200:
                    result["success"] = True
                    print(f"✅ 成功 (非JSON响应)")

    except httpx.TimeoutException:
        error_msg = "请求超时"
        print(f"❌ {error_msg}")
        result["error"] = error_msg

    except httpx.ConnectError as e:
        error_msg = f"连接错误: {e}"
        print(f"❌ {error_msg}")
        result["error"] = error_msg

    except Exception as e:
        error_msg = f"异常: {e}"
        print(f"❌ {error_msg}")
        result["error"] = error_msg

    return result


async def test_common_video_models():
    """测试常见的视频模型名称"""
    print(f"\n{'#'*80}")
    print("测试常见视频模型")
    print(f"{'#'*80}")

    # 常见视频模型列表
    video_models = [
        "sora-1.0",
        "sora-2.0",
        "sora-turbo",
        "veo-3.1",
        "veo-3",
        "kling-2.1",
        "runway-gen3",
        "cogvideo",
    ]

    results = []

    for model in video_models:
        print(f"\n{'='*80}")
        print(f"🎬 测试模型: {model}")
        print(f"{'='*80}")

        # 尝试 /v1/videos/generations 端点
        endpoint_info = {
            "name": f"视频生成 - {model}",
            "method": "POST",
            "endpoint": "/v1/videos/generations",
            "headers": {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            "data": {
                "prompt": "一位年轻女性在现代办公室里微笑",
                "model": model,
            },
        }

        result = await test_endpoint(endpoint_info)
        results.append(result)

        await asyncio.sleep(1)

    return results


async def main():
    """主测试函数"""
    print("="*80)
    print("🔬 热门百科API (remenbaike.com) 完整测试")
    print("="*80)
    print(f"🔑 API密钥: {API_KEY[:20]}...{API_KEY[-10:]}")
    print(f"🌐 基础URL: {BASE_URL}")
    print("="*80)

    all_results = []

    # 第一阶段：测试基础端点
    print(f"\n\n{'#'*80}")
    print("第一阶段: 测试基础端点和API密钥")
    print(f"{'#'*80}")

    for endpoint_info in TEST_ENDPOINTS:
        result = await test_endpoint(endpoint_info)
        all_results.append(result)
        await asyncio.sleep(2)

    # 第二阶段：如果基础测试成功，测试不同视频模型
    basic_success = any(r["success"] for r in all_results)

    if basic_success:
        print(f"\n\n✅ 基础测试通过，继续测试视频模型...")
        video_results = await test_common_video_models()
        all_results.extend(video_results)
    else:
        print(f"\n\n⚠️ 基础测试未通过，跳过视频模型测试")

    # 生成测试报告
    print(f"\n\n{'='*80}")
    print("📊 测试报告")
    print(f"{'='*80}")

    success_results = [r for r in all_results if r["success"]]
    failed_results = [r for r in all_results if not r["success"]]

    print(f"\n✅ 成功的端点 ({len(success_results)}/{len(all_results)}):")
    if success_results:
        for r in success_results:
            print(f"\n    🎯 {r['name']}")
            print(f"       端点: {r['endpoint']}")
            print(f"       状态: HTTP {r['status_code']}")
            if r.get('response'):
                resp_str = str(r['response'])[:200]
                print(f"       响应: {resp_str}...")
    else:
        print("    ❌ 没有成功的端点")

    print(f"\n❌ 失败的端点 ({len(failed_results)}/{len(all_results)}):")
    for r in failed_results:
        print(f"\n    ⛔ {r['name']}")
        print(f"       端点: {r['endpoint']}")
        if r['status_code']:
            print(f"       HTTP状态: {r['status_code']}")
        if r['error']:
            print(f"       错误: {r['error']}")

    # 生成使用建议
    print(f"\n\n{'='*80}")
    print("💡 使用建议")
    print(f"{'='*80}")

    if success_results:
        print("\n根据测试结果，建议使用以下配置:\n")

        # 找出成功的视频生成端点
        video_endpoints = [r for r in success_results if 'video' in r['endpoint'].lower() or 'sora' in r['endpoint'].lower()]

        if video_endpoints:
            best = video_endpoints[0]
            print(f"# config.py 配置")
            print(f"REMENBAIKE_API_KEY = \"{API_KEY}\"")
            print(f"REMENBAIKE_BASE_URL = \"{BASE_URL}\"")
            print(f"REMENBAIKE_VIDEO_ENDPOINT = \"{best['endpoint']}\"")
            print(f"\n# 使用示例")
            print(f"headers = {{'Authorization': f'Bearer {{API_KEY}}', 'Content-Type': 'application/json'}}")
            print(f"data = {{'prompt': '你的提示词', 'model': 'sora-1.0'}}")
            print(f"resp = await client.post('{BASE_URL}{best['endpoint']}', headers=headers, json=data)")
        else:
            print("未找到视频生成端点，但API密钥有效。")
            print("建议:")
            print("1. 访问 https://api.remenbaike.com/console 查看文档")
            print("2. 联系平台客服获取视频API端点信息")
    else:
        print("\n⚠️ 所有端点测试都失败了!")
        print("\n可能的原因:")
        print("1. API密钥无效或已过期")
        print("2. 账户余额不足")
        print("3. API服务器地址错误")
        print("4. 需要特殊的认证方式")
        print("\n建议:")
        print("1. 登录 https://api.remenbaike.com/console/token 检查密钥")
        print("2. 查看账户余额和权限")
        print("3. 查找平台文档或联系客服")

    print(f"\n{'='*80}")
    print("测试完成!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
