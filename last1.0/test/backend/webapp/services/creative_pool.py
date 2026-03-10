# -*- coding: utf-8 -*-
"""
创意博主池 - 按创意机制分类的博主名单

用于方向C跨行业创意迁移：从池中随机抽取不同类型博主，
拉取其爆款视频进行创意机制拆解和结构同构迁移。
"""
import random
from typing import List, Dict


# 创意博主池 - 按创意机制分类
CREATIVE_POOL: List[Dict] = [
    # === 反转剧情型 ===
    # 特征：看到最后才知道卖什么，剧情反转揭示品牌
    {
        "name": "李宗恒",
        "search_keyword": "李宗恒",
        "category": "反转剧情",
        "mechanism": "出其不意的反套路喜剧，结尾反转揭示产品",
        "signature_device": "先建立观众预期，再用意想不到的方式打破",
    },
    {
        "name": "吴夏帆",
        "search_keyword": "吴夏帆",
        "category": "反转剧情",
        "mechanism": "情感故事中自然植入产品，一眼心动式种草",
        "signature_device": "情感高潮时刻与产品功能绑定，让产品成为情节关键道具",
    },

    # === 情感共鸣型 ===
    # 特征：日常生活剧情引发情感共鸣，产品是情感载体
    {
        "name": "这是TA的故事",
        "search_keyword": "这是TA的故事",
        "category": "情感共鸣",
        "mechanism": "老夫老妻日常剧情触发情感共鸣，产品融入生活瞬间",
        "signature_device": "真实感的生活场景+意料之外的温情转折",
    },
    {
        "name": "多余和毛毛姐",
        "search_keyword": "多余和毛毛姐",
        "category": "情感共鸣",
        "mechanism": "夸张人设+生活化段子，娱乐中植入产品记忆点",
        "signature_device": "标志性人设表演让观众记住场景，产品绑定记忆锚点",
    },

    # === 极致实验型 ===
    # 特征：暴力测试/极端条件，用实验结果证明产品力
    {
        "name": "老爸评测",
        "search_keyword": "老爸评测",
        "category": "极致实验",
        "mechanism": "科学实验+数据说话，用客观测试结果建立信任",
        "signature_device": "实验室级别测试设备+可视化数据对比",
    },
    {
        "name": "疯狂小杨哥",
        "search_keyword": "疯狂小杨哥",
        "category": "极致实验",
        "mechanism": "极端条件暴力测试，夸张到荒谬的实验吸引眼球",
        "signature_device": "高价值物品x破坏性工具=认知冲突→反预期结果",
    },

    # === 泰式创意型 ===
    # 特征：不到最后不知道品牌，极致的悬念和反转
    {
        "name": "泰国创意广告",
        "search_keyword": "泰国创意广告 反转",
        "category": "悬念反转",
        "mechanism": "全程不出现品牌，用完整故事在最后3秒揭示产品",
        "signature_device": "信息极度不对称：观众全程不知道在看广告",
    },
    {
        "name": "泰国感人广告",
        "search_keyword": "泰国广告 感人 催泪",
        "category": "悬念反转",
        "mechanism": "情感催泪+品牌价值观输出，产品是精神符号而非功能展示",
        "signature_device": "3分钟完整短片叙事，最后10秒品牌升华",
    },

    # === 街头社交实验型 ===
    # 特征：真实街头互动，用路人反应证明产品效果
    {
        "name": "街头测试",
        "search_keyword": "街头测试 产品 路人反应",
        "category": "社交实验",
        "mechanism": "真实路人的即时反应=最强社交证据",
        "signature_device": "隐藏产品身份→路人体验→震惊反应→揭示品牌",
    },

    # === 科普可视化型 ===
    # 特征：用视觉化方式展示原理，让抽象功效变得直观
    {
        "name": "科普可视化",
        "search_keyword": "成分科普 显微镜 可视化",
        "category": "科普可视化",
        "mechanism": "微观放大/慢动作/特效，让不可见的功效变成可见的震撼",
        "signature_device": "显微镜/高速摄影/动画模拟，视觉冲击力=说服力",
    },

    # === 生活反差型 ===
    # 特征：日常场景中的意外反差，制造强烈对比
    {
        "name": "生活反差对比",
        "search_keyword": "素人改造 对比 前后",
        "category": "生活反差",
        "mechanism": "before/after的强烈视觉反差，用时间或场景切换制造冲击",
        "signature_device": "同一个人/物在使用前后的极端对比",
    },
]


def pick_creators(n: int = 2, exclude_categories: List[str] = None) -> List[Dict]:
    """
    从创意博主池中随机抽取n个不同类型的创意博主

    Args:
        n: 抽取数量
        exclude_categories: 需要排除的类别

    Returns:
        抽取的博主列表
    """
    exclude = set(exclude_categories or [])
    pool = [c for c in CREATIVE_POOL if c["category"] not in exclude]

    # 按类别分组
    by_category: Dict[str, List[Dict]] = {}
    for creator in pool:
        cat = creator["category"]
        by_category.setdefault(cat, []).append(creator)

    # 从不同类别中各抽1个，确保多样性
    categories = list(by_category.keys())
    random.shuffle(categories)

    picked = []
    for cat in categories[:n]:
        picked.append(random.choice(by_category[cat]))

    return picked


def get_all_categories() -> List[str]:
    """获取所有创意类别"""
    return list(set(c["category"] for c in CREATIVE_POOL))
