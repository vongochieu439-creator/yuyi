# -*- coding: utf-8 -*-
"""
漫剧分镜提示词模板
"""


STYLE_MODIFIERS = {
    "cinematic": {
        "name": "电影写实",
        "suffix": "cinematic lighting, photorealistic, 8K ultra HD, dramatic shadows, film grain, anamorphic lens flare, movie color grading, shallow depth of field",
        "mood_map": {
            "epic": "dramatic orchestral atmosphere",
            "dark": "noir shadows with rim lighting",
            "warm": "golden hour warm tones",
            "mysterious": "foggy blue-teal atmosphere",
            "intense": "high contrast red-orange hues",
        },
    },
    "ink_wash": {
        "name": "国风水墨",
        "suffix": "traditional Chinese ink wash painting style, xuan paper texture, elegant brushstrokes, flowing ink, minimalist composition, ancient Chinese aesthetic, muted earth tones with splashes of vermillion",
        "mood_map": {
            "epic": "sweeping mountain landscape with crane",
            "dark": "misty bamboo forest at twilight",
            "warm": "cherry blossoms by a moonlit pavilion",
            "mysterious": "ethereal clouds among ancient peaks",
            "intense": "raging calligraphy strokes in wind",
        },
    },
    "anime": {
        "name": "日系动漫",
        "suffix": "anime style, Studio Ghibli inspired, vibrant colors, detailed cel shading, dynamic action lines, sparkle effects, manga-inspired composition, trending on Pixiv",
        "mood_map": {
            "epic": "dramatic speed lines and aura effects",
            "dark": "moody blue tones with glowing eyes",
            "warm": "soft pastel sakura petals floating",
            "mysterious": "ethereal glow with particle effects",
            "intense": "explosive energy burst with motion blur",
        },
    },
    "comedy": {
        "name": "沙雕搞笑",
        "suffix": "exaggerated cartoon style, bold outlines, vivid saturated colors, comic book halftone dots, chibi proportions, comedic expressions, meme aesthetic, pop art influenced",
        "mood_map": {
            "epic": "over-the-top dramatic zoom with sweat drops",
            "dark": "comedically spooky with wobbly shadows",
            "warm": "sparkly shoujo manga background",
            "mysterious": "suspicious squinting with question marks",
            "intense": "explosive anger veins and fire background",
        },
    },
}

# 预置剧本模板 (Gemini失败时的降级方案)
FALLBACK_STORYBOARDS = {
    "default": {
        "title": "觉醒之路",
        "character": {
            "description": "A young man with messy dark hair, piercing blue eyes, wearing a tattered school uniform with a mysterious glowing mark on his left hand, determined expression",
            "name": "少年",
        },
        "bgm_style": "epic",
        "scenes": [
            {
                "scene_id": 1,
                "visual_prompt": "Extreme wide shot of a desolate post-apocalyptic cityscape at dawn, crumbling skyscrapers silhouetted against a blood-red sky, a lone figure standing on a rooftop",
                "narration": "这个世界，在那一天彻底改变了。",
                "camera": "slow_up",
                "mood": "mysterious",
                "duration": 5.0,
            },
            {
                "scene_id": 2,
                "visual_prompt": "Close-up portrait of a teenage boy with messy dark hair and piercing blue eyes, a glowing blue mark appears on his left hand, expression shifts from confusion to determination",
                "narration": "而我，不过是千万个普通人中的一个。",
                "camera": "zoom_in",
                "mood": "mysterious",
                "duration": 5.0,
            },
            {
                "scene_id": 3,
                "visual_prompt": "Dynamic action shot, the boy unleashes a wave of blue energy from his hand, debris floating in mid-air, shockwave ripples visible, dramatic backlighting",
                "narration": "直到那股力量，突然在我体内觉醒。",
                "camera": "shake",
                "mood": "intense",
                "duration": 5.0,
            },
            {
                "scene_id": 4,
                "visual_prompt": "Medium shot of shadowy figures in dark cloaks watching from a distant rooftop, city burning in background, ominous red symbols floating around them",
                "narration": "他们说，觉醒者要么成为武器，要么被消灭。",
                "camera": "pan_left",
                "mood": "dark",
                "duration": 5.0,
            },
            {
                "scene_id": 5,
                "visual_prompt": "The boy stands protectively in front of a group of frightened civilians, blue energy armor forming around him, wind blowing his hair and clothes dramatically",
                "narration": "但我选择了第三条路——守护。",
                "camera": "zoom_out",
                "mood": "epic",
                "duration": 5.0,
            },
            {
                "scene_id": 6,
                "visual_prompt": "Epic wide shot from below, the boy leaps into the air with trails of blue energy, city skyline behind him, sunrise breaking through dark clouds, heroic pose",
                "narration": "这是我的故事，才刚刚开始。",
                "camera": "slow_up",
                "mood": "epic",
                "duration": 5.0,
            },
        ],
    }
}


