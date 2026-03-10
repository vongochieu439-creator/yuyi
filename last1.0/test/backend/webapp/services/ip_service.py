# -*- coding: utf-8 -*-
"""
个人IP工作室服务 - 增强版V2
- 3+1阶段AI记者访谈（背景→热点观点→认知→表达）
- 3步档案合成（事实提炼 + 认知声音建模 + 观点表达提取）
- 3步脚本生成（Think→Write→DeAI）基于观点素材库+表达种子
- 段落反馈+编辑循环（"不像我"+直接编辑→更新声音指纹+表达模式）
- 选题增强（注入商业意图 + strategic_angle）
"""
import json
import copy
import uuid
import asyncio
import tempfile
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from loguru import logger
from .gemini_client import GeminiClient

IP_PROFILES_FILE = Path(__file__).parent.parent / "data" / "ip_profiles.json"
IP_TOPICS_FILE = Path(__file__).parent.parent / "data" / "ip_topics.json"

_profiles_lock = asyncio.Lock()
_topics_lock = asyncio.Lock()


class _FileCache:
    """内存缓存，避免每次都读磁盘"""
    def __init__(self):
        self._profiles: Optional[Dict] = None
        self._topics: Optional[Dict] = None

    def get_profiles(self) -> Optional[Dict]:
        return self._profiles

    def set_profiles(self, data: Dict):
        self._profiles = data

    def get_topics(self) -> Optional[Dict]:
        return self._topics

    def set_topics(self, data: Dict):
        self._topics = data

    def invalidate_profiles(self):
        self._profiles = None

    def invalidate_topics(self):
        self._topics = None


_cache = _FileCache()


# ==================== 档案 CRUD ====================

def _load_profiles() -> Dict:
    """返回深拷贝，防止外部修改污染缓存"""
    cached = _cache.get_profiles()
    if cached is not None:
        return copy.deepcopy(cached)
    if not IP_PROFILES_FILE.exists():
        return {}
    try:
        data = json.loads(IP_PROFILES_FILE.read_text(encoding="utf-8"))
        _cache.set_profiles(data)
        return copy.deepcopy(data)
    except Exception as e:
        logger.error(f"加载IP档案文件失败: {e}")
        return {}


def _save_profiles(data: Dict):
    IP_PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=2)
    # 原子写入：先写临时文件，再 os.replace
    fd, tmp_path = tempfile.mkstemp(
        dir=str(IP_PROFILES_FILE.parent), suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, str(IP_PROFILES_FILE))
        _cache.set_profiles(data)
    except Exception:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _load_topics() -> Dict:
    """返回深拷贝，防止外部修改污染缓存"""
    cached = _cache.get_topics()
    if cached is not None:
        return copy.deepcopy(cached)
    if not IP_TOPICS_FILE.exists():
        return {}
    try:
        data = json.loads(IP_TOPICS_FILE.read_text(encoding="utf-8"))
        _cache.set_topics(data)
        return copy.deepcopy(data)
    except Exception as e:
        logger.error(f"加载选题文件失败: {e}")
        return {}


def _save_topics(data: Dict):
    IP_TOPICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=2)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(IP_TOPICS_FILE.parent), suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, str(IP_TOPICS_FILE))
        _cache.set_topics(data)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def get_all_profiles() -> List[Dict]:
    return list(_load_profiles().values())


def get_profile(profile_id: str) -> Optional[Dict]:
    return _load_profiles().get(profile_id)


async def delete_profile(profile_id: str) -> bool:
    async with _profiles_lock:
        profiles = _load_profiles()
        if profile_id in profiles:
            del profiles[profile_id]
            _save_profiles(profiles)
            async with _topics_lock:
                topics = _load_topics()
                topics.pop(profile_id, None)
                _save_topics(topics)
            return True
    return False


async def save_profile(profile: Dict) -> Dict:
    async with _profiles_lock:
        profiles = _load_profiles()
        profiles[profile["profile_id"]] = profile
        _save_profiles(profiles)
    return profile


def get_topics_for_profile(profile_id: str) -> List[Dict]:
    return _load_topics().get(profile_id, [])


async def save_topics_for_profile(profile_id: str, topics: List[Dict]):
    async with _topics_lock:
        data = _load_topics()
        data[profile_id] = topics
        _save_topics(data)


# ==================== 热点话题获取 ====================

HOT_TOPICS_FILTER_PROMPT = """从以下热门话题列表中，筛选出与"{industry}"行业最相关的5-8个话题。
如果列表中没有足够相关的，可以基于行业常识补充。
每个话题给出一个讨论角度（让受访者容易发表看法的角度）。

【热门话题原始列表】
{raw_topics}

输出JSON数组（不要其他文字）：
[
  {{"title": "话题标题", "angle": "推荐讨论角度（如：'你觉得这对你们行业影响大吗？'）", "source": "tikhub/tavily/补充"}}
]
"""


async def fetch_hot_topics_for_industry(industry: str) -> List[Dict]:
    """并行调用TikHub+Tavily获取行业热点，用Gemini筛选"""
    industry = _sanitize_input(industry, max_length=50)
    raw_topics = []

    async def _fetch_tikhub():
        try:
            from .tikhub_client import TikHubClient
            client = TikHubClient()
            topics = await client.get_hot_topics()
            return [{"title": t.get("title", ""), "source": "tikhub"} for t in topics[:20]]
        except Exception as e:
            logger.warning(f"TikHub热点获取失败: {e}")
            return []

    async def _fetch_tavily():
        try:
            from .tavily_client import TavilyClient
            client = TavilyClient()
            result = await client.search(f"{industry} 热点话题 {datetime.now().year}", max_results=10)
            return [{"title": r.get("title", ""), "source": "tavily"} for r in result.get("results", [])]
        except Exception as e:
            logger.warning(f"Tavily热点获取失败: {e}")
            return []

    # 并行获取
    tikhub_results, tavily_results = await asyncio.gather(
        _fetch_tikhub(), _fetch_tavily()
    )
    raw_topics = tikhub_results + tavily_results

    if not raw_topics:
        logger.warning("热点话题获取全部失败，使用通用话题")
        return [
            {"title": "AI对行业的冲击", "angle": "你觉得AI会取代你们行业的哪些岗位？", "source": "fallback"},
            {"title": "年轻人入行建议", "angle": "如果一个年轻人想进你这个行业，你会怎么说？", "source": "fallback"},
            {"title": "行业最大的坑", "angle": "你见过最多人踩的坑是什么？", "source": "fallback"},
            {"title": "未来3年趋势", "angle": "你觉得未来3年你们行业最大的变化是什么？", "source": "fallback"},
            {"title": "同行最常犯的错", "angle": "你最看不惯同行的什么做法？", "source": "fallback"},
        ]

    # 用Gemini筛选
    gemini = GeminiClient()
    raw_text = "\n".join(f"- {t['title']} (来源: {t['source']})" for t in raw_topics)
    prompt = HOT_TOPICS_FILTER_PROMPT.format(industry=industry, raw_topics=raw_text)

    try:
        result = await gemini._call_api(prompt)
        filtered = _parse_json(result)
        if isinstance(filtered, list) and len(filtered) >= 3:
            logger.info(f"筛选出 {len(filtered)} 个{industry}行业热点话题")
            return filtered[:8]
    except Exception as e:
        logger.warning(f"热点话题筛选失败: {e}")

    # 筛选失败，返回原始前5个
    return [{"title": t["title"], "angle": "你怎么看这个话题？", "source": t["source"]} for t in raw_topics[:5]]


# ==================== 3+1阶段AI记者访谈 ====================

