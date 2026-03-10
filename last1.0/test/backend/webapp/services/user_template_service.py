# -*- coding: utf-8 -*-
"""
用户自建模板服务 - CRUD + AI提炼
"""
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from loguru import logger

from .gemini_client import GeminiClient

USER_TEMPLATES_FILE = Path(__file__).parent.parent / "data" / "user_templates.json"


def _load() -> List[Dict]:
    if not USER_TEMPLATES_FILE.exists():
        return []
    try:
        return json.loads(USER_TEMPLATES_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"加载用户模板失败: {e}")
        return []


def _save(templates: List[Dict]):
    USER_TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    USER_TEMPLATES_FILE.write_text(
        json.dumps(templates, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def get_all() -> List[Dict]:
    return _load()


def get_by_id(template_id: str) -> Optional[Dict]:
    for t in _load():
        if t["template_id"] == template_id:
            return t
    return None


def create(template_data: Dict) -> Dict:
    templates = _load()
    new_id = f"user_{uuid.uuid4().hex[:8]}"
    author_name = template_data.get("author_name", "自定义")

    template = {
        "template_id": new_id,
        "name": template_data.get("name", "未命名模板"),
        "source": {
            "type": "user",
            "name": author_name,
            "label": f"用户自建 · {author_name}",
            "bio": template_data.get("description", "用户自定义内容模板"),
            "followers": "",
            "avatar_hint": ""
        },
        "core_strategy": template_data.get("core_strategy", ""),
        "hook_formula": template_data.get("hook_formula", ""),
        "narration_style": template_data.get("narration_style", ""),
        "narration_examples": template_data.get("narration_examples", []),
        "structure": template_data.get("structure", {
            "act1": {"name": "开场", "description": "", "emotion": ""},
            "act2": {"name": "主体", "description": "", "emotion": ""},
            "act3": {"name": "结尾", "description": "", "emotion": ""}
        }),
        "suitable_categories": template_data.get("suitable_categories", []),
        "tags": template_data.get("tags", []),
        "unsuitable_for": template_data.get("unsuitable_for", []),
        "best_duration": template_data.get("best_duration", "60-90秒"),
        "cloned_from": template_data.get("cloned_from"),
        "is_user_template": True,
        "created_at": datetime.now().isoformat()
    }

    templates.append(template)
    _save(templates)
    logger.info(f"创建用户模板: {new_id} - {template['name']}")
    return template


def update(template_id: str, updates: Dict) -> Optional[Dict]:
    templates = _load()
    for i, t in enumerate(templates):
        if t["template_id"] == template_id and t.get("is_user_template"):
            allowed = {"name", "core_strategy", "hook_formula", "narration_style",
                       "narration_examples", "structure", "suitable_categories",
                       "tags", "best_duration", "description"}
            for k, v in updates.items():
                if k in allowed:
                    templates[i][k] = v
            templates[i]["updated_at"] = datetime.now().isoformat()
            _save(templates)
            return templates[i]
    return None


def delete(template_id: str) -> bool:
    templates = _load()
    new_list = [t for t in templates if not (
        t["template_id"] == template_id and t.get("is_user_template")
    )]
    if len(new_list) < len(templates):
        _save(new_list)
        logger.info(f"删除用户模板: {template_id}")
        return True
    return False


async def extract_from_script(script_text: str, template_name: str) -> Dict:
    """使用 Gemini 从脚本文本提炼模板结构"""
    gemini = GeminiClient()

    prompt = f"""你是短视频内容方法论专家。请分析以下脚本，提炼出其创作方法论，输出为可复用的内容模板。

脚本内容：
{script_text[:3000]}

请输出JSON格式（不要其他文字）：
{{
  "core_strategy": "核心创作逻辑，概括这个脚本的整体方法（1-2句话，要具体）",
  "hook_formula": "开场公式（提炼开场套路，用{{产品名}}等占位符表示变量）",
  "narration_style": "旁白风格描述（如：口语化+情感共鸣、理性干货型、痛点驱动型）",
  "narration_examples": [
    "从脚本提炼的典型句式1（用{{占位符}}）",
    "从脚本提炼的典型句式2",
    "从脚本提炼的典型句式3"
  ],
  "structure": {{
    "act1": {{
      "name": "第一幕名称（2-4字）",
      "description": "第一幕做什么、用什么手法（2-3句话）",
      "emotion": "传递的情绪状态"
    }},
    "act2": {{
      "name": "第二幕名称（2-4字）",
      "description": "第二幕做什么、用什么手法（2-3句话）",
      "emotion": "传递的情绪状态"
    }},
    "act3": {{
      "name": "第三幕名称（2-4字）",
      "description": "第三幕做什么、用什么手法（2-3句话）",
      "emotion": "传递的情绪状态"
    }}
  }},
  "suitable_categories": ["最适合的产品品类（2-4个）"],
  "tags": ["标签1", "标签2", "标签3"],
  "best_duration": "推荐视频时长范围，如60-90秒"
}}"""

    try:
        result = await gemini._call_api(prompt)
        text = result.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        extracted = json.loads(text)
        extracted["name"] = template_name
        logger.info(f"AI提炼模板成功: {template_name}")
        return extracted
    except Exception as e:
        logger.error(f"AI提炼模板失败: {e}")
        raise
