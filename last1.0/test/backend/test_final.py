# -*- coding: utf-8 -*-
"""
最终API测试 - 测试用户提供的密钥
"""

import sys
import io
import asyncio
import httpx

# 设置Windows输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 用户提供的API密钥
API_KEYS = [
    ("用户提供的密钥", "Q0X6CV17w4th5qwBxxaKAcjatj"),
    ("羽翼video密钥", "FPjr4Z4KMszvRa624bU9PGbvfy"),
]

BASE_URL = "https://api.wuyinkeji.com/api"


async def test_api_key(name, api_key):
    """测试单个API密钥"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"密钥: {api_key}")
    print(f"{'='*60}")

    submit_url = f"{BASE_URL}/sora2/submit"

    data = {
        "prompt": "一位年轻女性在现代办公室里微笑",
        "duration": "10",
        "aspectRatio": "9:16",
        "size": "small"
    }

    # 方法1: URL参数
    print(f"\n>>> 方法1: URL参数 ?key=xxx")
    url_with_key = f"{submit_url}?key={api_key}"

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            resp = await client.post(url_with_key, data=data)
            print(f"状态码: {resp.status_code}")
            print(f"响应: {resp.text[:300]}")

            if resp.status_code == 200:
                response_data = resp.json()
                code = response_data.get("code")
                msg = response_data.get("msg", "")

                if code == 200:
                    print(f"✅ 成功! 这个密钥可用!")
                    return True, api_key
                else:
                    print(f"❌ 错误: code={code}, msg={msg}")
            else:
                print(f"❌ HTTP错误")

    except Exception as e:
        print(f"❌ 异常: {e}")

    # 方法2: Authorization头
    print(f"\n>>> 方法2: Authorization头")
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            resp = await client.post(submit_url, data=data, headers=headers)
            print(f"状态码: {resp.status_code}")
            print(f"响应: {resp.text[:300]}")

            if resp.status_code == 200:
                response_data = resp.json()
                code = response_data.get("code")
                msg = response_data.get("msg", "")

                if code == 200:
                    print(f"✅ 成功! 这个密钥可用!")
                    return True, api_key
                else:
                    print(f"❌ 错误: code={code}, msg={msg}")
            else:
                print(f"❌ HTTP错误")

    except Exception as e:
        print(f"❌ 异常: {e}")

    return False, None


async def main():
    """主测试"""
    print("="*60)
    print("速创API密钥测试")
    print("="*60)

    working_key = None

    for name, key in API_KEYS:
        success, api_key = await test_api_key(name, key)
        if success:
            working_key = api_key
            break

        await asyncio.sleep(2)

    print(f"\n{'='*60}")
    print("测试结果")
    print(f"{'='*60}")

    if working_key:
        print(f"✅ 找到可用的密钥: {working_key}")
        print(f"\n请更新 config.py 中的 SUCHUANG_API_KEY = \"{working_key}\"")
    else:
        print(f"❌ 所有密钥都不可用!")
        print(f"\n可能的原因:")
        print(f"1. API密钥已过期")
        print(f"2. Sora2接口正在维护 (看到'该接口正在维护')")
        print(f"3. 账户余额不足")
        print(f"4. 需要登录速创API控制台获取新密钥")
        print(f"\n建议:")
        print(f"1. 访问: https://api.wuyinkeji.com/user/")
        print(f"2. 登录后查看密钥管理")
        print(f"3. 检查账户余额")
        print(f"4. 查看哪些API服务是可用的")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