def get_storyboard_prompt(user_input: str, style: str = "cinematic") -> str:
    """生成分镜提示词"""
    style_info = STYLE_MODIFIERS.get(style, STYLE_MODIFIERS["cinematic"])
    style_suffix = style_info["suffix"]

    return f"""你是一位顶级漫剧分镜师。根据用户的故事概念，创作一个6幕漫剧分镜脚本。

## 用户输入
{user_input}

## 视觉风格
{style_info['name']} - 所有visual_prompt必须包含以下风格关键词: {style_suffix}

## 输出要求
请严格输出以下JSON格式（不要输出任何其他内容）:

```json
{{
  "title": "漫剧标题（中文，6字以内）",
  "character": {{
    "description": "Main character detailed visual description in English. Include: hair color/style, eye color, clothing, distinguishing features, age appearance. Must be specific enough to maintain visual consistency across all scenes. 30-50 words.",
    "name": "角色名（中文）"
  }},
  "bgm_style": "epic|romantic|suspense|comedy|chinese",
  "scenes": [
    {{
      "scene_id": 1,
      "visual_prompt": "Cinematic description in English, 30-50 words. MUST include the character description for consistency. Include: shot type (wide/medium/close-up), environment details, lighting, action, emotion. End with style keywords: {style_suffix}",
      "narration": "中文旁白台词，15-25字，富有感染力和悬念",
      "camera": "zoom_in|zoom_out|pan_left|pan_right|shake|breathe|slow_up|slow_down|diagonal|focus_in|static",
      "mood": "epic|dark|warm|mysterious|intense",
      "duration": 5.0
    }}
  ]
}}
```

## 分镜结构要求
- 第1幕(开场): 环境大全景，建立世界观，制造悬念
- 第2幕(引入): 角色特写，展现角色魅力
- 第3幕(冲突): 动态场景，矛盾爆发
- 第4幕(转折): 新信息揭示，剧情反转
- 第5幕(高潮): 情感最高点，视觉冲击力最强
- 第6幕(结尾): 余韵收束，留下悬念

## 关键规则
1. visual_prompt必须全英文，用于AI图片生成
2. 每个场景的visual_prompt中都要包含角色的外貌描述关键词，确保角色一致性
3. narration是中文旁白，要有画外音的感觉，不是对话
4. camera运镜要配合场景情绪（激烈场景用shake，安静场景用breathe等）
5. 6个场景总时长约30秒
6. 旁白要有节奏感，短句为主，制造悬念和情绪张力

直接输出JSON，不要有任何额外说明。"""


def get_style_suffix(style: str) -> str:
    """获取风格后缀"""
    return STYLE_MODIFIERS.get(style, STYLE_MODIFIERS["cinematic"])["suffix"]


def get_mood_modifier(style: str, mood: str) -> str:
    """获取情绪修饰词"""
    style_info = STYLE_MODIFIERS.get(style, STYLE_MODIFIERS["cinematic"])
    return style_info["mood_map"].get(mood, "")
