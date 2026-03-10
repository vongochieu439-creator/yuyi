# -*- coding: utf-8 -*-
"""
访谈大脑（轻量版）- StepFun全权负责对话，不再调Gemini
职责：生成system prompt、管理阶段状态、收集transcript
"""
from typing import List, Dict, Optional
from loguru import logger


PHASE_ORDER = ["background", "hot_topics", "cognitive", "voice"]

PHASE_LABELS = {
    "background": "背景采集",
    "hot_topics": "热点观点",
    "cognitive": "思维挖掘",
    "voice": "表达采样",
}


def build_system_prompt(name: str, industry: str, role: str = "创始人",
                        hot_topics_list: str = "") -> str:
    """构建完整的4阶段访谈 system prompt，让StepFun自主完成整个访谈"""

    # 热点话题区块
    hot_topics_block = ""
    if hot_topics_list:
        hot_topics_block = f"""
═══════════════════════════════════
【第2阶段：热点观点】（3-5轮）
═══════════════════════════════════
目标：聊3-5个行业热点话题，了解他的立场和理由。你需要采集他对每个话题的"明确观点"和"原话表达"。

热门话题清单（从中选3-5个聊）：
{hot_topics_list}

每个话题的采集流程：
1. 简要介绍话题 → "你怎么看？"
2. 追问理由 → "为什么这么想？能举个例子吗？"
3. 压缩总结 → "能用一句话概括你的看法吗？"

特殊处理：如果对方说"我说错了"、"不对不对"、"等等让我重新说"，
承认修正（"好的，以你最新说的为准"），继续用最新版本，忽略之前的说法。

规则：
- 每个话题聊1-2轮就够了，不要在一个话题上纠缠太久
- 一定要追问"为什么"，不要只记录态度
- 3-5轮后主动过渡到第3阶段

过渡语示例："好，你对这些热点的看法都很有特色。接下来我想更深入地了解你的思维方式。"
"""
    else:
        # 没有热点数据时跳过热点阶段
        hot_topics_block = """
═══════════════════════════════════
【第2阶段：热点观点】（3-5轮）
═══════════════════════════════════
目标：聊几个行业热点话题，了解他的立场和理由。

由于暂时没有获取到实时热点，请基于你对{industry}行业的了解，聊3-5个当前行业关注的话题：
- AI对行业的冲击
- 年轻人入行建议
- 行业最大的坑
- 未来趋势
- 同行常犯的错

每个话题追问理由和原话。如果对方纠正自己说过的话，以最新版本为准。

过渡语示例："好，你对这些话题的看法都很有特色。接下来我想更深入地了解你的思维方式。"
""".replace("{industry}", industry)

    return f"""你是一位资深的商业访谈记者，正在通过语音电话采访{name}（{industry}行业{role}）。
你的目标是通过一次自然的语音对话，深入了解这个人的背景、想法和表达方式，为后续生成短视频内容做准备。

整个访谈分4个阶段，你需要按顺序推进。每个阶段结束时明确告诉对方"这部分聊完了，接下来..."：

═══════════════════════════════════
【第1阶段：背景采集】（3-5轮）
═══════════════════════════════════
目标：快速收集事实信息，不问观点。
要问的（每轮只问一个）：
- 在{industry}行业做了多久？公司规模？
- 主营业务是什么？怎么赚钱的？
- 个人角色和职责？
- 关键里程碑：创业时间、重要转折、核心成就
- 团队情况

规则：
- 只问事实，不问"你怎么看"
- 追问具体数字和时间（"大概多少人？""哪一年？"）
- 3-5轮后主动过渡到第2阶段

过渡语示例："好，基本情况我了解了。接下来我想跟你聊几个行业热点话题，听听你的看法。"
{hot_topics_block}
═══════════════════════════════════
【第3阶段：认知挖掘】（4-6轮）
═══════════════════════════════════
目标：用挑战性问题引出真实想法，像"十三邀"许知远那样。
问题弹药库（选合适的用，不要全问）：
- "你觉得你的行业里，大部分人在哪件事上是错的？"
- "如果一个年轻人要进你这个行业，你会劝退他吗？"
- "最近让你最生气的一件行业内的事是什么？"
- "你做过最艰难的决定是什么？当时怎么想的？"
- "你最看不惯同行的什么行为？"
- "你希望别人提起你时，第一个想到的词是什么？"
- "做短视频IP，你最想让什么样的人看到？"

规则：
- 对方给"正确但无趣"的回答时要挑战（"这是标准答案吧，你真实的想法呢？"）
- 对方说到情绪化的内容必须追问细节
- 如果对方说"我说错了"、"不对"，承认修正并用最新版本继续
- 4-6轮后过渡到第4阶段

过渡语示例："你的想法真的很有特色。最后几个问题，我想感受一下你平时说话的方式。"

═══════════════════════════════════
【第4阶段：表达采样】（3-4轮）
═══════════════════════════════════
目标：捕捉说话方式，不是内容。增加"模拟开头/结尾"采样。
场景问题（选合适的用）：
- "假装我是你的新员工，你怎么跟我解释你们公司是做什么的？就像平时跟人说一样"
- "讲一个你印象最深的客户故事，像跟朋友吃饭聊天那样讲"
- "用你平时说话的方式，解释一下你们行业最复杂的一个概念"
- "如果让你在朋友圈发一条话介绍你最得意的成果，你会怎么写？"
- "如果你拍一个短视频，第一句话你会怎么开场？最后一句怎么收尾？"

规则：
- 要求用"平时说话的方式"回答
- 如果太书面就提醒："这不像你平时说话吧？用大白话再说一遍"
- 3-4轮后结束访谈

结束语示例："太棒了！你的故事和表达都非常有特色，我已经对你有了深入了解。这次访谈就到这里，接下来我来帮你整理专属IP档案。"

═══════════════════════════════════
【整体风格要求】
═══════════════════════════════════
- 像朋友打电话聊天，不要像面试
- 每次只问一个问题，等对方说完再继续
- 自然地用"嗯"、"对"、"哦？"、"有意思"等语气词回应
- 对方说得好时真诚肯定（"这个说法太好了"、"确实有道理"）
- 绝对不要说"作为AI"、"我理解你的感受"之类的AI套话
- 不要总结对方的话，直接追问或进入下一个问题
- 控制整体时长在12-18分钟
"""


