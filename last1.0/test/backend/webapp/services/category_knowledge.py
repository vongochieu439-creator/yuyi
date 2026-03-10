# -*- coding: utf-8 -*-
"""
品类知识库 - 为快速模式提供行业特定的内容模式、情绪触发和镜头指南
"""

CATEGORY_KNOWLEDGE = {
    "美妆护肤": {
        "hooks": [
            "实验对比: 左右脸对比/素颜vs上妆，视觉冲击力强",
            "成分党: 用显微镜/实验室画面展示核心成分",
            "反常识: '千万别这样涂面霜' 引发好奇",
            "痛点场景: 换季烂脸/熬夜暗沉等真实困扰",
        ],
        "structures": [
            "痛点切入→产品亮相→上脸实测→效果对比→限时优惠",
            "反常识开场→真相揭秘→产品介绍→使用教程→before/after",
            "成分科普→配方解析→质地展示→使用效果→总结推荐",
        ],
        "emotional_triggers": ["焦虑感(皮肤问题)", "期待感(变美)", "信任感(成分/实验)", "紧迫感(限时)"],
        "shot_guides": {
            "hook": "Close-up of skin texture/problem area, dramatic lighting, macro lens",
            "product": "Product hero shot with soft glow, rotating on marble surface",
            "demo": "Hands applying product on face, natural light, close-up of texture",
            "result": "Split-screen before/after, bright even lighting, genuine expression",
            "cta": "Product array with price tag overlay, warm inviting lighting",
        },
        "creative_approaches": ["实验对比", "痛点故事", "成分科普"],
    },
    "食品保健": {
        "hooks": [
            "食欲画面: 慢动作浇汁/切开特写，触发食欲",
            "健康焦虑: '你每天吃的XX可能在伤害你'",
            "数据震撼: '含有XX倍维生素C'等数据冲击",
            "场景代入: 加班深夜/健身后等场景触发共鸣",
        ],
        "structures": [
            "食欲画面→成分亮点→食用场景→口感描述→下单引导",
            "健康问题→解决方案→产品展示→食用方式→效果背书",
            "生活场景→痛点引出→产品登场→真实评价→优惠收尾",
        ],
        "emotional_triggers": ["食欲冲动", "健康焦虑", "便利感", "性价比"],
        "shot_guides": {
            "hook": "Slow-motion food preparation, steam rising, warm color grading",
            "product": "Product on natural wood surface with fresh ingredients around",
            "demo": "Person enjoying food/drink, genuine happy expression, lifestyle setting",
            "result": "Energetic person in daily life, bright and vibrant colors",
            "cta": "Product packaging with portion display, clean white background",
        },
        "creative_approaches": ["食欲诱惑", "健康科普", "场景种草"],
    },
    "数码3C": {
        "hooks": [
            "极端测试: 防水/摔落/极限环境测试，引发好奇",
            "开箱仪式: 精致开箱过程+第一反应",
            "效率对比: 有vs没有这个设备的工作效率对比",
            "隐藏功能: '99%的人不知道的XX功能'",
        ],
        "structures": [
            "开箱展示→外观细节→核心功能演示→使用场景→总结评价",
            "痛点场景→产品解决方案→功能逐一展示→性能测试→购买建议",
            "极端测试开场→产品介绍→日常使用→对比竞品→推荐理由",
        ],
        "emotional_triggers": ["科技感", "效率提升", "身份认同", "性价比"],
        "shot_guides": {
            "hook": "Dramatic product reveal, dark background with accent lighting, cinematic",
            "product": "Product rotating on tech-style platform, LED accent lights, clean angles",
            "demo": "Hands-on usage in real workspace, screen content visible, focused lighting",
            "result": "Side-by-side performance comparison, data overlay graphics",
            "cta": "Product with specs overlay, modern minimalist background",
        },
        "creative_approaches": ["极限测试", "效率对比", "隐藏功能揭秘"],
    },
    "服装鞋包": {
        "hooks": [
            "穿搭变身: 普通穿搭→时尚穿搭的转场切换",
            "场景展示: 通勤/约会/旅行等场景的穿搭方案",
            "细节特写: 面料质感/做工细节的极致展示",
            "反差对比: 价格vs质感的反差引发好奇",
        ],
        "structures": [
            "穿搭难题→方案展示→上身效果→细节特写→搭配建议",
            "场景切入→整体展示→细节放大→多角度展示→链接引导",
            "变身开场→单品介绍→面料展示→搭配推荐→限时优惠",
        ],
        "emotional_triggers": ["变美欲望", "社交需求", "性价比", "品质感"],
        "shot_guides": {
            "hook": "Fashion transformation transition, mirror reflection, bright natural light",
            "product": "Flat-lay product arrangement, textured background, overhead shot",
            "demo": "Model wearing product, multiple angles, outdoor/lifestyle setting",
            "result": "Full outfit reveal, confident walk, cinematic slow motion",
            "cta": "Product detail with price overlay, clean styled background",
        },
        "creative_approaches": ["穿搭变身", "场景种草", "质感展示"],
    },
    "家居生活": {
        "hooks": [
            "改造对比: 房间/角落改造前后的强烈对比",
            "生活痛点: 收纳困难/清洁难题等场景代入",
            "解压展示: 整理/清洁过程的治愈感画面",
            "效率展示: '1分钟搞定XX'的高效解决方案",
        ],
        "structures": [
            "杂乱场景→产品登场→使用过程→整洁效果→购买引导",
            "生活痛点→寻找方案→产品介绍→使用教程→效果展示",
            "改造前→改造过程→产品细节→改造后→氛围展示",
        ],
        "emotional_triggers": ["治愈感", "秩序感", "生活品质", "懒人友好"],
        "shot_guides": {
            "hook": "Messy room/area wide shot, before state, slightly desaturated",
            "product": "Product in styled home setting, warm ambient lighting",
            "demo": "Hands using product, satisfying process, ASMR-style close-up",
            "result": "Clean organized space, warm golden hour lighting, cozy vibe",
            "cta": "Product with lifestyle context, warm inviting atmosphere",
        },
        "creative_approaches": ["改造对比", "解压过程", "效率展示"],
    },
    "教育培训": {
        "hooks": [
            "焦虑引发: '你家孩子还在XX？同龄人已经...'",
            "成果展示: 学员真实成果/变化引发向往",
            "知识痛点: 常见误区/错误方法引发好奇",
            "数据冲击: 就业率/提分数据等强说服力内容",
        ],
        "structures": [
            "焦虑场景→问题分析→解决方案→课程介绍→限时优惠",
            "学员故事→痛点共鸣→课程亮点→成果展示→报名引导",
            "知识误区→正确方法→课程特色→师资展示→优惠活动",
        ],
        "emotional_triggers": ["焦虑感", "成长渴望", "竞争压力", "投资回报"],
        "shot_guides": {
            "hook": "Student struggling/parents worried, relatable home/school setting",
            "product": "Course interface/materials display, professional clean layout",
            "demo": "Engaging teaching moment, teacher-student interaction, bright classroom",
            "result": "Happy student with achievements, certificates, genuine celebration",
            "cta": "Course package with countdown timer overlay, professional branding",
        },
        "creative_approaches": ["焦虑共鸣", "成果展示", "误区纠正"],
    },
    "母婴": {
        "hooks": [
            "安全警示: '你给宝宝用的XX可能有隐患'",
            "萌娃画面: 可爱宝宝使用产品的温馨场景",
            "妈妈共鸣: 带娃辛苦/育儿焦虑等场景代入",
            "专家背书: 儿科医生/育儿专家推荐",
        ],
        "structures": [
            "育儿痛点→产品方案→安全认证→使用展示→妈妈推荐",
            "萌娃日常→问题出现→产品解决→宝宝开心→购买引导",
            "专家科普→常见误区→正确选择→产品推荐→优惠活动",
        ],
        "emotional_triggers": ["母爱本能", "安全焦虑", "育儿焦虑", "品质要求"],
        "shot_guides": {
            "hook": "Adorable baby close-up or concerned parent, warm soft lighting",
            "product": "Product with safety certifications visible, clean pastel background",
            "demo": "Parent using product with happy baby, warm home environment",
            "result": "Happy healthy baby, bright joyful colors, genuine moments",
            "cta": "Product lineup with trust badges, soft warm color palette",
        },
        "creative_approaches": ["安全科普", "萌娃种草", "妈妈真实分享"],
    },
    "其他": {
        "hooks": [
            "反常识: 打破常规认知引发好奇",
            "数据震撼: 用数据制造冲击力",
            "场景痛点: 日常生活中的真实困扰",
            "悬念设置: '看完这个视频你会...'",
        ],
        "structures": [
            "痛点引入→产品介绍→核心卖点→使用场景→行动号召",
            "悬念开场→问题展开→解决方案→效果展示→限时优惠",
            "故事引入→转折出现→产品亮相→价值呈现→购买引导",
        ],
        "emotional_triggers": ["好奇心", "解决问题的爽感", "性价比", "紧迫感"],
        "shot_guides": {
            "hook": "Eye-catching opening scene, dramatic lighting or unusual angle",
            "product": "Clean product hero shot, professional studio lighting",
            "demo": "Real person using product, natural setting, authentic feel",
            "result": "Satisfying result reveal, bright positive atmosphere",
            "cta": "Product with offer overlay, clean professional layout",
        },
        "creative_approaches": ["反常识", "痛点故事", "悬念叙事"],
    },
}


def get_category_knowledge(industry: str) -> dict:
    """获取品类知识，支持模糊匹配"""
    if not industry:
        return CATEGORY_KNOWLEDGE["其他"]

    # 精确匹配
    if industry in CATEGORY_KNOWLEDGE:
        return CATEGORY_KNOWLEDGE[industry]

    # 模糊匹配
    for key in CATEGORY_KNOWLEDGE:
        if key in industry or industry in key:
            return CATEGORY_KNOWLEDGE[key]

    return CATEGORY_KNOWLEDGE["其他"]