# 阶段1：背景采集（3-5轮）—— 只问事实
JOURNALIST_PROMPT_BACKGROUND = """你是一位资深商业记者，正在对一位行业人士做背景调研。你的任务是快速、精准地收集事实信息。

【采集目标】只问事实，不要问观点和情绪：
1. 行业和具体领域
2. 公司/业务的基本情况（规模、年限、主营业务）
3. 个人角色和职责
4. 关键里程碑（创业时间、重要转折、核心成就）
5. 团队和业务现状

【当前状态】
受访者：{name}，{industry}行业
已进行轮数：{round_count}

【对话记录】
{chat_history}

【你的任务】
- 如果关键事实还不完整（少于3轮），继续提问
- 如果已收集到足够的事实背景（通常3-5轮），设置is_done=true
- 每次只问一个问题，语气像朋友聊天
- 优先问具体数字和时间节点
- 不要问"你怎么看""你觉得"这类观点问题

输出JSON（不要其他文字）：
如果继续：{{"question": "下一个问题", "is_done": false, "round_hint": "目的"}}
如果结束：{{"question": "好的，基本情况我了解了！接下来想跟你聊几个行业热点话题...", "is_done": true}}
"""

# 阶段1.5：热点观点（3-5轮）—— 聊行业热点，采集立场+原话
JOURNALIST_PROMPT_HOT_TOPICS = """你是一位资深商业记者，正在跟受访者聊行业热点话题，目标是采集他对每个话题的立场和原话表达。

【采集目标】
对每个话题，你需要获得：
1. 他的明确立场（赞成/反对/中立+理由）
2. 他的原话表达（最好让他用一句话概括观点）

【热门话题参考】
{hot_topics}

【当前状态】
受访者：{name}，{industry}行业
已进行轮数：{round_count}（热点观点阶段）

【对话记录】
{chat_history}

【每个话题的采集流程】
1. 简要介绍话题 → "你怎么看？"
2. 追问理由 → "为什么这么想？能举个例子吗？"
3. 压缩总结 → "能用一句话概括你的看法吗？"

【特殊处理】
如果对方说"我说错了"、"不对不对"、"等等让我重新说"，
承认修正（"好，以你最新说的为准"），继续用最新版本。

【规则】
- 每个话题聊1-2轮就够，不要在一个话题上纠缠太久
- 一定要追问"为什么"，不要只记录态度
- 已聊3-5轮后可以设置is_done=true
- 每次只问一个问题

输出JSON（不要其他文字）：
如果继续：{{"question": "下一个问题", "is_done": false, "round_hint": "目的"}}
如果结束：{{"question": "好，你对这些话题的看法都很有特色。接下来我想更深入地了解你的思维方式...", "is_done": true}}
"""

# 阶段2：认知挖掘（4-8轮）—— 刺激性问题引出真实想法
JOURNALIST_PROMPT_COGNITIVE = """你是一位犀利的深度访谈记者，擅长用挑战性的问题引出受访者的真实想法。你不是来拍马屁的，而是要像"十三邀"的许知远一样，用有深度的问题让对方"掏心窝子"。

【挖掘目标】
1. 思维模型：他信什么？他做决策的底层逻辑是什么？
2. 情绪触发点：什么事让他最生气？什么事让他最骄傲？什么事让他最焦虑？
3. 逆主流观点：他和大多数同行有什么不同看法？他觉得行业里什么"常识"是错的？
4. 商业意图：他做IP的真正目的是什么？想被记住为什么样的人？

【问题弹药库（选择合适的使用，不要全部问）】
- "你觉得你的行业里，大部分人在哪件事上是错的？"
- "如果一个年轻人要进你这个行业，你会劝退他吗？为什么？"
- "最近让你最生气的一件行业内的事是什么？"
- "你做过最艰难的决定是什么？当时怎么想的？"
- "用30秒安利一下你的产品/服务"
- "你最看不惯同行的什么行为？"
- "如果明天你的公司倒闭了，你最不甘心的是什么？"
- "你觉得你和竞争对手最大的不同是什么？"
- "你希望别人提起你时，第一个想到的词是什么？"
- "做短视频IP，你最想让什么样的人看到？想让他们觉得你是什么样的人？"

【当前状态】
受访者：{name}，{industry}行业
已进行轮数：{round_count}（认知阶段）

【对话记录】
{chat_history}

【规则】
- 对方说到情绪化的内容必须追问细节
- 对方给出"正确但无趣"的回答时要挑战他（"这是标准答案，我想听你真实的想法"）
- 每次只问一个问题
- 如果已经挖到足够的认知信息（通常4-8轮），设置is_done=true

输出JSON（不要其他文字）：
如果继续：{{"question": "下一个问题", "is_done": false, "round_hint": "目的"}}
如果结束：{{"question": "聊到这我对你的想法了解很多了。最后我想听你讲几个故事，感受一下你平时怎么说话...", "is_done": true}}
"""

# 阶段3：表达采样（3-4轮）—— 捕捉语言组织方式
JOURNALIST_PROMPT_VOICE = """你是一位语言风格研究员，需要通过几个特定场景，采集受访者的真实表达方式。你关注的不是内容本身，而是他**怎么组织语言**。

【采样目标】
1. 句式习惯：句子长短、是否爱用反问、排比、类比
2. 论证结构：先说结论还是先铺垫？用数据还是用故事？
3. 比喻偏好：喜欢用什么领域的比喻（军事、体育、生活、商业）
4. 情绪表达：激动时怎么说话？自嘲时怎么表达？
5. 口头禅和禁忌：常说什么词？从不说什么词？

【场景问题（选择合适的使用）】
- "假装我是你的新员工，你怎么跟我解释你们公司是做什么的？就像平时跟人说一样"
- "你怎么跟员工解释为什么要砍掉一个项目？假装我就是那个项目负责人"
- "讲一个你印象最深的客户故事，就像跟朋友吃饭时聊天那样讲"
- "如果让你在朋友圈发一条话，介绍你最得意的一个成果，你会怎么写？"
- "用你平时说话的方式，解释一下你们行业最复杂的一个概念"

【当前状态】
受访者：{name}，{industry}行业
已进行轮数：{round_count}（表达采样阶段）

【对话记录】
{chat_history}

【规则】
- 要求他用"平时说话"的方式回答，不要"端着"
- 如果他说得太书面，提醒："这不像你平时说话吧？用大白话再说一遍"
- 每次只出一个场景
- 通常3-4轮就够了，设置is_done=true

输出JSON（不要其他文字）：
如果继续：{{"question": "下一个场景", "is_done": false, "round_hint": "目的"}}
如果结束：{{"question": "太棒了！你的故事和表达都非常有特色，我已经对你有了深入了解。接下来我来为你整理专属IP档案...", "is_done": true}}
"""