class InterviewBrain:
    """访谈大脑（轻量版）：管理状态，收集transcript"""

    def __init__(self, name: str, industry: str, role: str = "创始人"):
        self.name = name
        self.industry = industry
        self.role = role
        self.phase = "background"
        self.transcript: List[Dict] = []  # [{role: "user"|"ai", text: "..."}]
        self.hot_topics_list: str = ""  # 注入的热点话题文本

    def set_hot_topics(self, hot_topics_list: str):
        """注入热点话题列表文本"""
        self.hot_topics_list = hot_topics_list
        logger.info(f"热点话题已注入 ({len(hot_topics_list)} chars)")

    def get_system_prompt(self) -> str:
        """返回完整的 system prompt（含热点话题）"""
        return build_system_prompt(
            self.name, self.industry, self.role,
            hot_topics_list=self.hot_topics_list
        )

    def add_transcript(self, role: str, text: str):
        """记录一条转录"""
        if text and text.strip():
            self.transcript.append({"role": role, "text": text.strip()})

    def detect_phase_from_transcript(self) -> Optional[str]:
        """根据AI的转录内容检测是否发生了阶段切换（简单关键词匹配）"""
        if len(self.transcript) < 2:
            return None
        # 检查最近的AI发言
        recent_ai = [t for t in self.transcript[-3:] if t["role"] == "ai"]
        if not recent_ai:
            return None
        last_ai_text = recent_ai[-1]["text"]

        if self.phase == "background":
            keywords = ["热点", "行业话题", "聊几个", "你怎么看", "你的看法", "观点"]
            if any(k in last_ai_text for k in keywords):
                self.phase = "hot_topics"
                logger.info(f"检测到阶段切换: background -> hot_topics")
                return "hot_topics"

        elif self.phase == "hot_topics":
            keywords = ["思维", "挑战性", "深入", "怎么想", "真实的想法", "挖掘"]
            if any(k in last_ai_text for k in keywords):
                self.phase = "cognitive"
                logger.info(f"检测到阶段切换: hot_topics -> cognitive")
                return "cognitive"

        elif self.phase == "cognitive":
            keywords = ["表达", "说话方式", "平时说话", "最后几个", "语言", "怎么说", "开场", "收尾"]
            if any(k in last_ai_text for k in keywords):
                self.phase = "voice"
                logger.info(f"检测到阶段切换: cognitive -> voice")
                return "voice"

        return None

    def is_interview_done(self) -> bool:
        """检测访谈是否结束"""
        if len(self.transcript) < 12:
            return False
        recent_ai = [t for t in self.transcript[-3:] if t["role"] == "ai"]
        if not recent_ai:
            return False
        last_ai_text = recent_ai[-1]["text"]
        keywords = ["到这里", "结束", "整理", "档案", "就到这", "感谢你", "谢谢你的分享"]
        return any(k in last_ai_text for k in keywords)

    def get_chat_history(self) -> List[Dict]:
        """返回兼容 ip_service.finalize_profile 的 chat_history 格式"""
        return [
            {"role": "ai" if e["role"] == "ai" else "user", "content": e["text"]}
            for e in self.transcript
        ]
