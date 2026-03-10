# -*- coding: utf-8 -*-
"""
多Agent分镜提示词 V2 — 面向抖音卖货/涨粉短视频
Agent架构: Director(创意策划) → Screenwriter(分镜编剧) → Producer(质量把关)

核心理念: 不是写"广告分镜"，是写"博主种草脚本"
- 口播要像真人说话，有态度、有情绪、有口语碎片
- 画面要有创意实验/极致对比/场景故事，不是产品摆拍
- 每个镜头都有明确的"内容钩子"，不是流水账
"""

# ==================== 爆款参考范例（用于few-shot） ====================

EXAMPLE_SCRIPT_CLEANSER = """
【范例: 洗面奶 60秒种草脚本】

0-5s 暴力钩子:
  画面: 宏观特写，一颗娇嫩红草莓，博主将其按入一碗黑亮的工业机油和碳粉混合物中。草莓被拎起时，细小的孔洞里塞满了黑色油污，极像黑头鼻。博主在水龙头下冲洗草莓，黑油纹丝不动。
  口播: 这！是一颗沾满油的草莓。清水洗不掉这脏东西。普通洗面奶也洗不干净草莓鼻。
  卖点: 清洁痛点

5-10s 嗅觉刺激:
  画面: 近景，博主皱起眉头，把草莓凑到鼻尖闻了一下，露出一脸嫌弃的表情。
  口播: 你闻到了吗？这就是你堵了二十几年的油脂味道。
  卖点: 痛点戳心

10-18s 极致对比:
  画面: 特写，博主挤出洁面乳揉搓出泡沫，将泡沫覆盖草莓，指尖轻轻打圈。清水冲过，草莓瞬间恢复鲜红，孔洞里没有任何黑色残留。
  口播: 明明每天都在洗脸，却总感觉脸上油油的，很多时候不是你的皮肤底子有问题，而是你的洗脸方式彻底错了！最近我把洁面换成了华熙生物这个上市公司出的这款洗面奶。长得很低调，效果却很猛。
  卖点: 专利清洁/稳泡技术

18-28s 场景转换:
  画面: 快速转场，镜头切到博主在差旅的高铁站或健身房洗手间。博主从精致的洗漱包里快速掏出一支100g便携装，利索地挤出洁面在脸上快速揉搓。
  口播: 因为它是华熙生物这种上市大厂出的，成分里直接加了高级护肤品才有的里的玻尿酸。所以它是那种温和不刺激的流派，洗的过程就像在做修护。
  卖点: 100g便携装

28-38s 核心功效:
  画面: 中景，博主洗完脸，用毛巾按干。镜头推进，展示皮肤的水润感。屏幕侧边弹出"留存型玻尿酸"、"初颜舒PRO"等字样。博主用手指轻按脸颊，展示皮肤的回弹。
  口播: 特别是咱们出差怕头水土不服，或者平时皮肤敏感的，用这种带玻尿酸的洁面就特别安心。洗完之后不仅不假滑，感觉每个毛孔都在大口呼吸，肤感非常软糯。
  卖点: 玻尿酸锁水/舒缓泛红

45s+ 促单转化:
  画面: 博主特写，单手拿着产品，指着左下角的小黄车。
  口播: 而且大厂出品，价格却很克制，两位数就能买到这种级别的洁面，真的没必要去试那些乱七八糟的了。击视频下方小黄车，和我一起精致起来。
  卖点: 促单/性价比
"""


# ==================== Director Agent Prompts ====================

