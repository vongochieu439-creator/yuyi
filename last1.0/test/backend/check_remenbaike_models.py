# -*- coding: utf-8 -*-
"""
查看热门百科API支持的所有模型
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


async def get_all_models():
    """获取所有模型"""
    print("="*80)
    print("🔍 查看热门百科API支持的所有模型")
    print("="*80)

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            resp = await client.get(
                f"{BASE_URL}/v1/models",
                headers={"Authorization": f"Bearer {API_KEY}"}
            )

            if resp.status_code == 200:
                data = resp.json()
                models = data.get("data", [])

                print(f"\n找到 {len(models)} 个模型:\n")

                # 分类统计
                text_models = []
                vision_models = []
                thinking_models = []
                other_models = []

                for model in models:
                    model_id = model.get("id", "")

                    # 分类
                    if "vision" in model_id.lower() or "vl" in model_id.lower():
                        vision_models.append(model_id)
                    elif "thinking" in model_id.lower() or "think" in model_id.lower():
                        thinking_models.append(model_id)
                    elif any(x in model_id.lower() for x in ["gpt", "claude", "gemini", "qwen", "llama", "deepseek"]):
                        text_models.append(model_id)
                    else:
                        other_models.append(model_id)

                # 显示分类结果
                print(f"📝 文本模型 ({len(text_models)}):")
                for m in text_models[:10]:  # 只显示前10个
                    print(f"    - {m}")
                if len(text_models) > 10:
                    print(f"    ... 还有 {len(text_models) - 10} 个")

                print(f"\n👁️ 视觉/多模态模型 ({len(vision_models)}):")
                for m in vision_models:
                    print(f"    - {m}")

                print(f"\n🧠 思考链模型 ({len(thinking_models)}):")
                for m in thinking_models:
                    print(f"    - {m}")

                if other_models:
                    print(f"\n🔧 其他模型 ({len(other_models)}):")
                    for m in other_models[:10]:
                        print(f"    - {m}")
                    if len(other_models) > 10:
                        print(f"    ... 还有 {len(other_models) - 10} 个")

                # 搜索可能的图像/视频相关模型
                print(f"\n\n{'='*80}")
                print("🎨 搜索图像/视频相关模型:")
                print(f"{'='*80}")

                media_keywords = ["image", "img", "video", "vid", "stable", "diffusion", "dall", "midjourney", "flux", "sora", "runway", "kling", "veo"]
                media_models = []

                for model in models:
                    model_id = model.get("id", "").lower()
                    if any(keyword in model_id for keyword in media_keywords):
                        media_models.append(model.get("id"))

                if media_models:
                    print(f"\n找到 {len(media_models)} 个可能的图像/视频模型:")
                    for m in media_models:
                        print(f"    ✨ {m}")
                else:
                    print("\n❌ 未找到任何图像或视频生成模型")
                    print("\n⚠️ 结论: 这个平台主要提供**文本生成(LLM)** API")
                    print("         不支持 Sora/Veo/Kling 等视频生成模型")

                # 保存完整列表
                with open("remenbaike_models_full.json", "w", encoding="utf-8") as f:
                    json.dump(models, f, ensure_ascii=False, indent=2)
                print(f"\n\n💾 完整模型列表已保存到: remenbaike_models_full.json")

            else:
                print(f"❌ 请求失败: HTTP {resp.status_code}")

    except Exception as e:
        print(f"❌ 错误: {e}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(get_all_models())
