# -*- coding: utf-8 -*-
"""
Gemini LLM客户端 - 使用OpenAI兼容格式调用Gemini API生成脚本内容
"""
import json
import httpx
from typing import List, Dict, Optional
from loguru import logger

from ..config import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL


class GeminiClient:
    """Gemini API客户端 - 生成视频脚本内容"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.base_url = base_url or GEMINI_BASE_URL
        self.model = model or GEMINI_MODEL

    async def generate_script_content(
        self,
        topic: str,
        shots_structure: List[Dict],
        style: str = "marketing",
        product_info: Optional[str] = None
    ) -> List[Dict]:
        """
        根据主题和镜头结构生成完整脚本内容

        Args:
            topic: 视频主题
            shots_structure: Director生成的镜头结构列表, 每项含 id, shot_type, duration, act_type
            style: 视频风格
            product_info: 产品卖点信息(可选)

        Returns:
            列表, 每项含 shot_id, visual_description(英文), narration(中文)
        """
        prompt = self._build_prompt(topic, shots_structure, style, product_info)

        try:
            result = await self._call_api(prompt)
            parsed = self._parse_response(result, shots_structure)
            return parsed
        except Exception as e:
            logger.error(f"Gemini生成脚本失败: {e}, 使用回退模板")
            return self._fallback_template(topic, shots_structure, style, product_info)

    def _build_prompt(
        self,
        topic: str,
        shots_structure: List[Dict],
        style: str,
        product_info: Optional[str]
    ) -> str:
        shots_desc = ""
        for shot in shots_structure:
            shots_desc += f"- Shot {shot['id']}: type={shot.get('shot_type', 'unknown')}, act={shot.get('act_type', 'unknown')}, duration={shot.get('duration', 5)}s\n"

        product_section = ""
        if product_info:
            product_section = f"""
产品卖点信息: {product_info}
注意: 对于 product 和 hands_on 类型的镜头，画面描述要突出产品特征和卖点。
"""

        style_map = {
            "marketing": "营销推广视频，节奏紧凑，吸引眼球，强调产品亮点",
            "documentary": "纪录片风格，叙事平稳，信息丰富",
            "narrative": "故事叙事风格，有起承转合"
        }
        style_desc = style_map.get(style, style)

        return f"""你是一个专业的视频脚本编剧。请根据以下信息为每个镜头生成画面描述和口播文案。

视频主题: {topic}
视频风格: {style_desc}
{product_section}
镜头结构:
{shots_desc}

请为每个镜头生成:
1. visual_description: 英文的画面描述(用于AI图片生成), 要具体生动, 30-50个英文单词即可，不要太长
2. narration: 中文口播文案, 一两句话即可, 自然流畅

请严格按以下JSON格式输出(不要有其他文字):
[
  {{
    "shot_id": 1,
    "visual_description": "...",
    "narration": "..."
  }},
  ...
]

