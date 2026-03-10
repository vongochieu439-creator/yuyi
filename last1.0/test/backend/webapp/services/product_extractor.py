# -*- coding: utf-8 -*-
"""
智能产品信息提取服务
- URL页面抓取 → Gemini结构化提取
- 图片多模态识别 → Gemini Vision结构化提取
- 纯文本 → Gemini结构化提取
"""
import base64
import httpx
from typing import Dict, Optional
from loguru import logger

from .gemini_client import GeminiClient
from ..config import TAVILY_API_KEY, TAVILY_BASE_URL

PRODUCT_EXTRACTION_PROMPT = """你是一个专业的产品信息分析师。请从以下内容中提取产品的结构化信息。

【内容来源】
{content}

请输出JSON格式（不要其他文字）：
{{
  "product_name": "产品名称",
  "category": "产品类别（如：护肤品、数码产品、食品等）",
  "price_range": "价格区间（如：¥99-199）",
  "core_features": ["核心功能/特点1", "核心功能/特点2", "核心功能/特点3"],
  "target_audience": "目标受众描述",
  "use_cases": ["使用场景1", "使用场景2"],
  "differentiators": ["差异化卖点1", "差异化卖点2"],
  "brand_tone": "品牌调性描述（如：年轻活力、专业权威、温暖亲切）",
  "raw_content": "原始内容摘要（100字以内）"
}}

【规则】
- 如果某个字段无法从内容中提取，填写空字符串或空数组
- core_features至少提取3个，如果内容不够就基于产品类型合理推断
- price_range如果无法确定，填"待确认"
- 提取要准确，不要编造不存在的信息
"""

PRODUCT_EXTRACTION_VISION_PROMPT = """你是一个专业的产品信息分析师。请从这张产品图片中识别并提取产品的结构化信息。

仔细观察图片中的：
- 产品名称、品牌logo
- 包装上的文字描述
- 产品外观特征
- 价格标签（如果有）
- 使用说明（如果可见）

请输出JSON格式（不要其他文字）：
{{
  "product_name": "产品名称",
  "category": "产品类别",
  "price_range": "价格区间",
  "core_features": ["核心功能/特点1", "核心功能/特点2", "核心功能/特点3"],
  "target_audience": "目标受众描述",
  "use_cases": ["使用场景1", "使用场景2"],
  "differentiators": ["差异化卖点1", "差异化卖点2"],
  "brand_tone": "品牌调性描述",
  "raw_content": "图片中识别到的关键文字信息摘要"
}}
"""


class ProductExtractor:
    """智能产品信息提取器"""

    def __init__(self):
        self.gemini = GeminiClient()

    async def extract_from_url(self, url: str) -> Dict:
        """通过URL抓取页面内容，然后用Gemini结构化提取"""
        logger.info(f"开始从URL提取产品信息: {url}")

        # 使用Tavily Extract API抓取页面
        page_content = await self._fetch_page_content(url)
        if not page_content:
            raise ValueError(f"无法获取页面内容: {url}")

        # Gemini结构化提取
        return await self._extract_structured(page_content)

    async def extract_from_image(self, image_base64: str) -> Dict:
        """通过图片多模态识别，提取产品信息"""
        logger.info("开始从图片提取产品信息")

        # 使用Gemini Vision多模态识别
        return await self._extract_from_image_vision(image_base64)

    async def extract_from_text(self, text: str) -> Dict:
        """从纯文本提取产品信息"""
        logger.info("开始从文本提取产品信息")

        if not text or len(text.strip()) < 5:
            raise ValueError("文本内容太短，无法提取产品信息")

        return await self._extract_structured(text)

    async def _fetch_page_content(self, url: str) -> str:
        """使用Tavily Extract API抓取页面内容"""
        try:
            payload = {
                "api_key": TAVILY_API_KEY,
                "urls": [url]
            }

            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                resp = await client.post(
                    f"{TAVILY_BASE_URL}/extract",
                    json=payload
                )

                if resp.status_code != 200:
                    logger.warning(f"Tavily Extract失败: {resp.status_code}, 尝试直接抓取")
                    return await self._direct_fetch(url)

                data = resp.json()
                results = data.get("results", [])
                if results:
                    content = results[0].get("raw_content", "") or results[0].get("text", "")
                    if content:
                        logger.info(f"Tavily Extract成功: {len(content)}字")
                        return content[:5000]

            return await self._direct_fetch(url)

        except Exception as e:
            logger.warning(f"Tavily Extract异常: {e}, 尝试直接抓取")
            return await self._direct_fetch(url)

    async def _direct_fetch(self, url: str) -> str:
        """直接HTTP抓取页面（兜底）"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, trust_env=False) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    text = resp.text[:5000]
                    # 简单清理HTML标签
                    import re
                    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
                    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                    text = re.sub(r'<[^>]+>', ' ', text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text
        except Exception as e:
            logger.error(f"直接抓取失败: {e}")
        return ""

    async def _extract_structured(self, content: str) -> Dict:
        """用Gemini从文本内容中结构化提取产品信息"""
        prompt = PRODUCT_EXTRACTION_PROMPT.format(content=content[:4000])

        try:
            result = await self.gemini.generate(prompt)
            parsed = self._parse_product_json(result)
            parsed["raw_content"] = content[:200]
            logger.info(f"产品信息提取成功: {parsed.get('product_name', '未知')}")
            return parsed
        except Exception as e:
            logger.error(f"Gemini产品提取失败: {e}")
            raise ValueError(f"产品信息提取失败: {e}")

    async def _extract_from_image_vision(self, image_base64: str) -> Dict:
        """用Gemini Vision从图片提取产品信息"""
        # 构建多模态请求
        headers = {
            "Authorization": f"Bearer {self.gemini.api_key}",
            "Content-Type": "application/json"
        }

        # 检测图片类型
        media_type = "image/jpeg"
        if image_base64.startswith("/9j/"):
            media_type = "image/jpeg"
        elif image_base64.startswith("iVBOR"):
            media_type = "image/png"

        payload = {
            "model": self.gemini.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": PRODUCT_EXTRACTION_VISION_PROMPT
                        }
                    ]
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }

        try:
            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                resp = await client.post(
                    f"{self.gemini.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                data = resp.json()
                if resp.status_code != 200:
                    raise RuntimeError(f"Gemini Vision API错误: {data}")

                content = data["choices"][0]["message"]["content"]
                parsed = self._parse_product_json(content)
                logger.info(f"图片产品提取成功: {parsed.get('product_name', '未知')}")
                return parsed

        except Exception as e:
            logger.error(f"Gemini Vision产品提取失败: {e}")
            raise ValueError(f"图片产品信息提取失败: {e}")

    def _parse_product_json(self, text: str) -> Dict:
        """解析产品信息JSON"""
        import json
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(text[start:end])
            # Ensure all expected fields exist
            defaults = {
                "product_name": "",
                "category": "",
                "price_range": "",
                "core_features": [],
                "target_audience": "",
                "use_cases": [],
                "differentiators": [],
                "brand_tone": "",
                "raw_content": ""
            }
            for k, v in defaults.items():
                result.setdefault(k, v)
            return result

        raise ValueError("无法解析产品信息JSON")