def get_director_prompt(product_name: str, product_detail: str = "",
                        industry: str = "", target_duration: int = 60,
                        reference_text: str = "", selling_points: list = None) -> str:
    """Director Agent: 创意策划 — 设计"内容创意概念"而非"广告镜头表" """
    sp_text = "\n".join(f"- {s}" for s in (selling_points or []))
    return f"""你是抖音千万级带货博主的内容策划总监。你策划的不是广告，是让人看完想买的"种草内容"。

## 产品信息
- 产品: {product_name}
- 行业: {industry or '根据产品判断'}
- 详情: {product_detail or '需要你根据产品常识补充'}
- 卖点:
{sp_text or '需要你根据产品和行业知识自行提炼3-5个具体卖点'}
- 参考: {reference_text or '无'}

## 你的核心任务

设计一个让人"停不下来"的种草视频创意方案。不是写广告脚本，是设计一个博主测评/种草视频的创意骨架。

## 输出JSON格式

```json
{{
  "creative_concept": {{
    "one_liner": "一句话概括创意核心（如：用草莓模拟黑头，实验证明清洁力）",
    "hook_device": "开场用什么创意装置抓人（如：视觉冲击实验/反常识数据/故事冲突/感官刺激）",
    "proof_method": "用什么方式证明产品好（如：极致对比实验/真人前后对比/数据测试/场景还原）",
    "emotion_journey": "情绪旅程（如：恶心→好奇→震惊→种草→紧迫）"
  }},
  "target_audience": {{
    "primary": "谁会看这个视频（具体人群+具体场景+具体痛点）",
    "scroll_stop_trigger": "第一帧出现什么画面，这个人会停下拇指（要极其具体）"
  }},
  "shot_plan": [
    {{
      "shot_id": 1,
      "segment_name": "暴力钩子",
      "act": "hook",
      "duration": 5,
      "creative_idea": "这个片段的创意点是什么（要具体，如：草莓按入机油模拟黑头堵塞）",
      "purpose": "让观众产生什么反应（如：视觉恶心+好奇这是在干嘛）",
      "target_emotion": "恶心/好奇",
      "intensity": 0.95,
      "shot_type": "macro_close_up",
      "camera_movement": "static"
    }},
    {{
      "shot_id": 2,
      "segment_name": "痛点戳心",
      "act": "problem",
      "duration": 5,
      "creative_idea": "如何让观众感同身受（如：嗅觉刺激+嫌弃表情引发共鸣）",
      "purpose": "观众OS：对对对我也是这样",
      "target_emotion": "共鸣/不适",
      "intensity": 0.8,
      "shot_type": "close_up",
      "camera_movement": "push_in"
    }}
  ],
  "product_showcase_strategy": {{
    "reveal_timing": "产品在第几秒出现（不要太早，先铺痛点）",
    "demonstration_type": "极致对比实验|使用过程实拍|before_after|场景演绎|数据测试",
    "proof_device": "用什么道具/方法证明产品效果（如：草莓实验/水分仪测试/显微镜/分屏对比）"
  }},
  "character_brief": {{
    "type": "博主真人出镜|素人测评|剧情演绎",
    "persona": "博主人设（如：成分党测评博主，说话犀利但真诚，偶尔毒舌）"
  }}
}}
```

## 铁律
1. 总时长 {target_duration} 秒，shot_plan必须有6-10个片段，每段有独立的creative_idea
2. 前5秒必须有"暴力钩子"——视觉冲击/反常识/强冲突，让人无法划走
3. 绝对不允许出现"产品摆拍"式的镜头——每个镜头都要有内容创意
4. segment_name要用中文，体现这段的内容价值（如"极致对比""场景转换""痛点戳心"），不要用"shot1""主体"这种废话
5. creative_idea是最重要的字段——写清楚这段为什么有趣、用什么创意装置
6. 如果产品信息不够，你必须根据行业知识补充合理的产品特点和卖点，不要输出空洞内容

直接输出JSON。"""


