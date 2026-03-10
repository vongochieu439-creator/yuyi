# -*- coding: utf-8 -*-
"""
测试重构后的Remenbaike系统
验证Veo、Kling、Grok三个平台的完整流程
"""

import sys
import io
import asyncio
from pathlib import Path

# 设置Windows输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from loguru import logger
from models import Shot, ShotType, ActType, Act, VideoScript
from modules.video_generator_remenbaike import RembaikeVideoGenerator
from config_remenbaike import VIDEO_MODELS

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True
)


def create_test_script(shot_count: int = 3, use_model: str = "kling-v2.5-turbo") -> VideoScript:
    """创建测试脚本"""
    print(f"\n{'='*80}")
    print(f"📋 创建测试脚本")
    print(f"{'='*80}")
    print(f"分镜数量: {shot_count}")
    print(f"使用模型: {use_model}")

    test_shots = []

    # 创建不同类型的分镜
    shot_definitions = [
        {
            "type": ShotType.TALKING_HEAD,
            "act": ActType.ACT1,
            "visual": "一位年轻女性在现代办公室里对镜头微笑",
            "narration": "大家好，今天给大家分享AI视频生成的革命性技术",
            "duration": 5.0
        },
        {
            "type": ShotType.SCENE,
            "act": ActType.ACT1,
            "visual": "现代化的科技公司办公室，阳光透过落地窗洒进来",
            "narration": "在这个AI时代，视频创作变得前所未有的简单",
            "duration": 5.0
        },
        {
            "type": ShotType.PRODUCT,
            "act": ActType.ACT2,
            "visual": "一台笔记本电脑屏幕上显示着AI视频生成界面",
            "narration": "只需要输入文字描述，AI就能帮你生成专业视频",
            "duration": 5.0
        },
        {
            "type": ShotType.HANDS_ON,
            "act": ActType.ACT2,
            "visual": "手在键盘上打字，输入视频生成提示词",
            "narration": "操作非常简单，任何人都能轻松上手",
            "duration": 5.0
        },
        {
            "type": ShotType.EFFECT,
            "act": ActType.ACT2,
            "visual": "屏幕上快速展示多个AI生成的视频片段",
            "narration": "生成速度快，质量高，让创作效率提升10倍",
            "duration": 5.0
        },
        {
            "type": ShotType.TALKING_HEAD,
            "act": ActType.ACT3,
            "visual": "女性对镜头兴奋地说话，背景是成功案例展示",
            "narration": "赶快尝试AI视频生成，开启你的创作之旅！",
            "duration": 5.0
        },
    ]

    # 选择前N个分镜
    for i in range(min(shot_count, len(shot_definitions))):
        shot_def = shot_definitions[i]
        shot = Shot(
            id=i+1,
            shot_type=shot_def["type"],
            act_type=shot_def["act"],
            visual_description=shot_def["visual"],
            narration=shot_def["narration"],
            duration=shot_def["duration"],
            assigned_model=use_model  # 直接分配模型
        )
        test_shots.append(shot)

    # 按幕分组
    act1_shots = [s for s in test_shots if s.act_type == ActType.ACT1]
    act2_shots = [s for s in test_shots if s.act_type == ActType.ACT2]
    act3_shots = [s for s in test_shots if s.act_type == ActType.ACT3]

    acts = []
    if act1_shots:
        acts.append(Act(ActType.ACT1, shots=act1_shots))
    if act2_shots:
        acts.append(Act(ActType.ACT2, shots=act2_shots))
    if act3_shots:
        acts.append(Act(ActType.ACT3, shots=act3_shots))

    script = VideoScript(
        title="AI视频生成革命",
        topic="AI视频生成技术",
        target_duration=shot_count * 5,
        acts=acts
    )

    script.calculate_totals()

    print(f"\n📊 脚本信息:")
    print(f"  标题: {script.title}")
    print(f"  总分镜: {script.shot_count}")
    print(f"  预计时长: {script.total_duration}秒")
    print(f"  幕数: {len(acts)}")

    return script


async def test_single_model(model_id: str, shot_count: int = 3):
    """测试单个模型"""
    print(f"\n\n{'#'*80}")
    print(f"🧪 测试模型: {model_id}")
    print(f"{'#'*80}")

    model_info = VIDEO_MODELS.get(model_id)
    if not model_info:
        print(f"❌ 模型不存在: {model_id}")
        return None

    print(f"模型信息:")
    print(f"  名称: {model_info['name']}")
    print(f"  提供商: {model_info['provider']}")
    print(f"  平均生成时间: {model_info['avg_generation_time']}秒")
    print(f"  质量分数: {model_info['quality_score']}")
    print(f"  速度分数: {model_info['speed_score']}")

    # 创建脚本
    script = create_test_script(shot_count=shot_count, use_model=model_id)

    # 创建生成器
    generator = RembaikeVideoGenerator()

    # 生成视频
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"./outputs/test_{model_id.replace('.', '_')}_{timestamp}"

    print(f"\n开始生成...")
    result = await generator.generate_all(
        script=script,
        output_dir=output_dir
    )

    # 显示结果
    print(f"\n{'='*80}")
    print(f"📊 测试结果")
    print(f"{'='*80}")
    print(f"成功: {result['success_count']}/{shot_count}")
    print(f"失败: {result['failed_count']}")
    print(f"总耗时: {result['total_duration']/60:.1f}分钟")
    print(f"成功率: {result['success_count']/shot_count*100:.1f}%")
    print(f"输出目录: {output_dir}")

    return result