async def conduct_interview(
    name: str,
    industry: str,
    chat_history: List[Dict],
    phase: str = "background",
    hot_topics: str = ""
) -> Dict:
    """
    AI记者动态访谈 - 按phase选择不同prompt
    phase: "background" | "hot_topics" | "cognitive" | "voice"
    返回: {question, is_done, round_hint}
    """
    gemini = GeminiClient()

    # 清理用户输入
    name = _sanitize_input(name, max_length=50)
    industry = _sanitize_input(industry, max_length=50)

    # 构建对话历史文本
    history_text = ""
    for msg in chat_history:
        role = "记者" if msg["role"] == "ai" else f"{name}"
        content = _sanitize_input(msg.get('content', ''), max_length=2000)
        history_text += f"{role}：{content}\n\n"

    round_count = len([m for m in chat_history if m["role"] == "user"])

    # 按阶段选择prompt
    prompt_map = {
        "background": JOURNALIST_PROMPT_BACKGROUND,
        "hot_topics": JOURNALIST_PROMPT_HOT_TOPICS,
        "cognitive": JOURNALIST_PROMPT_COGNITIVE,
        "voice": JOURNALIST_PROMPT_VOICE,
    }
    prompt_template = prompt_map.get(phase, JOURNALIST_PROMPT_BACKGROUND)

    # hot_topics阶段需要额外的hot_topics参数
    format_kwargs = {
        "name": name,
        "industry": industry,
        "round_count": round_count,
        "chat_history": history_text or "（访谈刚开始）"
    }
    if phase == "hot_topics":
        format_kwargs["hot_topics"] = _sanitize_input(hot_topics, max_length=2000) or "- AI对行业的冲击\n- 年轻人入行建议\n- 行业最大的坑"

    prompt = prompt_template.format(**format_kwargs)

    try:
        result = await gemini._call_api(prompt)
        parsed = _parse_json(result)
        if not isinstance(parsed, dict) or "question" not in parsed:
            logger.warning(f"AI返回结构缺少question字段: {parsed}")
            raise ValueError("AI返回结构不完整")
        return parsed
    except Exception as e:
        logger.error(f"AI记者访谈失败(phase={phase}): {e}")
        fallback_questions = {
            "background": f"能告诉我，你在{industry}行业做了多久了？公司目前什么规模？",
            "hot_topics": "最近AI对各行各业冲击挺大的，你觉得对你们行业影响大吗？",
            "cognitive": "你觉得你的行业里，大部分人在哪件事上是错的？",
            "voice": "假装我是你的新员工，你怎么跟我解释你们公司是做什么的？",
        }
        return {
            "question": fallback_questions.get(phase, "能具体说说吗？"),
            "is_done": False
        }


# ==================== 2步档案合成 ====================

# 第1步：事实提炼（和原来类似）
PROFILE_SYNTHESIS_PROMPT = """你是顶级IP策划师。根据以下访谈记录，提炼一份结构化的个人IP档案。

受访者：{name}，{industry}行业

【完整访谈记录】
{qa_text}

请输出JSON格式的IP档案（不要其他文字）：
{{
  "background_summary": "2-3句话概括这个人的背景（具体，包含行业/年限/成就）",
  "key_stories": [
    "故事1：具体情节描述（有时间/数字/冲突，50字内）",
    "故事2：...",
    "故事3：..."
  ],
  "unique_insights": [
    "洞见1：他对行业/创业/人生的独特看法（要有冲击性）",
    "洞见2：...",
    "洞见3：..."
  ],
  "speaking_style": "描述他的说话风格（根据回答内容推断：如'直接犀利，爱用数字说话，有时自嘲'）",
  "signature_phrases": ["从访谈中摘录的他的典型表达方式或口头禅（原话或近似原话）", "..."],
  "content_pillars": ["内容支柱1（他可以持续输出的主题）", "内容支柱2", "内容支柱3"],
  "target_audience": "他的目标受众是谁（具体描述）",
  "values": "他的核心价值观/人生信条（用他自己的方式表达）",
  "ip_positioning": "一句话定位：他是谁，能给观众带来什么（要有辨识度）"
}}
"""

# 第2步：认知+声音建模
PROFILE_SYNTHESIS_PROMPT_COGNITIVE = """你是一位认知科学家和语言学家。你的任务是分析访谈记录中的**模式**，不是内容。

重点分析：
1. 他怎么论证一个观点（先结论后案例？先数据后感受？）
2. 他用什么类型的比喻（军事？生活？体育？商业？）
3. 什么话题让他情绪波动（语气变强烈、用词变激烈）
4. 他有哪些"反常识"观点
5. 他说话的句式特征（短句多还是长句多？爱用反问？排比？）
6. 他绝对不会用的表达方式（太文绉绉的词、互联网黑话等）

受访者：{name}，{industry}行业

【完整访谈记录】
{qa_text}

请输出JSON格式（不要其他文字）：
{{
  "thinking_models": ["他信奉的核心原则/思维模型，3-5个，如：产品为王、现金流就是命"],
  "decision_framework": "他做决策的方式（一句话概括，如：数据驱动，先算账再决定）",
  "emotional_triggers": {{
    "anger": ["让他生气/愤怒的事，1-3个"],
    "passion": ["让他兴奋/骄傲的事，1-3个"],
    "pride": ["他最引以为傲的成就，1-3个"]
  }},
  "contrarian_views": ["他和主流不同的观点，2-4个，必须来自访谈内容"],
  "voice_fingerprint": {{
    "sentence_pattern": "句式特征描述（如：短句为主，偶尔一句长句总结）",
    "rhetoric_preference": "修辞偏好（如：爱用反问和数据）",
    "argument_structure": "论证结构（如：先抛结论，再用案例解释）",
    "metaphor_domain": "比喻来源领域（如：军事和生活）",
    "forbidden_words": ["他绝对不会说的AI味/互联网黑话词汇，如：赋能、抓手、底层逻辑、颗粒度、闭环、打法"],
    "raw_quotes": ["从访谈中摘录的5-8句最有个人特色的原话（一字不改）"]
  }},
  "business_intent": {{
    "primary_goal": "做IP的核心商业目的（如：通过IP招到优秀人才）",
    "target_perception": "希望观众觉得自己是什么样的人（如：务实、靠谱、有远见的行业老手）",
    "competitive_context": "和竞品/同行IP的差异化（如：竞品老板都在发鸡汤，我要发真实的）"
  }},
  "identity_attitude": {{
    "status_level": "身份定位（如：行业大佬/草根创业者/技术专家/行业新锐）",
    "communication_tone": "沟通基调（如：权威但不装，偶尔自嘲）",
    "hook_preference": "开场偏好（如：直接抛观点，不需要讨好观众）"
  }}
}}
"""


# 第3步：观点+表达提取
PROFILE_SYNTHESIS_PROMPT_OPINIONS = """你是一位内容分析专家。从以下访谈记录中提取受访者对每个话题的明确观点和表达模式。

【重要规则】
- 只提取真实表达过的观点，不编造
- 如果受访者纠正过自己（"我说错了"、"不对不对"），只取最终版本
- raw_expression必须是接近原话的表述，不是你的总结改写
- emotion只从以下选择：angry/passionate/confident/calm/humorous/worried
- confidence范围0.5-1.0，越肯定越高

受访者：{name}，{industry}行业

【完整访谈记录】
{qa_text}

请输出JSON格式（不要其他文字）：
{{
  "opinions": [
    {{
      "topic": "话题关键词",
      "stance": "一句话立场",
      "reasoning": "他的理由（2-3句）",
      "raw_expression": "他的原话或接近原话的表述（一句话）",
      "emotion": "angry/passionate/confident/calm/humorous/worried",
      "confidence": 0.8
    }}
  ],
  "expression_patterns": {{
    "preferred_openings": ["他喜欢用的开场方式，2-4个，如：'我跟你说个事儿'"],
    "preferred_transitions": ["他喜欢用的过渡方式，2-4个，如：'但问题来了'"],
    "preferred_closings": ["他喜欢用的收尾方式，2-4个，如：'你品品这个道理'"],
    "favorite_phrases": [
      {{"phrase": "常用表达", "context": "使用场景（如decision_making/argument/humor）"}}
    ],
    "argument_templates": [
      {{"pattern": "论证结构描述（如'先结论后举例'）", "example": "具体例子"}}
    ]
  }}
}}
"""


