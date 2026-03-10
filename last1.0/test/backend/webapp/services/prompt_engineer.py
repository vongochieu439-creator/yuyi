# -*- coding: utf-8 -*-
"""
PromptEngineer: 把中文镜头描述 → 专业英文生图提示词
使用 Gemini AI，支持全局风格词注入
"""
import asyncio
from typing import Dict, List, Optional
from loguru import logger

from .gemini_client import GeminiClient


# 镜头类型 → 构图说明
SHOT_TYPE_HINTS: Dict[str, str] = {
    "hook": "attention-grabbing opening shot, dynamic composition",
    "product": "product hero shot, studio lighting, clean background",
    "scene": "lifestyle scene, environmental storytelling",
    "talking_head": "presenter / talking head, medium shot, eye-level",
    "hands_on": "close-up hands demonstration, first-person POV",
    "effect": "before-after comparison, split-frame or two-panel layout",
    "transition": "smooth cinematic transition frame",
    "wide": "wide establishing shot, sweeping view",
    "medium": "medium shot, waist-up framing",
    "close_up": "extreme close-up, macro detail",
    "cta": "call-to-action closing frame, warm and inviting",
    "hook_opening": "bold attention-grabbing opener, cinematic wide",
    "result": "result / outcome showcase shot",
}

# 情绪 → 光线色调描述
MOOD_HINTS: Dict[str, str] = {
    "warm": "warm golden tones, soft natural light",
    "cool": "cool blue palette, clean clinical lighting",
    "energetic": "high contrast, vibrant saturated colors, dynamic angle",
    "calm": "soft diffused light, muted tones, peaceful atmosphere",
    "luxurious": "dramatic rim light, deep shadows, rich dark tones",
    "fresh": "bright airy light, clean whites, pastel accents",
    "professional": "neutral balanced lighting, corporate clean look",
}

# 摄像运动 → 画面构图暗示
CAMERA_HINTS: Dict[str, str] = {
    "zoom_in": "tightly framed subject, compressed foreground",
    "zoom_out": "expanding scene, wide reveal",
    "pan_left": "lateral motion implied, side-lit subject",
    "pan_right": "lateral motion implied, side-lit subject",
    "tilt_up": "low angle looking up, heroic perspective",
    "tilt_down": "high angle looking down, bird's-eye feel",
    "static": "static composition, stable framing",
    "handheld": "slightly off-center, natural handheld feel",
    "dolly": "smooth depth perspective, foreground/background separation",
}

# 风格预设
STYLE_PRESETS: Dict[str, str] = {
    "商业广告": "commercial photography style, professional advertising, highly polished, brand-quality visual",
    "电影质感": "cinematic color grade, film grain, anamorphic lens, movie-like atmosphere",
    "ins写真": "instagram lifestyle photography, natural light, authentic feel, trendy aesthetic",
    "极简白": "minimalist white background, clean negative space, product-focused",
    "国风写意": "Chinese aesthetic, ink wash inspired, elegant traditional mood",
    "科技感": "futuristic tech aesthetic, blue neon accent, dark background, digital vibe",
}

_SYSTEM_INSTRUCTION = """You are an expert visual prompt engineer for AI image generation (DALL-E, Midjourney, Stable Diffusion style).
Convert the given Chinese video shot description into a high-quality English image generation prompt.

Output rules:
1. Output ONLY the English prompt, no explanations, no labels
2. Include: subject/object details, composition, lighting, color tone, style keywords
3. Always end with quality boosters: photorealistic, commercial photography, 8k, sharp focus
4. Keep it concise (80-120 words)
5. Incorporate the global style requirements naturally if provided
"""


