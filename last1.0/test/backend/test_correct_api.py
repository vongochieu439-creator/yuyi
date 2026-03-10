# -*- coding: utf-8 -*-
"""
速创API正确测试 - 使用正确的API密钥和方法
"""

import sys
import io
import asyncio
import httpx

# 设置Windows输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 正确的API配置（从羽翼video项目中获取）
API_KEY = "FPjr4Z4KMszvRa624bU9PGbvfy"
BASE_URL = "https://api.wuyinkeji.com/api"


async def test_sora2():
    """测试Sora2接口"""
    print("="*60)
    print("测试 Sora2 接口")
    print("="*60)

    submit_url = f"{BASE_URL}/sora2/submit"
    query_url = f"{BASE_URL}/sora2/detail"

    # 测试数据
    data = {
        "prompt": "一位年轻女性在现代办公室里微笑",
        "duration": "10",
        "aspectRatio": "9:16",
        "size": "small"
    }

    # 使用URL参数key的方式（羽翼video项目的方法）
    url_with_key = f"{submit_url}?key={API_KEY}"

    print(f"\n提交接口: {submit_url}")
    print(f"API密钥: {API_KEY}")
    print(f"测试数据: {data}")

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            print(f"\n>>> 提交任务...")
            resp = await client.post(url_with_key, data=data)

            print(f"状态码: {resp.status_code}")
            print(f"响应: {resp.text[:500]}")

            if resp.status_code == 200:
                response_data = resp.json()
                code = response_data.get("code")
                msg = response_data.get("msg", "")

                if code == 200:
                    task_id = response_data.get("data", {}).get("id")
                    print(f"\n✅ 提交成功!")
                    print(f"任务ID: {task_id}")

                    # 测试查询接口
                    print(f"\n>>> 测试查询接口...")
                    query_url_with_key = f"{query_url}?key={API_KEY}&id={task_id}"
                    query_resp = await client.get(query_url_with_key)

                    print(f"状态码: {query_resp.status_code}")
                    print(f"响应: {query_resp.text[:500]}")

                    if query_resp.status_code == 200:
                        query_data = query_resp.json()
                        status = query_data.get("data", {}).get("status", 0)
                        print(f"\n✅ 查询成功!")
                        print(f"生成状态: {status} (0=排队, 1=成功, 2=失败, 3=生成中)")
                    else:
                        print(f"\n❌ 查询失败")

                else:
                    print(f"\n❌ API返回错误: code={code}, msg={msg}")

            else:
                print(f"\n❌ HTTP错误: {resp.status_code}")

    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(test_sora2())