async def finalize_profile(
    name: str,
    industry: str,
    role: str,
    chat_history: List[Dict]
) -> Dict:
    """
    访谈结束后，AI提炼完整IP档案（2步合成）
    """
    gemini = GeminiClient()

    # 清理用户输入
    name = _sanitize_input(name, max_length=50)
    industry = _sanitize_input(industry, max_length=50)
    role = _sanitize_input(role, max_length=50)

    qa_text = ""
    for msg in chat_history:
        speaker = "记者" if msg["role"] == "ai" else name
        content = _sanitize_input(msg.get('content', ''), max_length=2000)
        qa_text += f"【{speaker}】{content}\n\n"

    # 第1步：事实提炼
    prompt1 = PROFILE_SYNTHESIS_PROMPT.format(
        name=name,
        industry=industry,
        qa_text=qa_text
    )

    try:
        result1 = await gemini._call_api(prompt1)
        synthesized = _parse_json(result1)
    except Exception as e:
        logger.error(f"IP档案事实提炼失败: {e}")
        raise

    # 第2步：认知+声音建模
    cognitive = {}
    try:
        prompt2 = PROFILE_SYNTHESIS_PROMPT_COGNITIVE.format(
            name=name,
            industry=industry,
            qa_text=qa_text
        )
        result2 = await gemini._call_api(prompt2)
        cognitive = _parse_json(result2)
        logger.info(f"认知建模完成: {name}")
    except Exception as e:
        logger.warning(f"认知建模失败（不影响基础档案）: {e}")
        cognitive = {}

    # 第3步：观点+表达提取
    opinion_bank = []
    expression_patterns = {}
    try:
        prompt3 = PROFILE_SYNTHESIS_PROMPT_OPINIONS.format(
            name=name,
            industry=industry,
            qa_text=qa_text
        )
        result3 = await gemini._call_api(prompt3)
        opinions_data = _parse_json(result3)

        # 构建opinion_bank
        for op in opinions_data.get("opinions", []):
            opinion_bank.append({
                "opinion_id": f"op_{uuid.uuid4().hex[:6]}",
                "topic": op.get("topic", ""),
                "stance": op.get("stance", ""),
                "reasoning": op.get("reasoning", ""),
                "raw_expression": op.get("raw_expression", ""),
                "emotion": op.get("emotion", "calm"),
                "confidence": op.get("confidence", 0.7),
                "topic_source": "interview",
                "created_at": datetime.now().isoformat(),
                "used_count": 0
            })

        expression_patterns = opinions_data.get("expression_patterns", {})
        # 确保所有子字段存在
        expression_patterns.setdefault("preferred_openings", [])
        expression_patterns.setdefault("preferred_transitions", [])
        expression_patterns.setdefault("preferred_closings", [])
        expression_patterns.setdefault("favorite_phrases", [])
        expression_patterns.setdefault("argument_templates", [])

        logger.info(f"观点提取完成: {name}, {len(opinion_bank)}条观点, 表达模式已建立")
    except Exception as e:
        logger.warning(f"观点+表达提取失败（不影响基础档案）: {e}")

    # 合并三步结果 — AI输出放前面，核心字段放后面确保不被覆盖
    profile_id = f"ip_{uuid.uuid4().hex[:8]}"
    profile = {
        **synthesized,
        **cognitive,
        "profile_id": profile_id,
        "name": name,
        "industry": industry,
        "role": role,
        "interview_qa": chat_history,
        "opinion_bank": opinion_bank,
        "expression_patterns": expression_patterns,
        "edit_history": [],
        "created_at": datetime.now().isoformat()
    }
    await save_profile(profile)
    logger.info(f"IP档案创建完成: {profile_id} - {name}, {len(opinion_bank)}条观点素材")
    return profile


async def supplement_profile(profile_id: str, chat_history: List[Dict]) -> Dict:
    """
    补充访谈：只跑Step3（观点+表达提取），追加到现有档案。
    不覆盖Step1/2的基础信息。
    """
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError(f"IP档案不存在: {profile_id}")
    if not chat_history or len(chat_history) < 2:
        raise ValueError("补充访谈记录太短，至少需要一轮对话")

    gemini = GeminiClient()

    # 构建访谈文本
    qa_text = ""
    for msg in chat_history:
        speaker = "记者" if msg["role"] == "ai" else profile["name"]
        qa_text += f"【{speaker}】{msg['content']}\n\n"

    # 只跑Step3：观点+表达提取
    new_opinion_bank = []
    new_expression_patterns = {}
    try:
        prompt3 = PROFILE_SYNTHESIS_PROMPT_OPINIONS.format(
            name=profile["name"],
            industry=profile["industry"],
            qa_text=qa_text
        )
        result3 = await gemini._call_api(prompt3)
        opinions_data = _parse_json(result3)

        # 构建新的opinion_bank条目
        for op in opinions_data.get("opinions", []):
            new_opinion_bank.append({
                "opinion_id": f"op_{uuid.uuid4().hex[:6]}",
                "topic": op.get("topic", ""),
                "stance": op.get("stance", ""),
                "reasoning": op.get("reasoning", ""),
                "raw_expression": op.get("raw_expression", ""),
                "emotion": op.get("emotion", "calm"),
                "confidence": op.get("confidence", 0.7),
                "topic_source": "supplement_interview",
                "created_at": datetime.now().isoformat(),
                "used_count": 0
            })

        new_expression_patterns = opinions_data.get("expression_patterns", {})
        logger.info(f"补充访谈提取完成: {profile['name']}, {len(new_opinion_bank)}条新观点")
    except Exception as e:
        logger.error(f"补充访谈观点提取失败: {e}")
        raise

    # 追加opinion_bank（不覆盖原有的）
    existing_opinion_bank = profile.get("opinion_bank", [])
    existing_opinion_bank.extend(new_opinion_bank)
    profile["opinion_bank"] = existing_opinion_bank

    # 合并expression_patterns（去重追加）
    existing_expr = profile.get("expression_patterns", {})
    for key in ["preferred_openings", "preferred_transitions", "preferred_closings"]:
        existing_list = existing_expr.get(key, [])
        new_list = new_expression_patterns.get(key, [])
        for item in new_list:
            if item not in existing_list:
                existing_list.append(item)
        existing_expr[key] = existing_list

    # favorite_phrases 去重追加（按phrase字段）
    existing_phrases = existing_expr.get("favorite_phrases", [])
    existing_phrase_texts = {fp.get("phrase", "") for fp in existing_phrases}
    for fp in new_expression_patterns.get("favorite_phrases", []):
        if fp.get("phrase") and fp["phrase"] not in existing_phrase_texts:
            existing_phrases.append(fp)
    existing_expr["favorite_phrases"] = existing_phrases

    # argument_templates 去重追加（按pattern字段）
    existing_templates = existing_expr.get("argument_templates", [])
    existing_patterns = {t.get("pattern", "") for t in existing_templates}
    for t in new_expression_patterns.get("argument_templates", []):
        if t.get("pattern") and t["pattern"] not in existing_patterns:
            existing_templates.append(t)
    existing_expr["argument_templates"] = existing_templates

    profile["expression_patterns"] = existing_expr

    # 追加补充访谈记录
    supplement_history = profile.get("supplement_interviews", [])
    supplement_history.append({
        "chat_history": chat_history,
        "new_opinions_count": len(new_opinion_bank),
        "created_at": datetime.now().isoformat()
    })
    profile["supplement_interviews"] = supplement_history

    await save_profile(profile)
    logger.info(f"补充访谈已合并: {profile_id}, 新增{len(new_opinion_bank)}条观点, 总计{len(existing_opinion_bank)}条")
    return profile


# ==================== 选题生成（增强版） ====================

