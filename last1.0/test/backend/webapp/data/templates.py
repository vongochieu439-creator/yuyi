# -*- coding: utf-8 -*-
"""
爆款模板库 - 整合头部KOL、MCN机构、营销方法论的内容结构模板
每个模板来源可追溯，让用户看到"这来自谁"，提升价值感知
"""

TEMPLATE_LIBRARY = [

    # ==================== KOL 风格模板 ====================

    {
        "template_id": "lijiaqi_beauty",
        "name": "李佳琦种草公式",
        "source": {
            "type": "kol",
            "name": "李佳琦",
            "label": "抖音/淘宝直播·头部美妆主播",
            "followers": "7000万+",
            "bio": "连续多年双十一销售额第一，创造'OMG买它'文化，美妆种草界标杆",
            "avatar_hint": "energetic beauty influencer, studio background, ring light"
        },
        "suitable_categories": ["美妆", "护肤", "彩妆", "香水", "个人护理", "保健品", "零食"],
        "unsuitable_for": ["B端产品", "工业品", "房产", "金融"],
        "tags": ["种草", "激情", "美妆", "感染力", "冲动消费"],
        "core_strategy": "用极致情绪感染力制造冲动消费，上脸/使用过程是核心，价格揭晓是高潮",
        "structure": {
            "act1": {
                "name": "激情惊叹开场",
                "ratio": 0.20,
                "description": "开头1-3秒用高分贝惊叹词直接抓注意力，点明产品并给出震惊结论",
                "shot_types": ["opening", "talking_head"],
                "emotion": "兴奋、惊喜"
            },
            "act2": {
                "name": "沉浸式上脸/使用",
                "ratio": 0.60,
                "description": "详细展示使用过程：质地、上脸感受、效果变化，持续输出惊叹和赞美，穿插与其他产品的对比",
                "shot_types": ["hands_on", "product", "comparison", "talking_head"],
                "emotion": "专注、陶醉、满足"
            },
            "act3": {
                "name": "价格爆点+催购",
                "ratio": 0.20,
                "description": "价格揭晓制造惊喜感（要么超便宜，要么物超所值），连续重复'买它'制造紧迫感",
                "shot_types": ["talking_head", "closing"],
                "emotion": "紧迫、催促"
            }
        },
        "hook_formula": "OMG！这个{产品名}也太{核心优点}了吧！！",
        "narration_style": "大量感叹号，高频重复关键词，口语化，情绪外放，'天哪''绝了''买它'等词高频出现",
        "narration_examples": [
            "OMG这个也太好用了吧！我的天哪！",
            "质地绝了！上脸之后你们感受一下！",
            "买它！买它！买它！！这个价格真的太值了！"
        ],
        "key_shots": ["超近距离产品特写", "上脸/使用特写", "使用前后对比", "主播直视镜头激情讲解"],
        "best_duration": "60-90秒"
    },

    {
        "template_id": "zhangtonxue_lifestyle",
        "name": "张同学生活流叙事",
        "source": {
            "type": "kol",
            "name": "张同学",
            "label": "抖音·生活纪实类头部博主",
            "followers": "2000万+",
            "bio": "以真实农村生活第一视角出圈，开创'生活流'短视频范式，强调烟火气和真实感",
            "avatar_hint": "rural lifestyle, natural lighting, authentic daily life scene"
        },
        "suitable_categories": ["食品", "农副产品", "家居", "厨具", "日用品", "地方特产"],
        "unsuitable_for": ["高端奢侈品", "科技产品", "金融", "B端"],
        "tags": ["生活流", "真实感", "沉浸式", "烟火气", "第一视角"],
        "core_strategy": "产品自然融入真实生活场景，不是在卖东西，而是在展示生活，观众产生'我也想要这种生活'的向往",
        "structure": {
            "act1": {
                "name": "生活场景引入",
                "ratio": 0.25,
                "description": "第一视角展示真实生活场景，让观众有代入感，产品自然出现在生活中",
                "shot_types": ["broll", "opening"],
                "emotion": "平静、真实、亲切"
            },
            "act2": {
                "name": "产品融入过程",
                "ratio": 0.55,
                "description": "在真实劳作/生活过程中展示产品的使用，重在'用'而不是'展示'，画面语言胜过口播",
                "shot_types": ["hands_on", "broll", "product"],
                "emotion": "专注、享受"
            },
            "act3": {
                "name": "生活化收尾",
                "ratio": 0.20,
                "description": "用真实生活状态收尾，产品的价值通过最终画面自然呈现，弱化卖货感",
                "shot_types": ["broll", "closing"],
                "emotion": "满足、归属感"
            }
        },
        "hook_formula": "今天{真实场景描述}，顺手用了{产品名}……",
        "narration_style": "口语化、克制、不夸张，大量留白和沉默，画面说话为主，文字为辅，像在记录生活而非卖货",
        "narration_examples": [
            "今早起来，地里的活儿得干了。",
            "用这个弄起来，省了不少劲儿。",
            "晚上吃了顿好的，踏实。"
        ],
        "key_shots": ["第一视角劳作场景", "产品使用俯拍", "自然光线", "环境空镜"],
        "best_duration": "60-120秒"
    },

    {
        "template_id": "luoyonghao_tech",
        "name": "罗永浩极致产品主义",
        "source": {
            "type": "kol",
            "name": "罗永浩·交个朋友",
            "label": "抖音·交个朋友直播间创始人",
            "followers": "2900万+",
            "bio": "以深度产品讲解和真诚人设著称，'交个朋友'模式开创数码/工具类深度带货新范式",
            "avatar_hint": "confident male presenter, clean studio, professional lighting, tech product"
        },
        "suitable_categories": ["3C数码", "家电", "工具", "软件", "课程", "汽车"],
        "unsuitable_for": ["美妆", "零食", "快消品"],
        "tags": ["技术流", "深度讲解", "理性", "真诚", "参数对比"],
        "core_strategy": "把产品当成有灵魂的作品来讲，用逻辑和数据建立信任，自嘲增加亲和力，让观众觉得'他真的懂这个'",
        "structure": {
            "act1": {
                "name": "破局开场",
                "ratio": 0.15,
                "description": "提出一个行业痛点或认知误区，制造思考，让观众觉得'对，我也有这个问题'",
                "shot_types": ["talking_head", "opening"],
                "emotion": "思考、共鸣"
            },
            "act2": {
                "name": "深度拆解产品",
                "ratio": 0.65,
                "description": "逐条讲解产品设计细节，每个功能都有设计理由，用对比数据支撑，穿插自嘲和实测",
                "shot_types": ["product", "hands_on", "comparison", "talking_head"],
                "emotion": "专注、折服"
            },
            "act3": {
                "name": "真诚推荐收尾",
                "ratio": 0.20,
                "description": "用'我自己也在用'的真诚姿态收尾，说清楚适合什么人，不适合什么人，价格定锚",
                "shot_types": ["talking_head", "closing"],
                "emotion": "真诚、信任"
            }
        },
        "hook_formula": "我用了{时间}研究{产品名}，发现了一个很多人不知道的事情……",
        "narration_style": "逻辑严密，有条理，偶尔自嘲，语速适中，数据具体，不夸大，说'适合什么人/不适合什么人'",
        "narration_examples": [
            "很多人选这类产品，犯了一个根本性的错误。",
            "这个设计，乍一看没什么，但你仔细想想……",
            "我说句实话，它也有缺点，就是……"
        ],
        "key_shots": ["手持产品近景讲解", "参数/数据动态图表", "实测对比镜头", "细节特写"],
        "best_duration": "90-180秒"
    },

    {
        "template_id": "liziqi_aesthetic",
        "name": "李子柒唯美生活方式",
        "source": {
            "type": "kol",
            "name": "李子柒",
            "label": "抖音/YouTube·生活美学类全球头部博主",
            "followers": "1.7亿(YouTube)+5000万(国内)",
            "bio": "田园生活美学标杆，用极致视觉叙事打造产品向往感，是'情感价值>功能价值'的典型范式",
            "avatar_hint": "beautiful rural scenery, traditional Chinese elements, natural lighting, dreamy atmosphere"
        },
        "suitable_categories": ["食品", "传统手工艺", "茶叶", "家居", "文创", "美妆（天然系）"],
        "unsuitable_for": ["科技产品", "金融", "B端", "快消品"],
        "tags": ["唯美", "慢生活", "情感", "文化", "高级感"],
        "core_strategy": "用极致美好的视觉叙事让产品成为一种生活方式的象征，几乎不讲功能，让画面和情感说话",
        "structure": {
            "act1": {
                "name": "唯美场景铺垫",
                "ratio": 0.30,
                "description": "用极致唯美的自然/生活画面引入，建立情感氛围，不急于展示产品",
                "shot_types": ["broll", "opening"],
                "emotion": "宁静、向往"
            },
            "act2": {
                "name": "产品与生活融合",
                "ratio": 0.50,
                "description": "产品在自然环境或传统工艺场景中呈现，每一帧都是一幅画，产品是美好生活的一部分",
                "shot_types": ["product", "hands_on", "broll"],
                "emotion": "专注、陶醉"
            },
            "act3": {
                "name": "情感升华收尾",
                "ratio": 0.20,
                "description": "以情感和意境收尾，留给观众一种对这种生活的向往和想象",
                "shot_types": ["broll", "closing"],
                "emotion": "意犹未尽、向往"
            }
        },
        "hook_formula": "在{唯美场景}里，{诗意动作}……",
        "narration_style": "极简或无口播，若有台词则诗意、文学化，语速极慢，靠画面叙事，背景音乐比口播更重要",
        "narration_examples": [
            "春天来了，又到了做{产品}的时候。",
            "这样的日子，慢慢的，很好。",
            "（大部分镜头无口播，靠自然声音）"
        ],
        "key_shots": ["自然光线大景", "产品与自然环境融合", "双手劳作特写", "金色光线"],
        "best_duration": "90-180秒"
    },

    {
        "template_id": "papijian_fastcut",
        "name": "papi酱快剪吐槽流",
        "source": {
            "type": "kol",
            "name": "papi酱",
            "label": "抖音·生活吐槽类头部博主",
            "followers": "3000万+",
            "bio": "最早将快剪+自嘲+共鸣型内容带火，开创'痛点夸张化+解决方案'的种草范式",
            "avatar_hint": "young woman, expressive face, fast-paced editing, relatable daily life scenario"
        },
        "suitable_categories": ["服务类", "App/软件", "日用品", "食品", "效率工具", "教育"],
        "unsuitable_for": ["高端奢侈品", "工业品", "B端"],
        "tags": ["快节奏", "共鸣", "吐槽", "自嘲", "都市人"],
        "core_strategy": "把用户痛点夸张化演绎，让观众一边笑一边点头说'就是我'，然后产品作为救星出现",
        "structure": {
            "act1": {
                "name": "痛点夸张演绎",
                "ratio": 0.30,
                "description": "用夸张的表演/场景演绎目标用户最熟悉的痛点，让人'被说中'",
                "shot_types": ["opening", "talking_head", "broll"],
                "emotion": "共鸣、好笑"
            },
            "act2": {
                "name": "产品登场解围",
                "ratio": 0.45,
                "description": "产品像救星一样出现，快速展示解决痛点的过程，保持轻松幽默的基调",
                "shot_types": ["product", "hands_on", "talking_head"],
                "emotion": "轻松、惊喜、解脱"
            },
            "act3": {
                "name": "反转收尾",
                "ratio": 0.25,
                "description": "用反转或自嘲式收尾，给整个视频画上幽默的句点，最后带出CTA",
                "shot_types": ["talking_head", "closing"],
                "emotion": "幽默、轻松"
            }
        },
        "hook_formula": "每次{痛点场景}，我都{夸张反应}，直到我发现了{产品名}……",
        "narration_style": "语速快，快剪节奏，大量口语化表达，自嘲，'所以说''你们懂吗''我TM直接'等口头禅",
        "narration_examples": [
            "每次加班到十二点，打开外卖APP，我直接傻了。",
            "说真的，用了这个之后，人生都不一样了。",
            "所以说，救我狗命的就是它。"
        ],
        "key_shots": ["表情特写", "痛点场景还原", "产品快速展示", "before/after"],
        "best_duration": "30-60秒"
    },

    {
        "template_id": "kuangshaoyangge_reversal",
        "name": "疯狂小杨哥反转爆梗",
        "source": {
            "type": "kol",
            "name": "疯狂小杨哥·三只羊网络",
            "label": "抖音·全品类娱乐带货头部主播",
            "followers": "1亿+",
            "bio": "以夸张表演+反转梗+家庭互动带货见长，下沉市场覆盖广，爆款率极高",
            "avatar_hint": "energetic young man, family setting, exaggerated expressions, rural/suburban background"
        },
        "suitable_categories": ["食品", "日用品", "零食", "家居", "玩具", "下沉市场商品"],
        "unsuitable_for": ["高端奢侈品", "专业技术产品"],
        "tags": ["夸张", "反转", "下沉市场", "家庭", "爆梗", "娱乐化"],
        "core_strategy": "夸张的开场预期+反转带来笑点，娱乐性拉满，产品自然植入，下沉市场极强共鸣",
        "structure": {
            "act1": {
                "name": "夸张预期设置",
                "ratio": 0.25,
                "description": "用夸张表演或极端说法设置一个高预期，让观众以为要发生某件事",
                "shot_types": ["opening", "talking_head"],
                "emotion": "好奇、期待"
            },
            "act2": {
                "name": "产品体验+梗点",
                "ratio": 0.50,
                "description": "展示产品过程中穿插爆梗反应，夸张的惊喜或夸张的嫌弃（欲扬先抑），互动感强",
                "shot_types": ["hands_on", "product", "talking_head"],
                "emotion": "好笑、惊喜"
            },
            "act3": {
                "name": "反转收尾+催购",
                "ratio": 0.25,
                "description": "一个出乎意料的反转收尾，然后直接且粗暴地催购，干净利落",
                "shot_types": ["talking_head", "closing"],
                "emotion": "痛快、好笑"
            }
        },
        "hook_formula": "今天我哥/我弟给我寄了个{产品名}，我一看……直接{夸张反应}",
        "narration_style": "口语极度夸张，不讲文法，大量语气词，偶有方言，节奏快，'我滴个乖乖''绝了啊''这玩意儿'",
        "narration_examples": [
            "我滴个乖乖，这是什么东西？！",
            "不是，这个真的绝了啊，我之前怎么不知道！",
            "就这价，买它！不买是傻子！"
        ],
        "key_shots": ["夸张表情特写", "家庭/生活背景", "产品开箱", "惊讶反应"],
        "best_duration": "30-60秒"
    },

    # ==================== MCN 机构模板 ====================

    {
        "template_id": "meione_polished",
        "name": "美ONE精致种草法",
        "source": {
            "type": "mcn",
            "name": "美ONE（薇娅团队）",
            "label": "头部MCN·谦寻文化母公司",
            "bio": "培育出薇娅等头部主播，擅长精致化产品呈现，种草成功率行业顶尖",
            "avatar_hint": "elegant studio setting, professional product photography, soft lighting"
        },
        "suitable_categories": ["美妆", "护肤", "时尚", "家居", "母婴", "轻奢"],
        "unsuitable_for": ["低客单价快消品", "工业品"],
        "tags": ["精致", "种草", "品质感", "信任背书", "场景化"],
        "core_strategy": "营造精致生活场景，让产品成为升级生活品质的解决方案，用真实使用场景+KOL信任背书双重推动",
        "structure": {
            "act1": {
                "name": "精致场景引入",
                "ratio": 0.20,
                "description": "高质感画面引出产品所适配的精致生活场景，让观众产生向往",
                "shot_types": ["broll", "opening"],
                "emotion": "向往、精致"
            },
            "act2": {
                "name": "产品全维度展示",
                "ratio": 0.55,
                "description": "从外观、成分/材质、使用效果多角度展示，每个卖点都有场景支撑，真实用户反馈穿插",
                "shot_types": ["product", "hands_on", "comparison", "talking_head"],
                "emotion": "信任、心动"
            },
            "act3": {
                "name": "价值感收尾",
                "ratio": 0.25,
                "description": "强调产品带来的生活品质提升，给出明确购买理由，CTA自然不突兀",
                "shot_types": ["talking_head", "closing"],
                "emotion": "满足、行动"
            }
        },
        "hook_formula": "如果你也想要{美好生活状态}，这个{产品名}你一定要看看",
        "narration_style": "温柔、精致，语速适中，措辞考究，'质感''细腻''值得'等词高频，像闺蜜推荐而非卖货",
        "narration_examples": [
            "最近发现了一个真的很有质感的东西。",
            "用起来那种感觉，真的很难描述，就是很对。",
            "这种细节，一看就知道是用心做的。"
        ],
        "key_shots": ["精致产品棚拍", "使用场景美化", "细节特写", "温暖色调"],
        "best_duration": "60-90秒"
    },

    {
        "template_id": "jiaogepengyou_value",
        "name": "交个朋友极致性价比",
        "source": {
            "type": "mcn",
            "name": "交个朋友（罗永浩团队）",
            "label": "抖音头部带货机构·直播电商标杆",
            "bio": "以极致选品+价格锚定+真实测评著称，打造'不赚差价只收服务费'的信任模型",
            "avatar_hint": "clean livestream studio, product display table, confident presenter"
        },
        "suitable_categories": ["全品类", "标品", "家电", "食品", "日用品", "美妆"],
        "unsuitable_for": ["非标品", "价格不透明品类"],
        "tags": ["性价比", "真实测评", "价格锚定", "信任感", "全品类"],
        "core_strategy": "极致价格力+真实测评双轮驱动，先用对标品牌/价格锚定，再用亲测体验击穿犹豫",
        "structure": {
            "act1": {
                "name": "价格锚定开场",
                "ratio": 0.20,
                "description": "先报出竞品价格或市场均价，再亮出本品价格，制造巨大性价比冲击",
                "shot_types": ["opening", "talking_head"],
                "emotion": "震惊、好奇"
            },
            "act2": {
                "name": "真实测评主体",
                "ratio": 0.55,
                "description": "逐项测评核心功能，数据和实测结合，客观说优缺点，建立'不骗人'人设",
                "shot_types": ["product", "hands_on", "comparison"],
                "emotion": "信任、理性"
            },
            "act3": {
                "name": "直接催购",
                "ratio": 0.25,
                "description": "直接说'这就是今天的最低价'，限时限量，干净利落，不绕弯子",
                "shot_types": ["talking_head", "closing"],
                "emotion": "紧迫、行动"
            }
        },
        "hook_formula": "同款在{竞品平台}卖{高价}，今天给大家拿到了{低价}……",
        "narration_style": "直接、干脆、有底气，数字具体，'全网最低''今天这个价''不买亏了'但有真实依据",
        "narration_examples": [
            "同款在京东卖368，今天我给大家拿到了199。",
            "我自己用了三个月，说实话，就一个缺点……",
            "今天这个价，过了就没有了，不是套路。"
        ],
        "key_shots": ["价格对比字幕", "产品实测特写", "使用前后对比"],
        "best_duration": "60-90秒"
    },

    # ==================== 方法论框架模板 ====================

    {
        "template_id": "pas_formula",
        "name": "PAS痛点公式",
        "source": {
            "type": "methodology",
            "name": "PAS营销框架",
            "label": "经典营销方法论·Problem-Agitate-Solution",
            "bio": "源自直销行业的黄金文案公式，被全球顶尖营销人广泛使用，以精准痛点攻破心理防线",
            "avatar_hint": "marketing methodology visualization, clean infographic style"
        },
        "suitable_categories": ["功能性产品", "效率工具", "健康保健", "教育", "服务", "金融"],
        "unsuitable_for": ["纯情感型产品", "奢侈品"],
        "tags": ["痛点", "逻辑", "转化", "功能性", "理性"],
        "core_strategy": "三步走：点出用户真实痛点 → 放大痛苦的后果和危害 → 产品作为唯一正确解法出现",
        "structure": {
            "act1": {
                "name": "P·精准点痛",
                "ratio": 0.25,
                "description": "精准描述目标用户的具体痛点场景，要用'你是不是也……'的共鸣句式，让观众觉得被说中",
                "shot_types": ["opening", "broll", "talking_head"],
                "emotion": "共鸣、被说中"
            },
            "act2": {
                "name": "A·放大痛苦 + S·解决方案",
                "ratio": 0.55,
                "description": "先放大不解决这个痛点的后果（后果越严重越好），在痛苦到顶点时引出产品作为解决方案，逐步展示如何解决",
                "shot_types": ["talking_head", "product", "hands_on", "comparison"],
                "emotion": "焦虑、期待、解脱"
            },
            "act3": {
                "name": "结果确认+CTA",
                "ratio": 0.20,
                "description": "展示解决后的美好结果，与开头痛点形成鲜明对比，给出明确的行动指令",
                "shot_types": ["comparison", "closing"],
                "emotion": "解脱、满足、行动"
            }
        },
        "hook_formula": "你有没有遇到过这种情况：{精准痛点场景}……",
        "narration_style": "理性逻辑，层层递进，有因果关系，'如果不……就会……''正是因为……所以……'",
        "narration_examples": [
            "你有没有遇到过这种情况：{痛点场景}，我以前也是。",
            "如果不解决这个问题，你会发现……（后果越来越严重）",
            "直到我用了{产品}，这个问题才彻底解决了。"
        ],
        "key_shots": ["痛点场景还原", "后果可视化", "产品解决过程", "结果对比"],
        "best_duration": "45-90秒"
    },

    {
        "template_id": "aida_funnel",
        "name": "AIDA注意力漏斗",
        "source": {
            "type": "methodology",
            "name": "AIDA营销模型",
            "label": "百年营销经典·Attention-Interest-Desire-Action",
            "bio": "1898年由Elias St. Elmo Lewis提出，至今仍是品牌广告和内容营销的底层逻辑",
            "avatar_hint": "classic marketing funnel visualization, professional advertising style"
        },
        "suitable_categories": ["新品发布", "品牌推广", "高客单价", "奢侈品", "课程", "服务"],
        "unsuitable_for": ["冲动消费快消品"],
        "tags": ["品牌", "新品", "高客单", "循序渐进", "品质感"],
        "core_strategy": "四步递进：先夺注意力 → 建立兴趣 → 激发欲望 → 促成行动，适合需要理性决策的品类",
        "structure": {
            "act1": {
                "name": "A·夺注意力",
                "ratio": 0.15,
                "description": "用一个视觉冲击、数字震惊或反常识的开场瞬间抓住眼球",
                "shot_types": ["opening"],
                "emotion": "震惊、好奇"
            },
            "act2": {
                "name": "I·建兴趣 + D·激欲望",
                "ratio": 0.65,
                "description": "先介绍产品背景和独特性建立兴趣，再通过使用场景、效果展示、他人证明激发'我也要'的欲望",
                "shot_types": ["talking_head", "product", "hands_on", "broll"],
                "emotion": "兴趣、心动、欲望"
            },
            "act3": {
                "name": "A·促行动",
                "ratio": 0.20,
                "description": "给出明确的行动理由（限时/限量/特价/送礼）和简单的行动指令",
                "shot_types": ["closing", "talking_head"],
                "emotion": "紧迫、行动"
            }
        },
        "hook_formula": "99%的人不知道，{产品名}还可以这样用……",
        "narration_style": "专业而有吸引力，由浅入深，有故事感，语速由慢到快",
        "narration_examples": [
            "这个东西，你可能见过，但你不一定真的了解它。",
            "我第一次用的时候，真的没想到会有这种效果。",
            "现在还有限时折扣，机会不多，点击下方链接。"
        ],
        "key_shots": ["高冲击视觉开场", "产品故事化介绍", "使用场景美化", "CTA字幕"],
        "best_duration": "60-120秒"
    },

    {
        "template_id": "story_arc",
        "name": "故事弧线情感法",
        "source": {
            "type": "methodology",
            "name": "英雄旅程·故事弧线框架",
            "label": "好莱坞叙事结构·Joseph Campbell改编",
            "bio": "改编自坎贝尔'英雄旅程'，应用于商业内容创作，让产品成为消费者人生故事中的'神器'",
            "avatar_hint": "cinematic storytelling, emotional narrative, character journey visualization"
        },
        "suitable_categories": ["情感类产品", "礼品", "健康保健", "教育", "母婴", "宠物"],
        "unsuitable_for": ["纯功能型工具", "B端产品"],
        "tags": ["情感", "故事感", "共鸣", "转化", "记忆点"],
        "core_strategy": "用一个真实或虚构的人物故事来演绎产品的价值，观众被故事打动，产品的价值通过故事自然传递",
        "structure": {
            "act1": {
                "name": "人物困境",
                "ratio": 0.25,
                "description": "建立一个具体的人物和他/她面临的困境，观众能代入",
                "shot_types": ["broll", "opening", "talking_head"],
                "emotion": "共情、担忧"
            },
            "act2": {
                "name": "转折与产品登场",
                "ratio": 0.50,
                "description": "产品在关键节点出现，帮助人物完成转折，展示产品如何参与了这个故事",
                "shot_types": ["product", "hands_on", "broll"],
                "emotion": "转折、希望、感动"
            },
            "act3": {
                "name": "圆满收尾",
                "ratio": 0.25,
                "description": "人物状态改变，生活变好，情感高峰，产品成为这个美好结果的功臣",
                "shot_types": ["broll", "closing"],
                "emotion": "感动、满足、向往"
            }
        },
        "hook_formula": "三个月前，{人物}还在为{困境}发愁……",
        "narration_style": "叙事化，有人物有情节，情感真挚，语速平稳，像在讲一个真实发生的故事",
        "narration_examples": [
            "三个月前，她每天加班到深夜，回家只想倒头就睡。",
            "后来，朋友给她推荐了这个……",
            "现在，她说这是这一年做的最值的事情。"
        ],
        "key_shots": ["人物面部情绪", "生活场景还原", "产品使用转折", "美好结局画面"],
        "best_duration": "60-120秒"
    },

    {
        "template_id": "suspense_reveal",
        "name": "悬念揭秘反转公式",
        "source": {
            "type": "methodology",
            "name": "悬念叙事结构",
            "label": "综合自悬疑影视+内容营销·高完播率公式",
            "bio": "借鉴影视悬念创作手法，用好奇心驱动完播率，适合任何需要打破认知的产品",
            "avatar_hint": "mysterious opening, reveal moment visualization, high-contrast lighting"
        },
        "suitable_categories": ["新奇产品", "技术产品", "逆认知产品", "教育", "健康"],
        "unsuitable_for": ["认知已高的大众品"],
        "tags": ["悬念", "完播率", "反转", "好奇心", "高传播"],
        "core_strategy": "开头制造强烈好奇心，中间持续悬念不揭晓，结尾给出出乎意料的答案，完播率极高",
        "structure": {
            "act1": {
                "name": "悬念钩子",
                "ratio": 0.20,
                "description": "用一个反常识的结论、未完成的动作、或神秘的问题开场，让观众必须看下去",
                "shot_types": ["opening"],
                "emotion": "好奇、疑惑"
            },
            "act2": {
                "name": "逐步揭秘",
                "ratio": 0.55,
                "description": "一层一层剥开谜底，每揭示一层都给出新的惊喜，产品的展示成为解谜过程的一部分",
                "shot_types": ["product", "hands_on", "talking_head", "comparison"],
                "emotion": "期待、惊喜、折服"
            },
            "act3": {
                "name": "反转收尾",
                "ratio": 0.25,
                "description": "最终揭晓与开头呼应，给出出乎意料或情理之中的结论，余味悠长",
                "shot_types": ["closing", "talking_head"],
                "emotion": "恍然大悟、回味"
            }
        },
        "hook_formula": "千万别买{产品名}，除非你……（结尾揭晓）",
        "narration_style": "制造悬念感，留白多，语速节奏有张有弛，关键信息前停顿，'但是……''直到……''你猜怎么着'",
        "narration_examples": [
            "我研究了三个月，终于搞清楚为什么同样的{产品}差这么多。",
            "先别着急下结论……",
            "所以最后，我的选择是……（停顿）"
        ],
        "key_shots": ["神秘开场画面", "逐步揭秘镜头", "关键反转特写"],
        "best_duration": "45-90秒"
    }
]

# 按 template_id 建立索引，方便快速查找
TEMPLATE_INDEX = {t["template_id"]: t for t in TEMPLATE_LIBRARY}

# 所有品类标签，用于前端筛选
ALL_CATEGORIES = sorted(set(
    cat for t in TEMPLATE_LIBRARY for cat in t.get("suitable_categories", [])
))
