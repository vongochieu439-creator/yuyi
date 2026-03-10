# 使用示例

完整的代码示例，帮助你快速上手羽翼Pro V2 - Remenbaike版。

---

## 📚 目录

1. [基础示例](#基础示例)
2. [高级用法](#高级用法)
3. [实战案例](#实战案例)
4. [最佳实践](#最佳实践)

---

## 基础示例

### 示例1: 生成15秒抖音短视频

```python
import asyncio
from yuyi_pro_remenbaike import YuyiProRemenbaike

async def create_tiktok_video():
    """生成15秒抖音短视频"""
    yuyi = YuyiProRemenbaike()

    result = await yuyi.create_video(
        topic="新品上市 - iPhone 16 Pro",
        target_duration=15,        # 15秒
        total_budget=10.0,         # 预算10元
        quality_priority=False,    # 速度优先
        style="marketing"
    )

    if result["success"]:
        print("✅ 视频生成成功!")
        print(f"输出目录: {result['output_dir']}")
        print(f"成本: ¥{result['stats']['estimated_cost']:.2f}")
    else:
        print("❌ 生成失败")

asyncio.run(create_tiktok_video())
```

### 示例2: 生成60秒产品介绍视频

```python
async def create_product_video():
    """生成60秒产品介绍"""
    yuyi = YuyiProRemenbaike()

    # 定义产品信息
    from models import ProductProfile

    product = ProductProfile(
        name="智能手表 Pro",
        category="可穿戴设备",
        selling_points=[
            "7天超长续航",
            "血氧监测",
            "NFC支付"
        ],
        core_value="健康生活助手",
        target_audience="年轻白领",
        tone="科技感"
    )

    result = await yuyi.create_video(
        topic="智能手表 Pro 产品介绍",
        target_duration=60,
        product=product,
        total_budget=30.0,
        quality_priority=True,     # 质量优先
        style="professional"
    )

    return result

asyncio.run(create_product_video())
```

### 示例3: 批量生成视频

```python
async def batch_create_videos():
    """批量生成多个视频"""
    yuyi = YuyiProRemenbaike()

    topics = [
        "AI技术革命",
        "健康饮食指南",
        "理财入门知识",
        "时尚穿搭技巧",
        "旅游攻略分享"
    ]

    results = []

    for topic in topics:
        print(f"\n正在生成: {topic}")

        result = await yuyi.create_video(
            topic=topic,
            target_duration=30,
            total_budget=15.0,
            quality_priority=False,  # 批量生产用速度优先
            style="marketing"
        )

        results.append({
            "topic": topic,
            "success": result["success"],
            "cost": result["stats"]["estimated_cost"],
            "output": result["output_dir"]
        })

        # 避免API限流
        await asyncio.sleep(5)

    # 统计
    success_count = sum(1 for r in results if r["success"])
    total_cost = sum(r["cost"] for r in results)

    print(f"\n=== 批量生成完成 ===")
    print(f"成功: {success_count}/{len(topics)}")
    print(f"总成本: ¥{total_cost:.2f}")

asyncio.run(batch_create_videos())
```

---

## 高级用法

### 示例4: 自定义模型选择

```python
from engines.model_scheduler_remenbaike import RembaikeModelScheduler
from models import Shot, ShotType, ActType, Act, VideoScript

async def custom_model_selection():
    """自定义模型选择策略"""

    # 创建调度器
    scheduler = RembaikeModelScheduler()

    # 手动创建分镜
    shots = [
        Shot(1, ShotType.TALKING_HEAD, ActType.ACT1, "开场", "大家好", 5.0),
        Shot(2, ShotType.PRODUCT, ActType.ACT2, "产品展示", "看这个", 5.0),
        Shot(3, ShotType.EFFECT, ActType.ACT2, "效果展示", "太棒了", 5.0),
        Shot(4, ShotType.TALKING_HEAD, ActType.ACT3, "结尾", "关注我", 5.0),
    ]

    # 批量分配模型
    assigned_shots, total_cost = scheduler.batch_assign_models(
        shots=shots,
        total_budget=10.0,        # 预算限制
        quality_priority=True     # 质量优先
    )

    # 查看分配结果
    for shot in assigned_shots:
        print(f"分镜{shot.id}: {shot.assigned_model}")
        print(f"  理由: {shot.model_reason}")
        print(f"  成本: ¥{shot.estimated_cost:.2f}")

    print(f"\n总成本: ¥{total_cost:.2f}")
```

### 示例5: 成本优化分析

```python
from engines.model_scheduler_remenbaike import RembaikeModelScheduler
from models import Shot, ShotType, ActType

async def cost_optimization_analysis():
    """成本优化分析"""

    scheduler = RembaikeModelScheduler()

    # 创建测试分镜
    shots = [
        Shot(i, ShotType.PRODUCT, ActType.ACT2, f"产品{i}", f"文案{i}", 5.0)
        for i in range(1, 21)  # 20个分镜
    ]

    # 先分配模型（无预算限制）
    assigned_shots, original_cost = scheduler.batch_assign_models(
        shots=shots,
        total_budget=None,
        quality_priority=True
    )

    print(f"原始成本: ¥{original_cost:.2f}")

    # 生成优化方案
    optimization_plan = scheduler.get_optimization_plan(
        shots=assigned_shots,
        target_budget=25.0  # 目标预算25元
    )

    print(f"\n=== 优化方案 ===")
    print(f"优化后成本: ¥{optimization_plan.optimized_cost:.2f}")
    print(f"节省: ¥{optimization_plan.savings:.2f} ({optimization_plan.savings_percentage:.1f}%)")
    print(f"质量影响: {optimization_plan.quality_impact}")

    print(f"\n优化动作:")
    for action in optimization_plan.optimization_actions:
        print(f"  分镜{action['shot_id']}: {action['original_model']} → {action['new_model']}")
```

### 示例6: 使用优化预设

```python
from optimization_presets import (
    estimate_cost,
    compare_presets,
    recommend_preset,
    OPTIMIZATION_PRESETS
)

async def use_optimization_presets():
    """使用优化预设"""

    shot_count = 30

    # 1. 估算成本
    print("=== 成本估算 ===")
    estimate = estimate_cost(shot_count, "balanced")
    print(f"预设: {estimate['preset_name']}")
    print(f"总成本: ¥{estimate['total_cost']:.2f}")
    print(f"预计时间: {estimate['estimated_time_minutes']:.1f}分钟")

    # 2. 比较所有预设
    print("\n=== 预设对比 ===")
    comparisons = compare_presets(shot_count)
    for comp in comparisons:
        print(f"{comp['preset_name']}: ¥{comp['total_cost']:.2f}, {comp['estimated_time_minutes']:.1f}分钟")

    # 3. 智能推荐
    print("\n=== 智能推荐 ===")
    recommended = recommend_preset(
        shot_count=30,
        budget=40.0,
        time_limit_minutes=None,
        quality_requirement="high"
    )
    print(f"推荐预设: {recommended}")
    preset_info = OPTIMIZATION_PRESETS[recommended]
    print(f"描述: {preset_info['description']}")
```

---

## 实战案例

### 案例1: 电商产品视频

```python
async def ecommerce_product_video():
    """电商产品视频 - 1分钟完整介绍"""

    from models import ProductProfile

    product = ProductProfile(
        name="蓝牙降噪耳机 Pro",
        category="数码配件",
        selling_points=[
            "主动降噪50dB",
            "30小时续航",
            "HiFi音质",
            "佩戴舒适"
        ],
        core_value="沉浸式音乐体验",
        target_audience="音乐爱好者",
        tone="专业",
        keywords=["降噪", "音质", "续航", "舒适"]
    )

    yuyi = YuyiProRemenbaike()

    result = await yuyi.create_video(
        topic="蓝牙降噪耳机 Pro - 让音乐更纯粹",
        target_duration=60,
        product=product,
        total_budget=35.0,
        quality_priority=True,  # 产品视频要求高质量
        style="professional"
    )

    # 查看爆款预测
    prediction = result["prediction"]
    print(f"\n=== 爆款分析 ===")
    print(f"总分: {prediction.total_score:.1f}/100")
    print(f"爆款概率: {prediction.viral_probability:.1%}")

    if prediction.suggestions:
        print(f"\n优化建议:")
        for suggestion in prediction.suggestions:
            print(f"  - {suggestion}")

    return result

asyncio.run(ecommerce_product_video())
```

### 案例2: 教程视频系列

```python
async def tutorial_series():
    """教程视频系列 - 批量生成"""

    tutorials = [
        {
            "topic": "Python入门 - 第1课: 变量和数据类型",
            "duration": 120,
            "style": "educational"
        },
        {
            "topic": "Python入门 - 第2课: 条件语句和循环",
            "duration": 150,
            "style": "educational"
        },
        {
            "topic": "Python入门 - 第3课: 函数和模块",
            "duration": 180,
            "style": "educational"
        },
    ]

    yuyi = YuyiProRemenbaike()
    results = []

    for tutorial in tutorials:
        print(f"\n生成: {tutorial['topic']}")

        result = await yuyi.create_video(
            topic=tutorial["topic"],
            target_duration=tutorial["duration"],
            total_budget=50.0,  # 教程视频可以有较高预算
            quality_priority=True,
            style=tutorial["style"]
        )

        results.append(result)

        # 等待避免限流
        await asyncio.sleep(5)

    # 统计
    total_shots = sum(r["stats"]["total_shots"] for r in results)
    total_cost = sum(r["stats"]["estimated_cost"] for r in results)
    avg_score = sum(r["stats"]["viral_score"] for r in results) / len(results)

    print(f"\n=== 系列视频统计 ===")
    print(f"总分镜数: {total_shots}")
    print(f"总成本: ¥{total_cost:.2f}")
    print(f"平均爆款分数: {avg_score:.1f}/100")

asyncio.run(tutorial_series())
```

### 案例3: 社交媒体广告

```python
async def social_media_ads():
    """社交媒体广告 - A/B测试"""

    yuyi = YuyiProRemenbaike()

    # 生成多个版本用于A/B测试
    versions = [
        {
            "topic": "限时优惠！立省300元",
            "style": "urgent"
        },
        {
            "topic": "高品质生活，从这里开始",
            "style": "elegant"
        },
        {
            "topic": "99%的人都推荐的产品",
            "style": "social_proof"
        }
    ]

    results = []

    for i, version in enumerate(versions, 1):
        print(f"\n生成版本{i}: {version['topic']}")

        result = await yuyi.create_video(
            topic=version["topic"],
            target_duration=15,  # 15秒短广告
            total_budget=10.0,
            quality_priority=False,  # 速度优先，快速测试
            style="advertising"
        )

        results.append({
            "version": i,
            "topic": version["topic"],
            "viral_score": result["stats"]["viral_score"],
            "viral_probability": result["stats"]["viral_probability"],
            "output": result["output_dir"]
        })

    # 选择最佳版本
    best = max(results, key=lambda x: x["viral_score"])

    print(f"\n=== A/B测试结果 ===")
    for r in results:
        print(f"版本{r['version']}: {r['viral_score']:.1f}分 (爆款概率: {r['viral_probability']:.1%})")

    print(f"\n🏆 推荐使用版本{best['version']}: {best['topic']}")

asyncio.run(social_media_ads())
```

---

## 最佳实践

### 实践1: 错误处理

```python
async def robust_video_creation():
    """带完整错误处理的视频生成"""

    yuyi = YuyiProRemenbaike()

    try:
        result = await yuyi.create_video(
            topic="测试主题",
            target_duration=60,
            total_budget=20.0,
            quality_priority=False
        )

        if result["success"]:
            # 检查成功率
            success_rate = result["stats"]["success_count"] / result["stats"]["total_shots"]

            if success_rate >= 0.8:
                print("✅ 生成成功，质量良好")
            else:
                print(f"⚠️  生成完成，但成功率较低: {success_rate:.1%}")

            # 保存结果信息
            import json
            with open(f"{result['output_dir']}/info.json", "w", encoding="utf-8") as f:
                json.dump({
                    "topic": "测试主题",
                    "stats": result["stats"],
                    "viral_score": result["stats"]["viral_score"]
                }, f, ensure_ascii=False, indent=2)

        else:
            print("❌ 生成失败")

    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(robust_video_creation())
```

### 实践2: 日志和监控

```python
from loguru import logger
import time

async def monitored_video_creation():
    """带监控的视频生成"""

    start_time = time.time()

    yuyi = YuyiProRemenbaike()

    logger.info("开始视频生成")

    result = await yuyi.create_video(
        topic="监控测试",
        target_duration=60,
        total_budget=20.0,
        quality_priority=False
    )

    elapsed = time.time() - start_time

    # 记录关键指标
    logger.info(f"生成完成，耗时: {elapsed/60:.1f}分钟")
    logger.info(f"成功率: {result['stats']['success_count']}/{result['stats']['total_shots']}")
    logger.info(f"成本: ¥{result['stats']['estimated_cost']:.2f}")
    logger.info(f"爆款分数: {result['stats']['viral_score']:.1f}")

    # 检查是否超时
    if elapsed > 600:  # 10分钟
        logger.warning("生成时间过长!")

    # 检查是否超预算
    if result["stats"]["estimated_cost"] > 25.0:
        logger.warning("成本超出预期!")

asyncio.run(monitored_video_creation())
```

### 实践3: 性能优化

```python
async def optimized_batch_creation():
    """优化的批量生成"""

    from optimization_presets import recommend_preset, estimate_cost

    yuyi = YuyiProRemenbaike()

    # 场景: 需要生成10个视频，预算100元，时间限制10分钟
    video_count = 10
    total_budget = 100.0
    time_limit = 10  # 分钟

    # 计算单个视频预算和时间
    per_video_budget = total_budget / video_count
    per_video_time = time_limit / video_count

    # 根据约束推荐预设
    preset = recommend_preset(
        shot_count=12,  # 假设每个视频12个分镜
        budget=per_video_budget,
        time_limit_minutes=per_video_time,
        quality_requirement="medium"
    )

    print(f"推荐预设: {preset}")

    # 使用推荐预设批量生成
    for i in range(video_count):
        result = await yuyi.create_video(
            topic=f"视频{i+1}",
            target_duration=60,
            total_budget=per_video_budget,
            quality_priority=(preset != "ultra_low_cost"),  # 根据预设决定
            style="marketing"
        )

        print(f"视频{i+1}: ¥{result['stats']['estimated_cost']:.2f}")

        await asyncio.sleep(2)

asyncio.run(optimized_batch_creation())
```

---

## 📝 总结

这些示例涵盖了从基础到高级的各种使用场景。根据你的需求选择合适的示例开始。

**快速选择指南：**

- 新手入门 → 示例1、2
- 批量生产 → 示例3、案例2
- 成本优化 → 示例5、示例6
- 高质量视频 → 案例1
- A/B测试 → 案例3
- 生产环境 → 实践1、2、3

更多问题请查看 [README_REMENBAIKE.md](README_REMENBAIKE.md)