TOPIC_GENERATION_PROMPT = """你是顶级短视频选题策划，专为抖音个人IP设计内容。

【IP档案】
姓名：{name}，{industry} {role}
定位：{ip_positioning}
背景：{background_summary}

核心故事素材：
{key_stories}

独特观点：
{unique_insights}

逆主流观点：
{contrarian_views}

内容支柱：{content_pillars}
目标受众：{target_audience}

【商业意图】
核心目的：{business_primary_goal}
想被记住为：{business_target_perception}
竞争差异：{business_competitive_context}

【任务】
基于以上IP档案，生成{count}个高质量选题。每个选题必须服务于老板的商业目标。

选题类型分布（要有以下几类）：
- 故事型（4-5个）：用真实经历讲述，有冲突有转折
- 观点型（3-4个）：反常识观点，挑战主流认知
- 干货型（3-4个）：行业洞察/实用方法论，展示专业度
- 日常型（2-3个）：老板日记/背后故事，建立真实感
- 争议型（2-3个）：有争议的话题，激发讨论

每个选题必须基于档案中的真实素材（不要捏造），输出JSON数组：
[
  {{
    "title": "吸引人的标题（直接是Hooks，不超过20字）",
    "type": "故事型/观点型/干货型/日常型/争议型",
    "hook_opening": "开场第一句话（必须是炸裂的，能让人停下来的）",
    "core_angle": "这个视频的核心角度和卖点（1句话）",
    "story_materials": "用到了档案中哪些素材（说明）",
    "content_outline": ["第一幕：...", "第二幕：...", "第三幕：..."],
    "why_viral": "为什么这个选题可能爆（平台算法角度）",
    "estimated_duration": "建议时长（秒）",
    "strategic_angle": "这条内容如何服务于老板的商业目标（1句话）"
  }},
  ...
]
"""


TOPIC_GENERATION_PROMPT_SIMPLE = """你是顶级短视频选题策划。基于以下IP档案，生成{count}个选题。

【IP档案】
姓名：{name}，{industry} {role}
定位：{ip_positioning}
背景：{background_summary}
独特观点：{unique_insights}
内容支柱：{content_pillars}

每个选题只需3个字段，输出JSON数组（不要其他文字）：
[
  {{"title": "吸引人的标题（不超过20字）", "hook_opening": "开场第一句话", "core_angle": "核心角度（1句话）"}}
]
"""


def _build_topic_prompt_kwargs(profile: Dict, count: int) -> Dict:
    """构建选题prompt所需的参数字典"""
    key_stories_text = "\n".join(f"- {s}" for s in profile.get("key_stories", []))
    unique_insights_text = "\n".join(f"- {i}" for i in profile.get("unique_insights", []))
    content_pillars_text = "、".join(profile.get("content_pillars", []))
    contrarian_views_text = "\n".join(f"- {v}" for v in profile.get("contrarian_views", []))
    biz = profile.get("business_intent", {})
    return {
        "name": profile["name"],
        "industry": profile["industry"],
        "role": profile.get("role", "创始人"),
        "ip_positioning": profile.get("ip_positioning", ""),
        "background_summary": profile.get("background_summary", ""),
        "key_stories": key_stories_text,
        "unique_insights": unique_insights_text,
        "contrarian_views": contrarian_views_text or "（暂无）",
        "content_pillars": content_pillars_text,
        "target_audience": profile.get("target_audience", ""),
        "business_primary_goal": biz.get("primary_goal", "打造行业影响力"),
        "business_target_perception": biz.get("target_perception", "专业、真实"),
        "business_competitive_context": biz.get("competitive_context", "无"),
        "count": count,
    }


def _build_topics_list(topics_raw: List[Dict], profile_id: str, count: int, start_index: int = 0) -> List[Dict]:
    """将AI返回的原始选题列表转换为标准格式"""
    topics = []
    for i, t in enumerate(topics_raw[:count]):
        item = dict(t)  # AI输出先铺底
        item.update({    # 系统字段覆盖，防止AI输出篡改
            "topic_id": f"topic_{uuid.uuid4().hex[:8]}",
            "profile_id": profile_id,
            "index": start_index + i + 1,
            "created_at": datetime.now().isoformat()
        })
        topics.append(item)
    return topics


async def generate_topics(profile_id: str, count: int = 15) -> List[Dict]:
    """基于IP档案批量生成选题（增强版：分批防截断+重试）"""
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError(f"IP档案不存在: {profile_id}")

    gemini = GeminiClient()
    kwargs = _build_topic_prompt_kwargs(profile, count)

    # === 策略1：一次性生成全部 ===
    try:
        prompt = TOPIC_GENERATION_PROMPT.format(**kwargs)
        result = await gemini._call_api(prompt)
        topics_raw = _parse_json(result)
        if isinstance(topics_raw, list) and len(topics_raw) >= 3:
            topics = _build_topics_list(topics_raw, profile_id, count)
            await save_topics_for_profile(profile_id, topics)
            logger.info(f"为 {profile['name']} 一次性生成 {len(topics)} 个选题")
            return topics
    except Exception as e:
        logger.warning(f"选题一次性生成失败（JSON可能被截断），尝试分批: {e}")

    # === 策略2：分两批生成，合并结果 ===
    try:
        batch1_count = count // 2
        batch2_count = count - batch1_count
        all_topics = []

        for batch_idx, batch_count in enumerate([batch1_count, batch2_count]):
            batch_kwargs = {**kwargs, "count": batch_count}
            prompt = TOPIC_GENERATION_PROMPT.format(**batch_kwargs)
            result = await gemini._call_api(prompt)
            batch_raw = _parse_json(result)
            if isinstance(batch_raw, list):
                batch_topics = _build_topics_list(batch_raw, profile_id, batch_count, start_index=len(all_topics))
                all_topics.extend(batch_topics)
                logger.info(f"分批生成第{batch_idx+1}批: {len(batch_raw)}个选题")

        if len(all_topics) >= 3:
            await save_topics_for_profile(profile_id, all_topics)
            logger.info(f"为 {profile['name']} 分批生成 {len(all_topics)} 个选题")
            return all_topics
    except Exception as e:
        logger.warning(f"选题分批生成也失败，尝试精简模式: {e}")

    # === 策略3：精简prompt，只要3字段，生成5个 ===
    try:
        simple_kwargs = {
            "name": profile["name"],
            "industry": profile["industry"],
            "role": profile.get("role", "创始人"),
            "ip_positioning": profile.get("ip_positioning", ""),
            "background_summary": profile.get("background_summary", ""),
            "unique_insights": "\n".join(f"- {i}" for i in profile.get("unique_insights", [])),
            "content_pillars": "、".join(profile.get("content_pillars", [])),
            "count": 5,
        }
        prompt = TOPIC_GENERATION_PROMPT_SIMPLE.format(**simple_kwargs)
        result = await gemini._call_api(prompt)
        topics_raw = _parse_json(result)
        if isinstance(topics_raw, list):
            topics = _build_topics_list(topics_raw, profile_id, 5)
            await save_topics_for_profile(profile_id, topics)
            logger.info(f"为 {profile['name']} 精简模式生成 {len(topics)} 个选题")
            return topics
    except Exception as e:
        logger.error(f"选题精简模式也失败: {e}")
        raise ValueError(f"选题生成失败（已尝试3种策略）: {e}")


# ==================== 3步脚本生成 ====================


_STOPWORDS = set("的了是在我你他她它们这那个就也都要会可以不和与及等但又或")


def _extract_keywords(text: str) -> set:
    """按标点分词 + 2-gram滑窗 + 停用词过滤"""
    if not text:
        return set()
    # 按常见标点和空格分割
    segments = re.split(r'[，。！？、；：\s,\.\?!;:\-—""''（）()\[\]{}]+', text)
    keywords = set()
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        # 整段加入（如果长度>=2且不全是停用词字符）
        if len(seg) >= 2 and not all(c in _STOPWORDS for c in seg):
            keywords.add(seg)
        # 2-gram 滑窗：过滤掉两个字符都是停用词的组合
        for j in range(len(seg) - 1):
            bigram = seg[j:j+2]
            if not (bigram[0] in _STOPWORDS and bigram[1] in _STOPWORDS):
                keywords.add(bigram)
    # 过滤单字停用词
    keywords -= _STOPWORDS
    return keywords


