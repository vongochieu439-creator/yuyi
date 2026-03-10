# -*- coding: utf-8 -*-
"""
测试NanoBanana API - 验证API Key是否正常工作
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from webapp.services.nanobanana_client import NanoBananaClient


async def test_api():
    """测试NanoBanana API"""
    print("=" * 60)
    print("🧪 测试NanoBanana API")
    print("=" * 60)

    # 使用提供的API Key
    api_key = "sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq"

    client = NanoBananaClient(
        api_key=api_key,
        base_url="https://api.remenbaike.com"
    )

    print(f"\n✅ API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"✅ Base URL: https://api.remenbaike.com")
    print(f"✅ 预计成本: ¥{client.calculate_cost(1):.2f}\n")

    # 测试提示词
    prompt = "A beautiful sunset over the ocean, cinematic lighting, professional photography, 4K, high quality, warm colors"

    print(f"📝 测试提示词:\n   {prompt}\n")
    print("⏳ 开始生成图片...")
    print("   (这可能需要30秒-2分钟，请耐心等待)\n")

    try:
        # 生成单张图片
        images = await client.generate_image(
            prompt=prompt,
            num_images=1
        )

        print("=" * 60)
        print("✅ 测试成功！")
        print("=" * 60)
        print(f"\n🎨 生成的图片URL:")
        print(f"   {images[0]}\n")
        print(f"💰 实际成本: ¥{client.calculate_cost(1):.2f}")
        print(f"\n🌐 在浏览器中打开此URL查看图片:")
        print(f"   {images[0]}\n")

        return True

    except Exception as e:
        print("=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        print(f"\n错误信息: {e}\n")
        print("🔍 请检查:")
        print("   1. API Key是否正确")
        print("   2. 网络连接是否正常")
        print("   3. API额度是否充足")
        print("   4. 查看详细日志: logs/webapp.log\n")

        return False


async def test_batch_generation():
    """测试批量生成（3个提示词）"""
    print("\n" + "=" * 60)
    print("🧪 测试批量生成（3个提示词）")
    print("=" * 60)

    api_key = "sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq"

    client = NanoBananaClient(
        api_key=api_key,
        base_url="https://api.remenbaike.com"
    )

    prompts = [
        "A cute puppy playing in a park, natural lighting, 4K",
        "A modern office interior, professional photography, bright",
        "A delicious pizza on a wooden table, food photography"
    ]

    print(f"\n📝 将生成 {len(prompts)} 张图片")
    print(f"💰 预计总成本: ¥{client.calculate_cost(len(prompts)):.2f}\n")

    try:
        results = await client.batch_generate(
            prompts=prompts,
            num_images_per_prompt=1
        )

        print("=" * 60)
        print("✅ 批量生成成功！")
        print("=" * 60)

        for i, (prompt, images) in enumerate(zip(prompts, results)):
            print(f"\n{i+1}. {prompt[:50]}...")
            if images:
                print(f"   ✅ {images[0]}")
            else:
                print(f"   ❌ 生成失败")

        success_count = sum(1 for imgs in results if imgs)
        print(f"\n📊 成功率: {success_count}/{len(prompts)}")
        print(f"💰 实际成本: ¥{client.calculate_cost(success_count):.2f}\n")

        return True

    except Exception as e:
        print("=" * 60)
        print("❌ 批量测试失败")
        print("=" * 60)
        print(f"\n错误信息: {e}\n")
        return False


async def main():
    """主测试流程"""
    print("\n🚀 NanoBanana API 测试工具")
    print("=" * 60)

    # 测试1：单张图片生成
    success1 = await test_api()

    if not success1:
        print("\n⚠️ 单张图片测试失败，跳过批量测试")
        return

    # 询问是否继续批量测试
    print("\n" + "=" * 60)
    response = input("是否继续测试批量生成？(y/n): ").strip().lower()

    if response == 'y':
        await test_batch_generation()
    else:
        print("\n✅ 测试完成！")

    print("\n" + "=" * 60)
    print("🎉 下一步:")
    print("   1. 启动Web服务器: python -m webapp.main")
    print("   2. 访问: http://localhost:8080")
    print("   3. 选择项目 → 生成关键帧")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