要求:
- visual_description 必须是英文,描述画面场景、构图、光线、色调等,适合作为AI图片生成的prompt
- narration 必须是中文,是视频口播文案
- 内容必须与主题"{topic}"紧密相关
- 每个镜头的内容要根据其类型(shot_type)和所属幕(act_type)来设计
- opening类型: 吸引注意力的开场
- talking_head类型: 主讲人出镜讲解
- product类型: 产品展示特写
- hands_on类型: 产品使用演示
- broll类型: 补充画面/空镜头
- comparison类型: 对比画面
- closing类型: 结尾总结+号召行动
"""

    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 8192) -> str:
        """公共生成方法，内部调用 _call_api"""
        return await self._call_api(prompt, temperature=temperature, max_tokens=max_tokens)

    async def understand_video(self, video_url: str, prompt: str, max_tokens: int = 8192) -> str:
        """
        Gemini多模态视频理解

        通过OpenAI兼容格式传递视频URL，让Gemini分析视频内容。
        如果apiyi不支持video_url类型，自动fallback到纯文本分析。

        Args:
            video_url: 视频文件URL
            prompt: 分析提示词
            max_tokens: 最大输出token数

        Returns:
            Gemini的视频分析结果文本
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 尝试多模态格式
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "video_url", "video_url": {"url": video_url}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=180.0, trust_env=False) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                data = resp.json()

                if resp.status_code == 200:
                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"Gemini视频理解成功, 响应长度: {len(content)}")
                    return content

                # 如果video_url格式不支持，尝试纯文本模式
                logger.warning(f"Gemini视频多模态失败(status={resp.status_code}), 降级为纯文本模式")

        except Exception as e:
            logger.warning(f"Gemini视频多模态异常: {e}, 降级为纯文本模式")

        # 降级: 纯文本分析（没有视频画面，只分析已有文字信息）
        fallback_prompt = f"以下是一个视频的URL: {video_url}\n\n{prompt}\n\n注意: 当前无法直接分析视频画面，请根据提供的文字信息进行分析。"
        return await self._call_api(fallback_prompt, max_tokens=max_tokens)

    async def understand_with_images(self, image_urls: list, prompt: str, max_tokens: int = 8192) -> str:
        """
        Gemini多模态图片理解（备选方案）

        当视频直传不支持时，可用截帧图片进行分析。

        Args:
            image_urls: 图片URL列表
            prompt: 分析提示词
            max_tokens: 最大输出token数

        Returns:
            Gemini的分析结果文本
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建多图消息
        content_parts = []
        for url in image_urls:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": url}
            })
        content_parts.append({"type": "text", "text": prompt})

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": content_parts}
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )

                if resp.status_code != 200:
                    data = resp.json()
                    logger.error(f"Gemini图片理解失败: status={resp.status_code}, body={data}")
                    # 降级纯文本
                    return await self._call_api(prompt, max_tokens=max_tokens)

                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                logger.info(f"Gemini图片理解成功, 响应长度: {len(content)}")
                return content

        except Exception as e:
            logger.error(f"Gemini图片理解异常: {e}")
            return await self._call_api(prompt, max_tokens=max_tokens)

    async def _call_api(self, prompt: str, max_retries: int = 2, temperature: float = 0.7, max_tokens: int = 8192) -> str:
        """调用Gemini API (OpenAI兼容格式)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers
                    )
                    data = resp.json()
                    if resp.status_code != 200:
                        logger.error(f"Gemini API错误 (尝试{attempt+1}): status={resp.status_code}, body={data}")
                        if attempt < max_retries:
                            continue
                        raise RuntimeError(f"Gemini API返回错误: {data}")

                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"Gemini API调用成功, 响应长度: {len(content)}")
                    return content

            except httpx.HTTPError as e:
                logger.error(f"Gemini API网络错误 (尝试{attempt+1}): {e}")
                if attempt < max_retries:
                    continue
                raise

        raise RuntimeError("Gemini API调用失败，已耗尽重试次数")

    def _parse_response(self, response_text: str, shots_structure: List[Dict]) -> List[Dict]:
        """解析Gemini响应的JSON"""
        # 尝试提取JSON部分
        text = response_text.strip()

        # 处理markdown代码块
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # 找到JSON数组的起止位置
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            text = text[start:end]

        try:
            result = json.loads(text)
            if isinstance(result, list):
                logger.info(f"成功解析 {len(result)} 个镜头的脚本内容")
                return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 原文: {text[:200]}")

        raise RuntimeError("无法解析Gemini响应为JSON")

    def _fallback_template(
        self,
        topic: str,
        shots_structure: List[Dict],
        style: str,
        product_info: Optional[str]
    ) -> List[Dict]:
        """回退模板 - Gemini失败时使用"""
        result = []
        for shot in shots_structure:
            shot_type = shot.get("shot_type", "broll")
            shot_id = shot.get("id", 0)
            act_type = shot.get("act_type", "main")

            visual_desc, narration = self._get_template_content(
                topic, shot_type, act_type, shot_id, product_info
            )

            result.append({
                "shot_id": shot_id,
                "visual_description": visual_desc,
                "narration": narration
            })

        return result

    def _get_template_content(
        self, topic: str, shot_type: str, act_type: str,
        shot_id: int, product_info: Optional[str]
    ) -> tuple:
        """根据镜头类型生成模板内容"""
        product_text = product_info or topic

        templates = {
            "opening": (
                f"Dynamic opening shot with bold text overlay about {topic}, modern tech aesthetic, "
                f"vibrant colors, lens flare, cinematic wide angle, energetic mood, dark gradient background",
                f"大家好！今天给大家带来一个重磅评测——{topic}！"
            ),
            "talking_head": (
                f"Professional presenter speaking to camera about {topic}, modern studio background, "
                f"soft key lighting, shallow depth of field, confident expression, clean composition",
                f"接下来让我们深入了解{topic}的核心功能和特色。"
            ),
            "product": (
                f"Elegant product showcase of {topic}, studio lighting, clean white background, "
                f"dramatic angle, reflective surface, detailed close-up, commercial photography style",
                f"{product_text}，这就是它最大的亮点！"
            ),
            "hands_on": (
                f"Hands-on demonstration of {topic}, first person POV, natural indoor lighting, "
                f"detailed interaction, practical usage scenario, warm color tone",
                f"实际上手体验一下，操作非常简单直观。"
            ),
            "broll": (
                f"Cinematic B-roll footage related to {topic}, smooth camera movement, "
                f"atmospheric lighting, abstract tech visuals, bokeh effect, modern aesthetic",
                f"让我们从另一个角度来看看{topic}。"
            ),
            "comparison": (
                f"Split screen comparison related to {topic}, clean layout, before and after, "
                f"clear visual difference, professional infographic style, data visualization",
                f"对比一下就能看出差距了，优势非常明显。"
            ),
            "closing": (
                f"Closing shot with summary text about {topic}, call to action overlay, "
                f"subscribe button graphic, warm colors, friendly mood, professional ending",
                f"以上就是今天的评测内容，如果觉得有帮助的话，别忘了点赞关注！"
            ),
        }

        return templates.get(shot_type, templates["broll"])