def _find_relevant_opinions(opinion_bank: List[Dict], topic_title: str) -> List[Dict]:
    """从观点素材库中找与选题相关的观点（关键词集合交集）"""
    if not opinion_bank:
        return []
    topic_kw = _extract_keywords(topic_title)
    if not topic_kw:
        return opinion_bank[:5]
    scored = []
    for op in opinion_bank:
        op_text = op.get("topic", "") + op.get("stance", "") + op.get("reasoning", "")
        op_kw = _extract_keywords(op_text)
        overlap = len(topic_kw & op_kw)
        if overlap > 0:
            scored.append((overlap, op))
    scored.sort(key=lambda x: -x[0])
    result = [op for _, op in scored[:5]]
    if len(result) < 3:
        return opinion_bank[:5]
    return result


# Step 1: Think（思考备忘录）— 基于真实观点
SCRIPT_THINK_PROMPT = """你是{name}本人。现在你要拍一条短视频，在拍之前你先想一想。

【你的基本信息】
{industry} {role}，{background_summary}

【你的思维方式】
核心原则：{thinking_models}
决策方式：{decision_framework}
逆主流观点：{contrarian_views}

【你对相关话题的真实看法（来自之前访谈）】
{relevant_opinions}

【今天要拍的内容】
选题：{topic_title}
核心角度：{core_angle}

【请以第一人称思考以下问题，像自言自语一样】
1. 关于这个话题，我之前说过什么？我的真实观点是什么？（优先用上面"真实看法"里的内容）
2. 我有什么亲身经历跟这相关？（具体的时间、地点、人物）
3. 我和大多数人看法有什么不同？（我的"反常识"在哪）
4. 我希望观众看完记住我什么？（一个词或一句话）
5. 这期我的情绪基调应该是什么？（愤怒？自信？自嘲？语重心长？）

输出500字以内的思考备忘录，像在内心独白：
"""

# Step 2: Write（基于思考写稿）— 用原话当种子
SCRIPT_WRITE_PROMPT = """你是{name}的专属内容创作者。现在要基于{name}的思考备忘录，写出一个100%是{name}本人口吻的短视频口播稿。

【人物档案】
姓名：{name} | 行业：{industry} | 角色：{role}
个人定位：{ip_positioning}
背景：{background_summary}

核心故事素材（必须用到）：
{key_stories}

独特观点（可以融入）：
{unique_insights}

【表达种子 — 必须直接使用或改编】
开场方式（选一个）：{preferred_openings}
过渡方式：{preferred_transitions}
收尾方式：{preferred_closings}

他的原话（至少融入2句）：
{all_raw_quotes}

论证模板（按这个结构组织）：
{argument_templates}

【他对这个话题的真实观点】
{matched_opinion_seed}

【说话方式——兜底参考（优先用上面的表达种子）】
风格特征：{speaking_style}
典型表达：{signature_phrases}
价值观：{values}

【声音指纹——必须遵守】
句式特征：{sentence_pattern}
修辞偏好：{rhetoric_preference}
论证结构：{argument_structure}（写稿时论证必须按这个结构来）
比喻领域：{metaphor_domain}（所有比喻必须来自这个领域）
禁用词：{forbidden_words}（这些词绝对不能出现）

【身份态度——必须匹配】
身份：{status_level}
基调：{communication_tone}
开场偏好：{hook_preference}

【{name}的思考备忘录（基于此写稿）】
{thinking_memo}

【本期内容】
选题：{topic_title}
开场第一句：{hook_opening}
核心角度：{core_angle}
内容大纲：{content_outline}

【创作铁律——必须100%遵守】
1. 第一句就是hook_opening的内容，直接放，不要改太多
2. 用第一人称"我"讲述，全程像在聊天
3. 数字必须具体（"300万"不是"很多钱"，"2018年冬天"不是"那几年"）
4. 故事要有画面感——时间、地点、对话、细节都要有
5. 至少融入2句他的原话或原话变体（上面"他的原话"部分）
6. 论证结构按论证模板来组织
7. 结尾必须有互动引导（问一个有争议的问题，或预告下期）
8. 节奏要有快有慢，口语化，适合大声朗读
9. 总字数控制在{word_count}字左右（约{duration}秒）

【平台适配：抖音】
- 开头前3秒制造钩子
- 中间每30秒要有新的信息点或情绪高潮
- 结尾用问句引导评论

直接输出口播稿全文（纯文字，不要分镜格式，就是连续的说话内容）：
"""

# Step 3: De-AI（去AI味审核）— 参考更多原话样本
SCRIPT_DEAI_PROMPT = """你是一个"去AI味"审核官。你的任务是把下面这篇口播稿中所有AI感的表达替换掉，让它听起来100%是一个真实的人在说话。

【原始脚本】
{draft_script}

【这个人的声音指纹】
句式特征：{sentence_pattern}
修辞偏好：{rhetoric_preference}
论证结构：{argument_structure}
比喻领域：{metaphor_domain}
禁用词列表：{forbidden_words}
原话参考（用这些表达风格替换AI味句子）：{raw_quotes}

【这个人常用的表达（替换时优先用这些）】
{favorite_phrases}

【这个人的身份态度】
身份：{status_level}
基调：{communication_tone}
开场偏好：{hook_preference}

【你的审核清单——逐条检查】
1. 找出所有AI味表达并替换：
   - "值得注意的是" → 删掉或换成口语
   - "首先...其次...最后..." → 用更自然的过渡
   - "让我们..." → 他不会这么说
   - "不得不说" → 太书面
   - "说实话/坦白讲" → 如果频繁出现，删掉一些
   - 任何听起来像ChatGPT写的句子
2. 检查句式是否匹配声音指纹（句子长短、反问使用等）
3. 检查禁用词列表中的词是否出现，出现了必须替换
4. 检查态度匹配：
   - 如果是"行业大佬"身份 → 删除所有讨好观众的表达（"大家好""希望对大家有帮助"）
   - 如果是"草根创业者" → 不要用太权威的语气
5. 确保口语化，适合朗读（读出来不拗口）
6. 保持原稿的核心内容和结构不变，只改表达方式

直接输出修改后的完整稿件（纯文字，不要标注修改痕迹）：
"""