async def test_all_models():
    """测试所有可用模型"""
    print("\n" + "="*80)
    print("🚀 Remenbaike系统完整测试")
    print("="*80)
    print(f"可用模型: {len(VIDEO_MODELS)} 个")
    print("  - veo3.1-fast (Google, 177秒)")
    print("  - kling-v2.5-turbo (Kuaishou, 76秒)")
    print("  - grok-video-3 (xAI, 120秒)")

    results = {}

    # 测试每个模型（每个模型只生成1个分镜快速测试）
    for model_id in ["kling-v2.5-turbo", "veo3.1-fast", "grok-video-3"]:
        result = await test_single_model(model_id, shot_count=1)
        results[model_id] = result

        # 等待一下避免API限流
        await asyncio.sleep(3)

    # 汇总报告
    print(f"\n\n{'='*80}")
    print("📈 完整测试报告")
    print(f"{'='*80}")

    for model_id, result in results.items():
        if result:
            model_info = VIDEO_MODELS[model_id]
            success_rate = result['success_count'] / (result['success_count'] + result['failed_count']) * 100
            status = "✅" if success_rate == 100 else "⚠️" if success_rate > 0 else "❌"

            print(f"\n{status} {model_info['name']}")
            print(f"   成功率: {success_rate:.0f}%")
            print(f"   耗时: {result['total_duration']/60:.1f}分钟")
            print(f"   成功: {result['success_count']} / 失败: {result['failed_count']}")

    print(f"\n{'='*80}")
    print("✅ 测试完成!")
    print(f"{'='*80}\n")


async def test_mixed_models():
    """测试混合使用多个模型"""
    print(f"\n\n{'#'*80}")
    print(f"🎨 混合模型测试")
    print(f"{'#'*80}")
    print("使用不同模型生成不同分镜，模拟真实场景")

    # 创建测试分镜，使用不同模型
    test_shots = [
        Shot(1, ShotType.TRANSITION, ActType.ACT1, "快速转场效果", "开场", 3.0, assigned_model="veo3.1-fast"),
        Shot(2, ShotType.TALKING_HEAD, ActType.ACT1, "主播介绍", "大家好", 5.0, assigned_model="kling-v2.5-turbo"),
        Shot(3, ShotType.PRODUCT, ActType.ACT2, "产品特写", "产品展示", 5.0, assigned_model="grok-video-3"),
        Shot(4, ShotType.EFFECT, ActType.ACT2, "效果展示", "效果惊人", 5.0, assigned_model="grok-video-3"),
        Shot(5, ShotType.TALKING_HEAD, ActType.ACT3, "结尾号召", "行动起来", 5.0, assigned_model="kling-v2.5-turbo"),
    ]

    acts = [
        Act(ActType.ACT1, shots=test_shots[0:2]),
        Act(ActType.ACT2, shots=test_shots[2:4]),
        Act(ActType.ACT3, shots=test_shots[4:5]),
    ]

    script = VideoScript(
        title="混合模型测试",
        topic="测试",
        target_duration=23,
        acts=acts
    )
    script.calculate_totals()

    print(f"\n分镜分配:")
    for shot in test_shots:
        model_info = VIDEO_MODELS[shot.assigned_model]
        print(f"  分镜{shot.id}: {model_info['name']} ({shot.shot_type.value})")

    # 生成
    generator = RembaikeVideoGenerator()

    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"./outputs/test_mixed_{timestamp}"

    result = await generator.generate_all(
        script=script,
        output_dir=output_dir
    )

    print(f"\n{'='*80}")
    print(f"📊 混合模型测试结果")
    print(f"{'='*80}")
    print(f"成功: {result['success_count']}/{len(test_shots)}")
    print(f"失败: {result['failed_count']}")
    print(f"总耗时: {result['total_duration']/60:.1f}分钟")
    print(f"成功率: {result['success_count']/len(test_shots)*100:.1f}%")
    print(f"输出目录: {output_dir}")

    return result


async def main():
    """主测试入口"""
    import argparse

    parser = argparse.ArgumentParser(description="测试重构后的Remenbaike系统")
    parser.add_argument("--mode", choices=["single", "all", "mixed"], default="single",
                        help="测试模式: single=单个模型, all=所有模型, mixed=混合模型")
    parser.add_argument("--model", default="kling-v2.5-turbo",
                        choices=["veo3.1-fast", "kling-v2.5-turbo", "grok-video-3"],
                        help="单个模型测试时使用的模型")
    parser.add_argument("--shots", type=int, default=3,
                        help="生成的分镜数量")

    args = parser.parse_args()

    if args.mode == "single":
        await test_single_model(args.model, args.shots)
    elif args.mode == "all":
        await test_all_models()
    elif args.mode == "mixed":
        await test_mixed_models()


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
