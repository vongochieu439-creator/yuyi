# -*- coding: utf-8 -*-
"""
速创API完整测试 - 基于官方文档验证
测试所有已确认文档的接口
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

# 基于官方文档的确认可用模型
DOCUMENTED_MODELS = [
    {
        "id": "sora2",
        "name": "Sora2",
        "doc": "35",
        "submit_url": f"{BASE_URL}/sora2/submit",
        "query_url": f"{BASE_URL}/sora2/detail",
        "status": "维护中 (文档确认)",
        "price": "0.2元/请求",
        "qps": "100/秒",
    },
    {
        "id": "sora2-new",
        "name": "Sora2 New",
        "doc": "60",
        "submit_url": f"{BASE_URL}/sora2-new/submit",
        "query_url": f"{BASE_URL}/sora2-new/detail",
        "status": "服务正常 (文档确认)",
        "price": "2.5元/请求",
        "qps": "300/秒",
        "expires": "2026-01-29",
    },
    {
        "id": "sora2-pro",
        "name": "Sora2 Pro",
        "doc": "40/41",
        "submit_url": f"{BASE_URL}/sora2-pro/submit",
        "query_url": f"{BASE_URL}/sora2-pro/detail",
        "status": "服务正常 (文档确认) - 老接口",
        "price": "免费 ✅",
        "qps": "1/秒(免费用户), 无限制(付费)",
        "daily_limit": "10,000请求/天",
    },
]

# 其他可能存在但文档未找到的模型
UNDOCUMENTED_MODELS = [
    {"id": "grok-imagine", "name": "Grok Imagine", "doc": "62?"},
    {"id": "wan2.6", "name": "Wan2.6", "doc": "47?"},
    {"id": "veo3.1", "name": "Veo 3.1", "doc": "未知"},
    {"id": "veo3.1-fast", "name": "Veo 3.1 Fast", "doc": "未知"},
    {"id": "veo3.1-pro", "name": "Veo 3.1 Pro", "doc": "未知"},
    {"id": "jimeng", "name": "即梦AI", "doc": "28(404)"},
    {"id": "runway", "name": "Runway", "doc": "未知"},
    {"id": "kling", "name": "可灵Kling", "doc": "未知"},
]


async def test_model_submission(model: Dict) -> Dict:
    """测试单个模型的提交接口"""
    print(f"\n{'='*80}")
    print(f"📹 测试模型: {model['name']} ({model['id']})")
    print(f"📄 文档编号: {model['doc']}")

    if 'status' in model:
        print(f"📊 文档状态: {model['status']}")
        print(f"💰 价格: {model['price']}")
        print(f"⚡ QPS限制: {model['qps']}")
        if 'daily_limit' in model:
            print(f"📈 每日限制: {model['daily_limit']}")
        if 'expires' in model:
            print(f"⏰ 过期时间: {model['expires']}")

    submit_url_display = model.get('submit_url', f"{BASE_URL}/{model['id']}/submit")
    print(f"🔗 提交端点: {submit_url_display}")
    print(f"{'='*80}")

    submit_url = model.get('submit_url', f"{BASE_URL}/{model['id']}/submit")

    # 测试数据 - 严格按照文档格式
    test_data = {
        "prompt": "一位年轻女性在现代办公室里微笑",
        "duration": "10",
        "aspectRatio": "9:16",
        "size": "small"
    }

    result = {
        "id": model["id"],
        "name": model["name"],
        "doc": model["doc"],
        "success": False,
        "method": None,
        "error": None,
        "response": None,
        "status_code": None,
    }

    # 方法1: Authorization头 (文档标准方法)
    print(f"\n>>> 方法1: Authorization头 (文档标准)")
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            resp = await client.post(submit_url, data=test_data, headers=headers)

            result["status_code"] = resp.status_code
            print(f"    HTTP状态: {resp.status_code}")
            print(f"    响应内容: {resp.text[:300]}")

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    code = data.get("code")
                    msg = data.get("msg", "")

                    result["response"] = data

                    if code == 200:
                        task_id = data.get("data", {}).get("id")
                        print(f"    ✅ 提交成功! 任务ID: {task_id}")
                        result["success"] = True
                        result["method"] = "Authorization头"
                        return result
                    else:
                        error_msg = f"API错误: code={code}, msg={msg}"
                        print(f"    ❌ {error_msg}")
                        result["error"] = error_msg

                        # 如果是维护错误，不需要尝试其他方法
                        if "维护" in msg or "maintenance" in msg.lower():
                            return result

                except Exception as e:
                    error_msg = f"JSON解析失败: {e}"
                    print(f"    ❌ {error_msg}")
                    result["error"] = error_msg
            else:
                print(f"    ⚠️ HTTP错误: {resp.status_code}")

    except Exception as e:
        print(f"    ❌ 请求异常: {e}")
        result["error"] = str(e)

    # 方法2: URL参数key (备用方法)
    print(f"\n>>> 方法2: URL参数key (备用方法)")
    url_with_key = f"{submit_url}?key={API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            resp = await client.post(url_with_key, data=test_data)

            result["status_code"] = resp.status_code
            print(f"    HTTP状态: {resp.status_code}")
            print(f"    响应内容: {resp.text[:300]}")

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    code = data.get("code")
                    msg = data.get("msg", "")

                    result["response"] = data

                    if code == 200:
                        task_id = data.get("data", {}).get("id")
                        print(f"    ✅ 提交成功! 任务ID: {task_id}")
                        result["success"] = True
                        result["method"] = "URL参数key"
                        return result
                    else:
                        error_msg = f"API错误: code={code}, msg={msg}"
                        print(f"    ❌ {error_msg}")
                        if not result["error"]:  # 只在之前没有错误时更新
                            result["error"] = error_msg

                except Exception as e:
                    error_msg = f"JSON解析失败: {e}"
                    print(f"    ❌ {error_msg}")
                    if not result["error"]:
                        result["error"] = error_msg
            else:
                http_error = f"HTTP {resp.status_code}"
                print(f"    ❌ {http_error}")
                if not result["error"]:
                    result["error"] = http_error

    except Exception as e:
        print(f"    ❌ 请求异常: {e}")
        if not result["error"]:
            result["error"] = str(e)

    return result


async def main():
    """主测试函数"""
    print("="*80)
    print("🚀 速创API完整测试 - 基于官方文档")
    print("="*80)
    print(f"🔑 API密钥: {API_KEY}")
    print(f"🌐 基础URL: {BASE_URL}")
    print("="*80)

    all_results = []

    # 测试已确认有文档的模型
    print(f"\n\n{'#'*80}")
    print("第一部分: 测试官方文档确认的模型")
    print(f"{'#'*80}")

    for model in DOCUMENTED_MODELS:
        result = await test_model_submission(model)
        all_results.append(result)
        await asyncio.sleep(2)  # 避免请求过快

    # 测试文档未确认的模型
    print(f"\n\n{'#'*80}")
    print("第二部分: 测试文档未找到的模型 (可能已下线)")
    print(f"{'#'*80}")

    for model in UNDOCUMENTED_MODELS:
        result = await test_model_submission(model)
        all_results.append(result)
        await asyncio.sleep(2)

    # 生成测试报告
    print(f"\n\n{'='*80}")
    print("📊 测试报告")
    print(f"{'='*80}")

    success_results = [r for r in all_results if r["success"]]
    failed_results = [r for r in all_results if not r["success"]]

    print(f"\n✅ 可用模型 ({len(success_results)}/{len(all_results)}):")
    if success_results:
        for r in success_results:
            print(f"\n    🎯 {r['name']} ({r['id']})")
            print(f"       文档: doc/{r['doc']}")
            print(f"       认证方式: {r['method']}")
            if r.get('response'):
                task_id = r['response'].get('data', {}).get('id')
                print(f"       测试任务ID: {task_id}")
    else:
        print("    ❌ 没有找到可用的模型！")

    print(f"\n❌ 不可用模型 ({len(failed_results)}/{len(all_results)}):")
    for r in failed_results:
        print(f"\n    ⛔ {r['name']} ({r['id']})")
        print(f"       文档: doc/{r['doc']}")
        print(f"       错误: {r['error']}")
        if r['status_code']:
            print(f"       HTTP状态: {r['status_code']}")

    # 生成配置建议
    print(f"\n\n{'='*80}")
    print("💡 配置文件更新建议")
    print(f"{'='*80}")

    if success_results:
        print("\n将以下代码更新到 config.py:\n")
        print("# 速创API - 实际可用的模型")
        print("VIDEO_MODELS = {")

        for r in success_results:
            model_id = r["id"]
            model_name = r["name"]

            # 从DOCUMENTED_MODELS中获取详细信息
            doc_model = next((m for m in DOCUMENTED_MODELS if m['id'] == model_id), None)

            if doc_model:
                print(f'''    "{model_id}": {{
        "name": "{model_name}",
        "provider": "suchuang",
        "endpoint": "{doc_model['submit_url']}",
        "query_endpoint": "{doc_model['query_url']}",
        "auth_method": "{r['method']}",
        "price": "{doc_model['price']}",
        "qps": "{doc_model['qps']}",
        "status": "{doc_model['status']}",''')

                if 'expires' in doc_model:
                    print(f'''        "expires": "{doc_model['expires']}",''')
                if 'daily_limit' in doc_model:
                    print(f'''        "daily_limit": "{doc_model['daily_limit']}",''')

                print(f'''        "cost_per_video": 2.0,  # 根据实际定价调整
        "duration_options": [10, 15],
        "strengths": ["AI音频", "人物对话", "场景生成"],
        "best_for": ["talking_head", "scene"],
        "quality_score": 85,
        "speed_score": 80,
    }},''')

        print("}")
    else:
        print("\n⚠️ 警告: 没有找到可用的API接口!")
        print("\n可能的解决方案:")
        print("1. 检查API密钥是否正确: https://api.wuyinkeji.com/user/")
        print("2. 确认账户余额充足")
        print("3. 查看账户是否有权限访问这些服务")
        print("4. 联系速创API客服确认哪些服务可用")
        print("5. 考虑使用其他视频生成API服务")

    print(f"\n{'='*80}")
    print("测试完成!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