async def generate_script(
    profile_id: str,
    topic: Dict,
    duration: int = 90
) -> Dict:
    """
    3步脚本生成：Think → Write → DeAI
    使用观点素材库+表达种子（有则用，无则回退到旧方式）
    """
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError(f"IP档案不存在: {profile_id}")

    gemini = GeminiClient()
    word_count = int(duration * 3.2)

    # 读取增强字段（向后兼容）
    voice = profile.get("voice_fingerprint", {})
    identity = profile.get("identity_attitude", {})
    opinion_bank = profile.get("opinion_bank", [])
    expr_patterns = profile.get("expression_patterns", {})

    key_stories_text = "\n".join(f"- {s}" for s in profile.get("key_stories", []))
    unique_insights_text = "\n".join(f"- {i}" for i in profile.get("unique_insights", []))
    signature_phrases_text = "、".join(f'"{p}"' for p in profile.get("signature_phrases", [])[:6])
    content_outline_text = "\n".join(f"  {o}" for o in topic.get("content_outline", []))
    thinking_models_text = "、".join(profile.get("thinking_models", []))
    contrarian_views_text = "\n".join(f"- {v}" for v in profile.get("contrarian_views", []))
    forbidden_words_text = "、".join(voice.get("forbidden_words", []))

    # 构建原话引用（opinion_bank + voice_fingerprint.raw_quotes 合并）
    all_raw_quotes = []
    for op in opinion_bank:
        if op.get("raw_expression"):
            all_raw_quotes.append(f'- "{op["raw_expression"]}" （关于{op.get("topic", "?")}）')
    for q in voice.get("raw_quotes", []):
        all_raw_quotes.append(f'- "{q}"')
    # 加上favorite_phrases
    for fp in expr_patterns.get("favorite_phrases", []):
        if fp.get("phrase"):
            all_raw_quotes.append(f'- "{fp["phrase"]}" （场景: {fp.get("context", "通用")}）')
    raw_quotes_text = "\n".join(all_raw_quotes) if all_raw_quotes else "（暂无原话参考）"

    # 找相关观点
    relevant_ops = _find_relevant_opinions(opinion_bank, topic.get("title", ""))
    relevant_opinions_text = ""
    matched_opinion_seed = ""
    if relevant_ops:
        parts = []
        for op in relevant_ops:
            parts.append(f"话题「{op.get('topic', '')}」: {op.get('stance', '')} — {op.get('reasoning', '')}\n  原话: \"{op.get('raw_expression', '')}\"")
        relevant_opinions_text = "\n".join(parts)
        matched_opinion_seed = "\n".join(
            f"- {op.get('stance', '')}: {op.get('raw_expression', '')}"
            for op in relevant_ops[:3]
        )

    # 表达模式文本
    preferred_openings = "、".join(f'"{o}"' for o in expr_patterns.get("preferred_openings", [])[:4]) or "（暂无）"
    preferred_transitions = "、".join(f'"{t}"' for t in expr_patterns.get("preferred_transitions", [])[:4]) or "（暂无）"
    preferred_closings = "、".join(f'"{c}"' for c in expr_patterns.get("preferred_closings", [])[:4]) or "（暂无）"
    argument_templates = "\n".join(
        f"- {at.get('pattern', '')}: {at.get('example', '')}"
        for at in expr_patterns.get("argument_templates", [])[:3]
    ) or "（暂无）"

    # 常用表达文本（DeAI用）
    favorite_phrases_text = "、".join(
        f'"{fp.get("phrase", "")}"' for fp in expr_patterns.get("favorite_phrases", [])
    ) or "（暂无）"

    # ========== Step 1: Think ==========
    think_prompt = SCRIPT_THINK_PROMPT.format(
        name=profile["name"],
        industry=profile["industry"],
        role=profile.get("role", "创始人"),
        background_summary=profile.get("background_summary", ""),
        thinking_models=thinking_models_text or "（暂无）",
        decision_framework=profile.get("decision_framework", "（暂无）"),
        contrarian_views=contrarian_views_text or "（暂无）",
        relevant_opinions=relevant_opinions_text or "（暂无观点记录，请根据人物背景自行思考）",
        topic_title=topic.get("title", ""),
        core_angle=topic.get("core_angle", ""),
    )

    try:
        thinking_memo = await gemini._call_api(think_prompt)
        thinking_memo = thinking_memo.strip()
        logger.info(f"Step1 Think完成: {len(thinking_memo)}字")
    except Exception as e:
        logger.warning(f"Step1 Think失败，跳过: {e}")
        thinking_memo = ""

    # ========== Step 2: Write ==========
    write_prompt = SCRIPT_WRITE_PROMPT.format(
        name=profile["name"],
        industry=profile["industry"],
        role=profile.get("role", "创始人"),
        ip_positioning=profile.get("ip_positioning", ""),
        background_summary=profile.get("background_summary", ""),
        key_stories=key_stories_text,
        unique_insights=unique_insights_text,
        preferred_openings=preferred_openings,
        preferred_transitions=preferred_transitions,
        preferred_closings=preferred_closings,
        all_raw_quotes=raw_quotes_text,
        argument_templates=argument_templates,
        matched_opinion_seed=matched_opinion_seed or "（暂无相关观点，请根据思考备忘录写）",
        speaking_style=profile.get("speaking_style", ""),
        signature_phrases=signature_phrases_text,
        values=profile.get("values", ""),
        sentence_pattern=voice.get("sentence_pattern", "（暂无）"),
        rhetoric_preference=voice.get("rhetoric_preference", "（暂无）"),
        argument_structure=voice.get("argument_structure", "（暂无）"),
        metaphor_domain=voice.get("metaphor_domain", "（暂无）"),
        forbidden_words=forbidden_words_text or "（暂无）",
        status_level=identity.get("status_level", "（暂无）"),
        communication_tone=identity.get("communication_tone", "（暂无）"),
        hook_preference=identity.get("hook_preference", "（暂无）"),
        thinking_memo=thinking_memo or "（思考步骤跳过）",
        topic_title=topic.get("title", ""),
        hook_opening=topic.get("hook_opening", ""),
        core_angle=topic.get("core_angle", ""),
        content_outline=content_outline_text,
        word_count=word_count,
        duration=duration
    )

    try:
        draft_script = await gemini._call_api(write_prompt)
        draft_script = draft_script.strip()
        logger.info(f"Step2 Write完成: {len(draft_script)}字")
    except Exception as e:
        logger.error(f"Step2 Write失败: {e}")
        raise

    # ========== Step 3: DeAI ==========
    try:
        deai_prompt = SCRIPT_DEAI_PROMPT.format(
            draft_script=draft_script,
            sentence_pattern=voice.get("sentence_pattern", "（暂无）"),
            rhetoric_preference=voice.get("rhetoric_preference", "（暂无）"),
            argument_structure=voice.get("argument_structure", "（暂无）"),
            metaphor_domain=voice.get("metaphor_domain", "（暂无）"),
            forbidden_words=forbidden_words_text or "（暂无）",
            raw_quotes=raw_quotes_text,
            favorite_phrases=favorite_phrases_text,
            status_level=identity.get("status_level", "（暂无）"),
            communication_tone=identity.get("communication_tone", "（暂无）"),
            hook_preference=identity.get("hook_preference", "（暂无）"),
        )
        final_script = await gemini._call_api(deai_prompt)
        final_script = final_script.strip()
        logger.info(f"Step3 DeAI完成: {len(final_script)}字")
    except Exception as e:
        logger.warning(f"Step3 DeAI失败，使用Step2结果: {e}")
        final_script = draft_script

    # 按段落拆分 → 对象数组（带paragraph_id）
    raw_paragraphs = [p.strip() for p in final_script.split("\n\n") if p.strip()]
    if len(raw_paragraphs) < 3:
        raw_paragraphs = [p.strip() for p in final_script.split("\n") if p.strip()]

    paragraphs = []
    for i, text in enumerate(raw_paragraphs):
        paragraphs.append({
            "index": i,
            "text": text,
            "paragraph_id": f"para_{uuid.uuid4().hex[:8]}"
        })

    # 更新opinion_bank中使用过的观点的used_count
    if relevant_ops and opinion_bank:
        used_ids = {op.get("opinion_id") for op in relevant_ops}
        for op in opinion_bank:
            if op.get("opinion_id") in used_ids:
                op["used_count"] = op.get("used_count", 0) + 1
        profile["opinion_bank"] = opinion_bank
        await save_profile(profile)

    result = {
        "profile_id": profile_id,
        "topic_title": topic.get("title", ""),
        "duration": duration,
        "word_count": len(final_script.replace(" ", "").replace("\n", "")),
        "full_script": final_script,
        "paragraphs": paragraphs,
        "thinking_memo": thinking_memo,
        "generated_at": datetime.now().isoformat()
    }
    logger.info(f"脚本3步生成完成: {profile['name']} - {topic.get('title', '')}, {result['word_count']}字")
    return result


# ==================== 段落反馈 ====================

FEEDBACK_ANALYSIS_PROMPT = """你是一个语言风格分析师。用户标记了以下段落为"不像我"，请分析这些段落中有哪些AI味的表达或不自然的措辞。

【被拒绝的段落】
{rejected_paragraphs}

【用户备注】
{user_notes}

【当前禁用词列表】
{current_forbidden}

请输出JSON格式（不要其他文字）：
{{
  "new_forbidden_words": ["从被拒段落中提取的新禁用词/表达，3-8个"],
  "style_issues": ["发现的风格问题描述，如'句子太长太书面'、'用了太多排比'"],
  "suggestions": "一句话建议：下次生成时应该注意什么"
}}
"""