def get_screenwriter_prompt(product_name: str, director_strategy: dict,
                            product_detail: str = "", selling_points: list = None,
                            style: str = "cinematic") -> str:
    """Screenwriter Agent: 写出"博主说人话"的口播 + 有创意的画面描述"""
    import json
    strategy_json = json.dumps(director_strategy, ensure_ascii=False, indent=2)
    sp_text = "\n".join(f"- {s}" for s in (selling_points or []))

    return f"""你是抖音头部带货博主的专属编剧。你写的不是广告文案，是博主的"说人话"脚本。

## 参考范例（学习这种风格）
{EXAMPLE_SCRIPT_CLEANSER}

## Director的创意策划
{strategy_json}

## 产品信息
- 产品: {product_name}
- 详情: {product_detail or '根据Director策略推断'}
- 卖点:
{sp_text or '参考Director策略'}

## 你需要为每个片段写出完整的分镜（JSON）

```json
{{
  "frames": [
    {{
      "frame_id": 1,
      "segment_name": "暴力钩子",
      "narration": "口播文案（见下方要求）",
      "visual_description": "详细的中文画面描述（见下方要求）",
      "visual_prompt": "English prompt for AI image generation, 40-80 words",
      "text_overlay": "屏幕上的文字贴片（如关键数据、产品名），无则null",
      "duration": 5,
      "shot_type": "macro_close_up",
      "camera_movement": "static",
      "lighting": "studio_soft",
      "mood": "shocking",
      "audio_cue": "音效提示"
    }}
  ]
}}
```

## 编剧铁律（最重要！！！）

### 口播(narration)要求：
1. **像博主说话，不像AI写的广告词**
   - 好: "你闻到了吗？这就是你堵了二十几年的油脂味道。"
   - 坏: "水润净肤新体验！"
   - 好: "长得很低调，效果却很猛。"
   - 坏: "本产品采用先进技术。"
2. **每段口播要长！要有信息量！** 不是一句话，是一整段话
   - 5秒镜头 = 15-20字口播
   - 8秒镜头 = 24-30字口播
   - 10秒镜头 = 30-40字口播
3. **要有口语碎片**: "就是说"、"真的"、"你知道吗"、"我当时就"
4. **卖点要用故事/场景/对比带出来**，绝不直接喊口号
   - 好: "两位数就能买到这种级别的洁面，真的没必要去试那些乱七八糟的了"
   - 坏: "性价比超高！赶快购买！"
5. **要有情绪递进**: 每段口播的情绪跟着Director的emotion_journey走

### 画面(visual_description)要求：
1. **中文详细描述**，要包含：镜头类型、主体动作、道具、环境、表情
   - 好: "【宏观特写】一颗娇嫩红草莓按入黑亮工业机油中，被拎起时孔洞塞满黑色油污。【动作】博主在水龙头下冲洗草莓，黑油纹丝不动。"
   - 坏: "产品特写镜头"
2. 要描述具体的**道具和实验装置**（如有）
3. 要描述人物的**具体表情和动作**

### visual_prompt(英文AI生图提示)要求：
1. 40-80 words, extremely specific
2. Include: subject details, exact action, props, environment, lighting, camera angle, style
3. 好: "Extreme macro close-up of a fresh red strawberry being pressed into a bowl of black industrial oil mixed with carbon powder. The strawberry's tiny pores are filled with black grimy residue, resembling clogged pores on a nose. Studio lighting, dramatic shadows, 4K commercial quality."
4. 坏: "Product shot with professional lighting"

直接输出JSON。"""


