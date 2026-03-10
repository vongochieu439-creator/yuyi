# -*- coding: utf-8 -*-
"""
多Agent分镜导演系统 — 面向抖音卖货/涨粉
Agent流水线: Director(策略) → Screenwriter(分镜) → Producer(质审)

与现有ScriptCreator的关系:
- ScriptCreator: 竞品研究 → 方向 → Hook → 文字脚本(shots)
- StoryboardDirector: 接收脚本 → 多Agent分镜 → 视觉化 → 可审核帧
"""
import copy
import json
import re
from typing import Dict, List, Optional, Callable, Awaitable
from loguru import logger

from ..config import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL
from .gemini_client import GeminiClient
from .storyboard_prompts_v2 import (
    get_director_prompt,
    get_screenwriter_prompt,
    get_producer_prompt,
)


class StoryboardDirector:
    """
    多Agent分镜导演

    三个Agent协作:
    1. Director  — 分析产品+市场，制定内容策略+情绪曲线+镜头规划
    2. Screenwriter — 基于策略为每帧写旁白(中文)+视觉描述(英文)
    3. Producer  — 质量审核+字数校验+卖点覆盖检查+一致性优化

    输入: 产品信息 + 卖点 + 风格
    输出: 完整分镜表(含产品/角色参考图描述)
    """

    def __init__(self):
        self.gemini = GeminiClient()

    async def generate_storyboard(
        self,
        product_name: str,
        product_detail: str = "",
        industry: str = "",
        selling_points: List[str] = None,
        target_duration: int = 60,
        style: str = "cinematic",
        reference_text: str = "",
        on_agent_complete: Optional[Callable] = None,
    ) -> dict:
        """
        多Agent流水线生成分镜

        Args:
            product_name: 产品名称
            product_detail: 产品详情
            industry: 行业
            selling_points: 核心卖点列表
            target_duration: 目标时长(秒)
            style: 视觉风格
            reference_text: 参考文案
            on_agent_complete: Agent完成回调 async def(agent_name, data)

        Returns:
            完整分镜dict
        """
        logger.info(f"StoryboardDirector启动: product={product_name}, duration={target_duration}s")

        # ===== Agent 1: Director — 策略制定 =====
        director_output = await self._run_director(
            product_name, product_detail, industry,
            target_duration, reference_text, selling_points
        )
        if on_agent_complete:
            await on_agent_complete("director", director_output)
        shot_count = len(director_output.get("shot_plan", []))
        logger.info(f"Director完成: {shot_count}个镜头, hook={director_output.get('content_strategy', {}).get('hook_type')}")

        # ===== Agent 2: Screenwriter — 分镜撰写 =====
        screenwriter_output = await self._run_screenwriter(
            product_name, director_output, product_detail,
            selling_points, style
        )
        if on_agent_complete:
            await on_agent_complete("screenwriter", screenwriter_output)
        frame_count = len(screenwriter_output.get("frames", []))
        logger.info(f"Screenwriter完成: {frame_count}帧分镜")

        # ===== Agent 3: Producer — 质量审核+优化 =====
        producer_output = await self._run_producer(
            product_name, screenwriter_output, director_output
        )
        if on_agent_complete:
            await on_agent_complete("producer", producer_output)
        logger.info(f"Producer完成: quality_report={producer_output.get('quality_report', {})}")

        # 组装最终结果
        result = self._build_final_storyboard(
            producer_output, director_output, product_name,
            product_detail, industry, selling_points, style, target_duration
        )
        return result

    # ==================== Agent Runners ====================

    async def _run_director(self, product_name, product_detail, industry,
                            target_duration, reference_text, selling_points) -> dict:
        """运行Director Agent"""
        prompt = get_director_prompt(
            product_name=product_name,
            product_detail=product_detail,
            industry=industry,
            target_duration=target_duration,
            reference_text=reference_text,
            selling_points=selling_points,
        )

        try:
            content = await self.gemini.generate(prompt, temperature=0.7, max_tokens=8192)
            result = self._parse_json(content)
            if result and "shot_plan" in result:
                return result
        except Exception as e:
            logger.error(f"Director Agent失败: {e}", exc_info=True)

        # 降级: 通用营销策略
        return self._fallback_director(product_name, target_duration, selling_points)

    async def _run_screenwriter(self, product_name, director_strategy,
                                 product_detail, selling_points, style) -> dict:
        """运行Screenwriter Agent"""
        prompt = get_screenwriter_prompt(
            product_name=product_name,
            director_strategy=director_strategy,
            product_detail=product_detail,
            selling_points=selling_points,
            style=style,
        )

        try:
            content = await self.gemini.generate(prompt, temperature=0.8, max_tokens=16384)
            result = self._parse_json(content)
            if result and "frames" in result:
                return result
        except Exception as e:
            logger.error(f"Screenwriter Agent失败: {e}", exc_info=True)

        # 降级: 从Director的shot_plan生成基础帧
        return self._fallback_screenwriter(director_strategy, product_name)

    async def _run_producer(self, product_name, screenwriter_output, director_strategy) -> dict:
        """运行Producer Agent"""
        prompt = get_producer_prompt(
            product_name=product_name,
            screenwriter_output=screenwriter_output,
            director_strategy=director_strategy,
        )

        try:
            content = await self.gemini.generate(prompt, temperature=0.3, max_tokens=16384)
            result = self._parse_json(content)
            if result and "frames" in result:
                return result
        except Exception as e:
            logger.error(f"Producer Agent失败: {e}", exc_info=True)

        # 降级: 直接返回screenwriter的输出加上默认quality_report
        output = copy.deepcopy(screenwriter_output)
        output["title"] = f"{product_name} - 种草视频"
        output["product_reference"] = {
            "description": f"Professional product shot of {product_name}, clean studio lighting, white background, detailed texture",
            "showcase_frames": []
        }
        output["character_reference"] = {"needed": False, "description": None}
        output["quality_report"] = {"hook_score": 6, "info_density_score": 6,
                                     "selling_point_coverage": [], "fixes_applied": ["Producer降级，未执行质审"]}
        return output

    # ==================== Result Builder ====================

    def _build_final_storyboard(self, producer_output, director_output,
                                 product_name, product_detail, industry,
                                 selling_points, style, target_duration) -> dict:
        """组装最终分镜结果"""
        frames = producer_output.get("frames", [])
        total_duration = sum(f.get("duration", 5) for f in frames)

        # 标准化每帧
        for i, frame in enumerate(frames):
            frame.setdefault("frame_id", i + 1)
            frame.setdefault("status", "pending")
            frame.setdefault("feedback", None)
            frame.setdefault("image_url", None)
            frame.setdefault("video_url", None)
            frame.setdefault("narration", "")
            frame.setdefault("visual_prompt", "")
            frame.setdefault("duration", 5)
            frame.setdefault("shot_type", "medium")
            frame.setdefault("camera_movement", "static")
            frame.setdefault("lighting", "natural_warm")
            frame.setdefault("mood", "curious")
            frame.setdefault("text_overlay", None)
            frame.setdefault("audio_cue", None)
            frame.setdefault("product_in_frame", False)
            frame.setdefault("needs_product_ref", False)
            frame.setdefault("needs_character_ref", False)

        return {
            "title": producer_output.get("title", f"{product_name}"),
            "product_name": product_name,
            "product_detail": product_detail,
            "industry": industry,
            "selling_points": selling_points or [],
            "style": style,
            "target_duration": target_duration,
            "total_duration": total_duration,
            "frames": frames,
            "product_reference": producer_output.get("product_reference", {}),
            "character_reference": producer_output.get("character_reference", {}),
            "director_strategy": director_output,
            "quality_report": producer_output.get("quality_report", {}),
        }

    # ==================== Fallbacks ====================

    def _fallback_director(self, product_name, target_duration, selling_points) -> dict:
        """Director降级方案"""
        sp = selling_points or ["高品质", "性价比", "便捷"]
        return {
            "target_audience": {
                "primary": "25-35岁关注生活品质的都市人群",
                "scroll_stop_trigger": f"一个让人意想不到的{product_name}使用场景"
            },
            "content_strategy": {
                "angle": f"用真实场景展示{product_name}如何解决日常痛点",
                "hook_type": "pain_point",
                "narrative_arc": "痛点共鸣→产品亮相→效果验证→限时CTA",
                "key_emotion_sequence": ["共鸣", "好奇", "惊喜", "信任", "紧迫"],
                "pattern_breaks": [{"at_second": 5, "technique": "突然放大产品特写+音效"}]
            },
            "shot_plan": [
                {"shot_id": 1, "act": "hook", "duration": 4, "purpose": "痛点场景引发共鸣",
                 "target_emotion": "共鸣", "intensity": 0.9, "shot_type": "medium", "camera_movement": "handheld"},
                {"shot_id": 2, "act": "problem", "duration": 5, "purpose": "放大痛点严重性",
                 "target_emotion": "焦虑", "intensity": 0.7, "shot_type": "close_up", "camera_movement": "zoom_in"},
                {"shot_id": 3, "act": "reveal", "duration": 4, "purpose": "产品首次出现",
                 "target_emotion": "好奇", "intensity": 0.8, "shot_type": "product_showcase", "camera_movement": "zoom_in"},
                {"shot_id": 4, "act": "demo", "duration": 6, "purpose": f"展示{sp[0]}",
                 "target_emotion": "惊喜", "intensity": 0.8, "shot_type": "pov", "camera_movement": "tracking"},
                {"shot_id": 5, "act": "benefit", "duration": 5, "purpose": f"展示{sp[1] if len(sp) > 1 else '效果'}",
                 "target_emotion": "信任", "intensity": 0.7, "shot_type": "medium", "camera_movement": "static"},
                {"shot_id": 6, "act": "social_proof", "duration": 4, "purpose": "用户评价/数据增加信任",
                 "target_emotion": "信任", "intensity": 0.6, "shot_type": "text_overlay", "camera_movement": "static"},
                {"shot_id": 7, "act": "cta", "duration": 4, "purpose": "限时优惠+行动号召",
                 "target_emotion": "紧迫", "intensity": 0.9, "shot_type": "product_showcase", "camera_movement": "zoom_in"},
            ],
            "product_showcase_strategy": {
                "reveal_timing": "第10秒",
                "showcase_shots": [3, 4, 7],
                "demonstration_type": "使用过程"
            },
            "character_brief": {
                "type": "场景演绎",
                "description": "25岁都市白领，干净利落，表情自然真实"
            }
        }

    def _fallback_screenwriter(self, director_strategy, product_name) -> dict:
        """Screenwriter降级方案 — 从Director策略生成基础口播，不是只放标签"""
        frames = []
        for shot in director_strategy.get("shot_plan", []):
            purpose = shot.get("purpose", "")
            creative = shot.get("creative_idea", purpose)
            segment = shot.get("segment_name", shot.get("act", ""))
            # 生成有内容的降级口播，而不是空标签
            narration = creative if len(creative) > 10 else f"{segment}：{purpose}"
            frames.append({
                "frame_id": shot.get("shot_id", 1),
                "segment_name": segment,
                "narration": narration,
                "visual_description": f"{segment}：{creative}",
                "visual_prompt": f"Commercial {shot.get('shot_type', 'medium')} shot, {product_name}, {creative[:50]}, professional lighting, 4K, cinematic style",
                "text_overlay": None,
                "duration": shot.get("duration", 5),
                "shot_type": shot.get("shot_type", "medium"),
                "camera_movement": shot.get("camera_movement", "static"),
                "lighting": "studio_soft",
                "mood": shot.get("target_emotion", "curious"),
                "audio_cue": None,
            })
        return {"frames": frames}

    # ==================== JSON Parser ====================

    def _parse_json(self, content: str) -> Optional[dict]:
        """解析LLM返回的JSON，支持被截断的JSON修复"""
        candidates = [content]

        # 提取 ```json``` 块
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if json_match:
            candidates.insert(0, json_match.group(1))

        # 提取 {...}
        brace_start = content.find("{")
        brace_end = content.rfind("}")
        if brace_start != -1 and brace_end != -1:
            candidates.append(content[brace_start:brace_end + 1])

        for candidate in candidates:
            candidate = candidate.strip()
            if not candidate:
                continue
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

            # 尝试修复被截断的JSON（补充缺失的括号）
            repaired = self._repair_truncated_json(candidate)
            if repaired:
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    pass

        logger.error(f"无法解析JSON: {content[:300]}")
        return None

    def _repair_truncated_json(self, text: str) -> Optional[str]:
        """尝试修复被截断的JSON"""
        text = text.strip()
        if not text.startswith("{"):
            return None

        # 统计未闭合的括号
        stack = []
        in_string = False
        escape = False
        for ch in text:
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch in '{[':
                stack.append(ch)
            elif ch == '}' and stack and stack[-1] == '{':
                stack.pop()
            elif ch == ']' and stack and stack[-1] == '[':
                stack.pop()

        if not stack:
            return None  # 已经平衡了，不是截断问题

        # 反向补充闭合括号
        closing = ""
        for bracket in reversed(stack):
            if bracket == '{':
                closing += '}'
            elif bracket == '[':
                closing += ']'

        repaired = text.rstrip().rstrip(',') + closing
        logger.info(f"尝试修复截断JSON: 补充了 {closing}")
        return repaired
