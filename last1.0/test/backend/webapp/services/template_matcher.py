# -*- coding: utf-8 -*-
"""
模板匹配服务 - 根据产品自动匹配最合适的内容模板
两级匹配：标签预筛选 + Gemini语义精排
"""
import json
from typing import List, Dict, Optional
from loguru import logger

from ..data.templates import TEMPLATE_LIBRARY, TEMPLATE_INDEX
from .gemini_client import GeminiClient
from . import user_template_service as user_svc


class TemplateMatcher:

    def __init__(self):
        self.gemini = GeminiClient()

    async def match(
        self,
        product_name: str,
        industry: Optional[str] = None,
        product_detail: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """
        为产品匹配最合适的模板，返回排好序的 top_k 个结果

        Returns:
            [{template, score, match_reason, match_highlights}, ...]
        """
        # 第一级：标签预筛选，缩小候选范围
        candidates = self._tag_filter(product_name, industry)

        # 第二级：Gemini语义精排（有产品信息时启用）
        if product_detail or industry:
            ranked = await self._gemini_rank(
                candidates=candidates,
                product_name=product_name,
                industry=industry,
                product_detail=product_detail,
                top_k=top_k
            )
        else:
            # 无详细信息时直接用标签匹配分数截取
            ranked = [
                {
                    "template": t["template"],
                    "score": t["score"],
                    "match_reason": f"适合{industry or '该品类'}产品的内容结构",
                    "match_highlights": [t["template"]["core_strategy"][:40] + "..."]
                }
                for t in candidates[:top_k]
            ]

        return ranked

    def _tag_filter(self, product_name: str, industry: Optional[str]) -> List[Dict]:
        """
        基于标签和品类的初步筛选，返回所有候选模板及粗粒度得分
        """
        keyword = f"{industry or ''} {product_name}".strip().lower()
        scored = []

        # 系统模板 + 用户自建模板合并
        all_templates = TEMPLATE_LIBRARY + user_svc.get_all()

        for template in all_templates:
            score = 0
            # 品类命中
            for cat in template.get("suitable_categories", []):
                if cat in keyword or keyword in cat:
                    score += 30
                    break
            # 标签命中
            for tag in template.get("tags", []):
                if tag in keyword:
                    score += 10

            # 不适合的品类扣分
            for bad in template.get("unsuitable_for", []):
                if bad in keyword:
                    score -= 50

            # 方法论模板保底10分（通用性强）
            if template["source"]["type"] == "methodology":
                score = max(score, 10)

            scored.append({"template": template, "score": score})

        # 按分数降序，取前8个进入精排
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:8]

    async def _gemini_rank(
        self,
        candidates: List[Dict],
        product_name: str,
        industry: Optional[str],
        product_detail: Optional[str],
        top_k: int
    ) -> List[Dict]:
        """
        用 Gemini 对候选模板进行语义精排
        """
        # 构建候选摘要传给 Gemini
        candidates_desc = ""
        for i, c in enumerate(candidates):
            t = c["template"]
            candidates_desc += (
                f"\n[{i}] {t['template_id']}\n"
                f"    名称: {t['name']}（来源: {t['source']['name']}）\n"
                f"    适合品类: {', '.join(t['suitable_categories'][:5])}\n"
                f"    核心策略: {t['core_strategy'][:80]}\n"
            )

        product_detail_section = f"产品详细信息: {product_detail}\n" if product_detail else ""

        prompt = f"""你是短视频营销专家。请为以下产品从候选模板中选出最合适的{top_k}个，并说明理由。

产品名称: {product_name}
行业/品类: {industry or '请根据产品名判断'}
{product_detail_section}
候选模板:
{candidates_desc}

请输出JSON数组（不要其他文字），按匹配度从高到低排列，只返回前{top_k}个：
[
  {{
    "template_id": "模板ID",
    "score": 匹配分数(0-100),
    "match_reason": "为什么这个模板适合这个产品（2-4句话，要具体，提到产品名）",
    "match_highlights": ["这个模板最适合该产品的1个核心亮点", "第2个亮点"]
  }},
  ...
]"""

        try:
            result = await self.gemini._call_api(prompt)
            parsed = self._parse_json(result)
            if isinstance(parsed, list) and len(parsed) > 0:
                # 补全 template 数据（系统 + 用户模板）
                all_index = {t["template_id"]: t for t in TEMPLATE_LIBRARY + user_svc.get_all()}
                output = []
                for item in parsed[:top_k]:
                    tid = item.get("template_id")
                    template = all_index.get(tid)
                    if template:
                        output.append({
                            "template": template,
                            "score": item.get("score", 70),
                            "match_reason": item.get("match_reason", ""),
                            "match_highlights": item.get("match_highlights", [])
                        })
                if output:
                    logger.info(f"Gemini精排完成，返回{len(output)}个模板")
                    return output
        except Exception as e:
            logger.warning(f"Gemini精排失败，使用标签排序: {e}")

        # 回退：直接返回标签分数前 top_k
        return [
            {
                "template": c["template"],
                "score": max(c["score"], 50),
                "match_reason": f"{c['template']['name']}的内容结构适合{product_name}类产品",
                "match_highlights": [c["template"]["core_strategy"][:60]]
            }
            for c in candidates[:top_k]
        ]

    @staticmethod
    def _parse_json(text: str):
        """解析 Gemini 返回的 JSON"""
        import re
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        return json.loads(text)

    def get_template(self, template_id: str) -> Optional[Dict]:
        """按 ID 获取模板详情（系统 + 用户）"""
        system = TEMPLATE_INDEX.get(template_id)
        if system:
            return system
        return user_svc.get_by_id(template_id)

    def get_all_templates(self) -> List[Dict]:
        """获取全部模板（系统 + 用户）"""
        return TEMPLATE_LIBRARY + user_svc.get_all()