EDIT_ANALYSIS_PROMPT = """你是一位表达风格分析师。用户直接编辑了AI生成的脚本段落，请对比编辑前后的差异，提炼出用户的表达偏好。

【编辑记录】
{edit_records}

【选题】
{topic_title}

请分析编辑前后的差异，输出JSON格式（不要其他文字）：
{{
  "new_forbidden_words": ["被用户删除/替换掉的AI味表达，如'值得注意的是'"],
  "new_preferred_expressions": [
    {{"phrase": "用户倾向使用的表达", "context": "使用场景（如opening/transition/closing/argument/general）"}}
  ],
  "new_argument_templates": [
    {{"pattern": "用户偏好的论证结构", "example": "从编辑后文本摘取的例子"}}
  ],
  "new_opinion_entries": [
    {{"topic": "如果编辑透露了新观点的话题", "stance": "立场", "raw_expression": "用户写的原话"}}
  ]
}}

注意：
- 只提取有明确证据的模式，不要过度推测
- new_opinion_entries只在用户编辑中明显表达了新观点时才填写，否则留空数组
"""


async def update_profile_from_feedback(
    profile_id: str,
    rejected_paragraphs: List[str],
    edits: List[Dict] = None,
    notes: str = ""
) -> Dict:
    """
    根据用户的"不像我"反馈 + 直接编辑，更新声音指纹和表达模式
    """
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError(f"IP档案不存在: {profile_id}")

    voice = profile.get("voice_fingerprint", {})
    current_forbidden = voice.get("forbidden_words", [])
    expr_patterns = profile.get("expression_patterns", {})
    opinion_bank = profile.get("opinion_bank", [])
    edit_history = profile.get("edit_history", [])

    gemini = GeminiClient()
    new_words = []
    style_issues = []
    suggestions = ""

    # === Part 1: 处理rejected段落（原有逻辑） ===
    if rejected_paragraphs:
        prompt = FEEDBACK_ANALYSIS_PROMPT.format(
            rejected_paragraphs="\n---\n".join(rejected_paragraphs),
            user_notes=notes or "（无备注）",
            current_forbidden="、".join(current_forbidden) or "（暂无）"
        )

        try:
            result = await gemini._call_api(prompt)
            analysis = _parse_json(result)
            new_words = analysis.get("new_forbidden_words", [])
            style_issues = analysis.get("style_issues", [])
            suggestions = analysis.get("suggestions", "")
        except Exception as e:
            logger.warning(f"rejected段落分析失败: {e}")

    # === Part 2: 处理编辑（新增逻辑） ===
    edit_analysis_result = {}
    if edits and len(edits) > 0:
        # 清理编辑内容中的用户输入
        for edit in edits:
            edit["original_text"] = _sanitize_input(edit.get("original_text", ""), max_length=2000)
            edit["edited_text"] = _sanitize_input(edit.get("edited_text", ""), max_length=2000)
            edit["topic_title"] = _sanitize_input(edit.get("topic_title", ""), max_length=200)

        # 记录编辑历史
        for edit in edits:
            edit_history.append({
                "edit_id": f"edit_{uuid.uuid4().hex[:6]}",
                "original_text": edit.get("original_text", ""),
                "edited_text": edit.get("edited_text", ""),
                "topic_title": edit.get("topic_title", ""),
                "timestamp": datetime.now().isoformat()
            })

        # 编辑分析
        edit_records_text = ""
        for i, edit in enumerate(edits):
            edit_records_text += f"\n--- 编辑 {i+1} ---\n"
            edit_records_text += f"原文: {edit.get('original_text', '')}\n"
            edit_records_text += f"改为: {edit.get('edited_text', '')}\n"

        topic_title = edits[0].get("topic_title", "") if edits else ""

        try:
            edit_prompt = EDIT_ANALYSIS_PROMPT.format(
                edit_records=edit_records_text,
                topic_title=topic_title
            )
            edit_result = await gemini._call_api(edit_prompt)
            edit_analysis_result = _parse_json(edit_result)

            # 合并 forbidden_words
            edit_forbidden = edit_analysis_result.get("new_forbidden_words", [])
            new_words = list(set(new_words + edit_forbidden))

            # 合并 expression_patterns.favorite_phrases
            new_exprs = edit_analysis_result.get("new_preferred_expressions", [])
            existing_phrases = expr_patterns.get("favorite_phrases", [])
            for expr in new_exprs:
                if expr.get("phrase"):
                    existing_phrases.append({
                        "phrase": expr["phrase"],
                        "context": expr.get("context", "general"),
                        "source": "user_edit"
                    })
            expr_patterns["favorite_phrases"] = existing_phrases

            # 合并 argument_templates
            new_templates = edit_analysis_result.get("new_argument_templates", [])
            existing_templates = expr_patterns.get("argument_templates", [])
            for tmpl in new_templates:
                if tmpl.get("pattern"):
                    existing_templates.append(tmpl)
            expr_patterns["argument_templates"] = existing_templates

            # 合并 opinion_bank
            new_opinions = edit_analysis_result.get("new_opinion_entries", [])
            for op in new_opinions:
                if op.get("topic") and op.get("raw_expression"):
                    opinion_bank.append({
                        "opinion_id": f"op_{uuid.uuid4().hex[:6]}",
                        "topic": op["topic"],
                        "stance": op.get("stance", ""),
                        "reasoning": "",
                        "raw_expression": op["raw_expression"],
                        "emotion": "confident",
                        "confidence": 0.8,
                        "topic_source": "user_edit",
                        "created_at": datetime.now().isoformat(),
                        "used_count": 0
                    })

            logger.info(f"编辑分析完成: 新增{len(edit_forbidden)}个禁用词, {len(new_exprs)}个偏好表达, {len(new_opinions)}条观点")
        except Exception as e:
            logger.warning(f"编辑分析失败: {e}")

    # === 更新profile ===
    updated_forbidden = list(set(current_forbidden + new_words))

    if "voice_fingerprint" not in profile:
        profile["voice_fingerprint"] = {}
    profile["voice_fingerprint"]["forbidden_words"] = updated_forbidden
    profile["expression_patterns"] = expr_patterns
    profile["opinion_bank"] = opinion_bank
    profile["edit_history"] = edit_history

    await save_profile(profile)
    logger.info(f"反馈更新完成: {profile['name']}, 新增{len(new_words)}个禁用词")

    return {
        "new_forbidden_words": new_words,
        "style_issues": style_issues,
        "suggestions": suggestions,
        "total_forbidden": len(updated_forbidden),
        "edits_processed": len(edits) if edits else 0,
        "new_patterns": len(edit_analysis_result.get("new_preferred_expressions", []))
    }


# ==================== 工具函数 ====================

def _sanitize_input(text: str, max_length: int = 2000) -> str:
    """截断+清理控制字符，防止prompt注入"""
    if not text:
        return ""
    # 截断
    text = text[:max_length]
    # 清理控制字符（保留换行和制表符）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()


def _parse_json(text: str):
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    # 检测 { 和 [ 哪个先出现，先出现的优先尝试
    obj_pos = text.find('{')
    arr_pos = text.find('[')
    if obj_pos < 0:
        obj_pos = float('inf')
    if arr_pos < 0:
        arr_pos = float('inf')
    if arr_pos < obj_pos:
        pairs = [('[', ']'), ('{', '}')]
    else:
        pairs = [('{', '}'), ('[', ']')]
    for start_char, end_char in pairs:
        start = text.find(start_char)
        end = text.rfind(end_char) + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                continue
    return json.loads(text)