def get_producer_prompt(product_name: str, screenwriter_output: dict,
                        director_strategy: dict) -> str:
    """Producer Agent: 质量把关 — 确保脚本达到爆款水准"""
    import json
    frames_json = json.dumps(screenwriter_output, ensure_ascii=False, indent=2)
    strategy_json = json.dumps(director_strategy, ensure_ascii=False, indent=2)

    return f"""你是抖音MCN机构的内容总监，负责最终审核脚本质量。
你的标准是：这个脚本放到抖音上，能不能让人看完想买？

## Director策略
{strategy_json}

## Screenwriter分镜
{frames_json}

## 审核清单（逐项检查，不合格直接改）

### 1. 口播质量审核（最重要！）
- [ ] **真人感**: 读出来像真人博主在说话吗？有没有AI腔/广告腔？有就改！
  - 检测关键词: "采用""搭载""体验""焕新" → 这些都是AI腔，必须改成口语
  - 正确风格: "就这个感觉""我当时就惊了""真的没必要""说实话"
- [ ] **信息密度**: 每段口播是否有具体信息（数据/场景/对比/故事）？空洞的直接补充
  - "水润好用" → 空洞，改为 "洗完之后不仅不假滑，感觉每个毛孔都在大口呼吸"
- [ ] **字数匹配**: narration中文字数 ≈ duration × 3.5（允许±5字）
  - 5秒 → 15-20字, 8秒 → 25-33字, 10秒 → 30-40字
  - 字数不够说明内容太空洞，必须补充

### 2. 创意质量审核
- [ ] **暴力钩子**: 前5秒的画面+口播能让人停下来吗？
- [ ] **极致对比/实验**: 中段是否有视觉冲击力强的对比/实验/证明？
- [ ] **场景真实感**: 画面描述是否具体到道具、动作、表情？模糊的补充细节
- [ ] **卖点覆盖**: 核心卖点是否自然融入了故事/场景？生硬植入的要改

### 3. 结构审核
- [ ] 总帧数6-10帧？太少就补
- [ ] 节奏变化: 是否有快慢交替？连续3帧同节奏就调整
- [ ] CTA: 最后一帧是否有明确的行动号召且不生硬？

## 输出格式

```json
{{
  "title": "视频标题（抖音爆款风格，制造好奇心，15字以内）",
  "product_reference": {{
    "description": "English product visual description for consistent AI generation. 30-50 words.",
    "showcase_frames": [3, 5]
  }},
  "character_reference": {{
    "needed": true,
    "description": "English character description. 30-50 words. null if no character."
  }},
  "frames": [
    {{
      "frame_id": 1,
      "segment_name": "暴力钩子",
      "narration": "审核优化后的口播（必须像真人说话）",
      "visual_description": "审核优化后的中文画面描述（必须具体到道具/动作/表情）",
      "visual_prompt": "审核优化后的英文AI生图提示（40-80 words, extremely specific）",
      "text_overlay": "屏幕文字或null",
      "duration": 5,
      "shot_type": "macro_close_up",
      "camera_movement": "static",
      "lighting": "studio_soft",
      "mood": "shocking",
      "audio_cue": "音效",
      "product_in_frame": false,
      "needs_product_ref": false,
      "needs_character_ref": true
    }}
  ],
  "quality_report": {{
    "hook_score": 9,
    "info_density_score": 8,
    "selling_point_coverage": ["卖点1: 在第X帧通过XX方式覆盖"],
    "fixes_applied": ["修改了第X帧口播，原文太广告腔改为口语化", "补充了第X帧画面细节"]
  }},
  "total_duration": 60,
  "estimated_cost": {{
    "images": 8,
    "videos_seconds": 60,
    "note": "预估"
  }}
}}
```

## 你的审核底线
- 如果口播读出来像广告/AI写的 → 必须改到像真人博主说话
- 如果画面描述不够具体（少于20字）→ 必须补充到50字以上
- 如果整个脚本只有4-5帧 → 必须扩展到6-10帧
- 如果没有实验/对比/故事等创意装置 → 必须加入至少一个

直接输出审核优化后的完整JSON。"""


# ==================== 营销风格词典 ====================

MARKETING_VISUAL_STYLES = {
    "product_hero": "Commercial product photography, studio lighting, clean background, hero shot, professional quality, 8K detail",
    "lifestyle": "Lifestyle photography, natural setting, warm tones, authentic moment, relatable scene, social media aesthetic",
    "before_after": "Split comparison, dramatic difference, clean layout, before and after transformation, clear visual evidence",
    "unboxing": "First person POV, hands opening package, anticipation, clean desk surface, natural lighting, ASMR aesthetic",
    "testimonial": "Medium close-up portrait, genuine expression, soft natural lighting, slightly blurred background, trustworthy feel",
    "data_visual": "Clean infographic style, bold numbers, minimal design, high contrast text, professional data visualization",
    "urgency": "Dynamic composition, bold red/orange accents, countdown timer aesthetic, high energy, action-oriented",
}

SHOT_DURATION_GUIDE = {
    "hook": (3, 5),          # 暴力钩子
    "problem": (4, 6),       # 痛点戳心
    "product_reveal": (3, 5), # 金手指觉醒
    "demo": (5, 10),         # 极致对比/实验
    "benefit": (5, 10),      # 核心功效
    "social_proof": (3, 5),  # 社交证明
    "scene_switch": (5, 10), # 场景转换
    "cta": (5, 8),           # 促单转化
    "transition": (2, 3),    # 快速转场
    "climax": (5, 10),       # 打脸高光/结果展示
}