class PromptEngineer:
    """中文镜头描述 → 专业英文生图提示词"""

    def __init__(self):
        self.client = GeminiClient()

    async def build_prompt(
        self,
        shot: Dict,
        global_style: str = "",
        product_name: str = "",
    ) -> str:
        """
        为单个镜头生成专业英文提示词

        Args:
            shot: 镜头数据（含 visual_description/narration/shot_type 等）
            global_style: 用户输入的全局风格描述（中英文均可）
            product_name: 产品名称，用于语境参考

        Returns:
            专业英文提示词字符串
        """
        visual = shot.get("visual_prompt", "") or shot.get("visual_description", "")
        narration = shot.get("narration", "")
        shot_type = shot.get("shot_type", "scene")
        duration = shot.get("duration", 5)
        mood = shot.get("mood", "")
        camera = shot.get("camera_movement", "")

        # 如果本身已经是高质量英文 prompt（长于 30 个词），只做风格融合
        if visual and self._is_quality_english(visual) and not global_style:
            return self._append_quality_boosters(visual)

        # 构建结构化描述给 Gemini
        parts: List[str] = []
        if visual:
            parts.append(f"Scene: {visual}")
        if narration:
            parts.append(f"Narration context (Chinese): {narration}")
        if product_name:
            parts.append(f"Product: {product_name}")

        shot_hint = SHOT_TYPE_HINTS.get(shot_type, "medium shot")
        parts.append(f"Shot type: {shot_hint}")

        if mood and mood in MOOD_HINTS:
            parts.append(f"Mood: {MOOD_HINTS[mood]}")
        if camera and camera in CAMERA_HINTS:
            parts.append(f"Camera: {CAMERA_HINTS[camera]}")
        if duration:
            parts.append(f"Duration: {duration}s")

        if global_style:
            # 先尝试匹配预设
            preset = STYLE_PRESETS.get(global_style.strip(), "")
            style_desc = preset if preset else global_style
            parts.append(f"Global style: {style_desc}")

        user_msg = "\n".join(parts)
        prompt_text = f"{_SYSTEM_INSTRUCTION}\n\n---\n{user_msg}\n---\nOutput the English prompt:"

        try:
            result = await self.client.generate(prompt_text, temperature=0.6, max_tokens=300)
            result = result.strip().strip('"').strip("'")
            # 清除可能的前缀说明
            for prefix in ["Prompt:", "English prompt:", "Output:"]:
                if result.lower().startswith(prefix.lower()):
                    result = result[len(prefix):].strip()
            return self._append_quality_boosters(result)
        except Exception as e:
            logger.warning(f"PromptEngineer Gemini调用失败, 使用fallback: {e}")
            return self._fallback_prompt(shot, global_style, product_name)

    async def build_batch(
        self,
        shots: List[Dict],
        global_style: str = "",
        product_name: str = "",
        concurrency: int = 3,
    ) -> Dict[int, str]:
        """
        并发为所有镜头生成提示词

        Returns:
            {shot_id: prompt_str} 映射
        """
        sem = asyncio.Semaphore(concurrency)

        async def _one(shot: Dict, idx: int):
            shot_id = shot.get("shot_id", idx + 1)
            async with sem:
                prompt = await self.build_prompt(shot, global_style, product_name)
            return shot_id, prompt

        tasks = [asyncio.create_task(_one(s, i)) for i, s in enumerate(shots)]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        out: Dict[int, str] = {}
        for i, res in enumerate(results_list):
            if isinstance(res, Exception):
                shot_id = shots[i].get("shot_id", i + 1)
                out[shot_id] = self._fallback_prompt(shots[i], global_style, product_name)
                logger.warning(f"Shot {shot_id} prompt generation failed: {res}")
            else:
                shot_id, prompt = res
                out[shot_id] = prompt
        return out

    # ------------------------------------------------------------------ #
    #  内部工具方法
    # ------------------------------------------------------------------ #

    def _is_quality_english(self, text: str) -> bool:
        """判断是否已经是足够长的英文描述"""
        if not text:
            return False
        words = text.split()
        non_ascii = sum(1 for c in text if ord(c) > 127)
        return len(words) >= 20 and non_ascii < 5

    def _append_quality_boosters(self, prompt: str) -> str:
        """确保末尾有质量关键词"""
        boosters = "photorealistic, commercial photography, 8k, sharp focus"
        if "photorealistic" not in prompt.lower() and "commercial" not in prompt.lower():
            return f"{prompt.rstrip('., ')}, {boosters}"
        return prompt

    def _fallback_prompt(self, shot: Dict, global_style: str, product_name: str) -> str:
        """Gemini 失败时的模板 fallback"""
        visual = shot.get("visual_prompt", "") or shot.get("visual_description", "")
        shot_type = shot.get("shot_type", "scene")
        mood = shot.get("mood", "warm")

        shot_hint = SHOT_TYPE_HINTS.get(shot_type, "medium shot")
        mood_hint = MOOD_HINTS.get(mood, "natural lighting, balanced tones")

        subject = visual if visual and self._is_quality_english(visual) else (
            f"product advertisement scene for {product_name}" if product_name else "product lifestyle scene"
        )

        style_suffix = ""
        if global_style:
            preset = STYLE_PRESETS.get(global_style.strip(), "")
            style_suffix = f", {preset}" if preset else f", {global_style} style"

        return (
            f"{subject}, {shot_hint}, {mood_hint}{style_suffix}, "
            f"photorealistic, commercial photography, 8k, sharp focus"
        )
