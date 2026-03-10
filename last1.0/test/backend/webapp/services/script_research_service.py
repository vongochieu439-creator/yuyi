# -*- coding: utf-8 -*-
"""
数据驱动脚本调研服务 - 三方向并行调研编排

方向A: 同行业头部 → 搜同品类爆款 → 拆解脚本 → 模仿生成
方向B: 评论区需求 → 抓评论聚类高频痛点 → 基于真实需求出脚本
方向C: 跨行业创意迁移 → 搜其他行业创意博主 → 提取创意模式 → 迁移到目标行业
"""
import asyncio
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Callable, Awaitable
from loguru import logger

from .tikhub_client import TikHubClient
from .video_analyzer import VideoAnalyzer, VideoAnalysis
from .gemini_client import GeminiClient


@dataclass
class IndustryResearch:
    """方向A: 同行业调研结果"""
    search_keyword: str = ""
    videos: List[Dict] = field(default_factory=list)        # 搜索结果摘要
    analyses: List[Dict] = field(default_factory=list)      # VideoAnalysis的dict形式
    success_patterns: str = ""                               # Gemini提取的成功模式
    structured_dna: Dict = field(default_factory=dict)       # 结构化DNA提取结果

    def to_dict(self):
        return asdict(self)


@dataclass
class CommentResearch:
    """方向B: 评论区调研结果"""
    total_comments: int = 0
    all_comments: List[Dict] = field(default_factory=list)  # 所有评论合集
    cluster_analysis: str = ""                               # Gemini聚类分析
    top_pain_points: List[str] = field(default_factory=list) # 高频痛点TOP5
    best_angles: List[str] = field(default_factory=list)     # 最佳选题角度
    # 争议挖掘 + 情绪冲突 新字段
    controversy_topic: str = ""                              # 最具争议性的话题
    emotional_triggers: List[str] = field(default_factory=list)  # 情绪触发点
    real_comments_for_hook: List[str] = field(default_factory=list)  # 可直接做钩子的原始评论

    def to_dict(self):
        return asdict(self)


@dataclass
class CreativeResearch:
    """方向C: 跨行业创意调研结果"""
    search_keyword: str = ""
    videos: List[Dict] = field(default_factory=list)
    analyses: List[Dict] = field(default_factory=list)
    creative_patterns: str = ""                              # 创意机制提取
    migration_ideas: str = ""                                # 迁移方案
    creator_info: List[Dict] = field(default_factory=list)   # 抽取的创意博主信息

    def to_dict(self):
        return asdict(self)


@dataclass
class ResearchResult:
    """三方向调研总结果"""
    industry: IndustryResearch = field(default_factory=IndustryResearch)
    comments: CommentResearch = field(default_factory=CommentResearch)
    creative: CreativeResearch = field(default_factory=CreativeResearch)

    def to_dict(self):
        return {
            "industry": self.industry.to_dict(),
            "comments": self.comments.to_dict(),
            "creative": self.creative.to_dict(),
        }


class ScriptResearchService:
    """三方向并行调研服务"""

    def __init__(self):
        self.tikhub = TikHubClient()
        self.analyzer = VideoAnalyzer()
        self.gemini = GeminiClient()

    async def research(
        self,
        product_name: str,
        industry: str,
        product_detail: str = "",
        on_progress: Optional[Callable[[str, float], Awaitable[None]]] = None,
    ) -> ResearchResult:
        """
        三方向并行调研

        Args:
            product_name: 产品名称
            industry: 行业
            product_detail: 产品详情
            on_progress: 进度回调 (message, progress_0_to_1)

        Returns:
            ResearchResult 三方向完整调研结果
        """
        result = ResearchResult()

        async def _progress(msg: str, pct: float):
            if on_progress:
                await on_progress(msg, pct)
            logger.info(f"[调研进度 {pct:.0%}] {msg}")

        await _progress("开始三方向数据调研...", 0.0)

        # 方向A和方向C并行搜索，方向B复用方向A数据
        a_task = self._research_industry(product_name, industry, product_detail, _progress)
        c_task = self._research_creative(product_name, industry, product_detail, _progress)

        a_result, c_result = await asyncio.gather(a_task, c_task)
        result.industry = a_result
        result.creative = c_result

        # 方向B: 复用方向A分析过的视频的评论数据
        await _progress("评论区聚类分析...", 0.75)
        b_result = await self._research_comments(
            product_name, industry, product_detail,
            a_result.analyses,  # 复用方向A的视频分析
            _progress,
        )
        result.comments = b_result

        await _progress("三方向调研完成!", 1.0)
        return result

    async def _research_industry(
        self,
        product_name: str,
        industry: str,
        product_detail: str,
        progress_fn,
    ) -> IndustryResearch:
        """
        方向A: 同行业头部视频分析

        1. TikHub搜"{品类} 推荐|测评" sort_by=likes → TOP3视频
        2. 每个视频调 VideoAnalyzer.analyze_video()
        3. Gemini综合: 提取成功模式
        """
        res = IndustryResearch()

        # Step 1: 三维搜索: 竞品直接 + 负面反向 + 信任种草
        keywords = [
            f"{product_name} 推荐 测评",
            f"{industry or product_name} 避坑 踩雷",
            f"{industry or product_name} 自用 真实",
        ]
        res.search_keyword = " | ".join(keywords)
        await progress_fn(f"三维搜索同行业爆款: {res.search_keyword}", 0.05)

        # Parallel search
        search_tasks = [self.tikhub.search_videos(kw, count=5, sort_type=1) for kw in keywords]
        search_results = await asyncio.gather(*search_tasks)

        # Merge and deduplicate by video_id, take top by engagement
        all_videos = []
        seen_ids = set()
        for videos in search_results:
            for v in videos:
                vid = v.get("video_id", "")
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    # Calculate engagement ratio
                    digg = v.get("digg_count", 0)
                    comment = v.get("comment_count", 0)
                    v["engagement_ratio"] = comment / max(digg, 1)
                    all_videos.append(v)

        if not all_videos:
            logger.warning(f"方向A: 未搜到视频 keywords={keywords}")
            return res

        # Sort by digg_count but prefer high engagement ratio
        all_videos.sort(key=lambda v: v.get("digg_count", 0) * (1 + v.get("engagement_ratio", 0)), reverse=True)
        top_videos = all_videos[:2]
        res.videos = top_videos

        await progress_fn(f"找到{len(all_videos)}个视频，取TOP{len(top_videos)}个同行业爆款", 0.10)

        # Step 2: 并行深度分析（使用batch方法）
        vids = [v["video_id"] for v in top_videos]

        async def _on_a_progress(msg: str):
            await progress_fn(f"[A] {msg}", 0.15)

        analyses = await self.analyzer.analyze_videos_batch(vids, _on_a_progress, max_concurrent=2)

        res.analyses = [a.to_dict() for a in analyses]

        # Step 3: Gemini综合提取成功模式
        await progress_fn("提取同行业成功模式...", 0.30)

        if analyses:
            pattern_prompt = self._build_pattern_extraction_prompt(analyses, product_name, industry)
            try:
                raw = await self.gemini.generate(pattern_prompt, max_tokens=4096)
                res.success_patterns = raw
                # Try to parse structured DNA
                res.structured_dna = self._parse_json_result(raw)
            except Exception as e:
                logger.error(f"方向A成功模式提取失败: {e}")

        return res

    async def _research_comments(
        self,
        product_name: str,
        industry: str,
        product_detail: str,
        existing_analyses: List[Dict],
        progress_fn,
    ) -> CommentResearch:
        """
        方向B: 评论区需求挖掘

        1. 复用方向A视频的评论数据
        2. 合并所有评论 → Gemini聚类分析
        3. 输出: 高频痛点TOP5 + 最佳选题角度
        """
        res = CommentResearch()

        # 收集所有评论
        all_comments = []
        for analysis in existing_analyses:
            comments = analysis.get("comments", [])
            all_comments.extend(comments)

        # 如果复用数据不够，额外搜索一批
        if len(all_comments) < 30:
            await progress_fn("补充搜索评论数据...", 0.78)
            # 用产品名搜索
            extra_videos = await self.tikhub.search_videos(
                f"{product_name} 怎么样", count=5, sort_type=1
            )
            for v in extra_videos[:3]:
                vid = v.get("video_id", "")
                if vid:
                    comments = await self.tikhub.get_video_comments(vid, count=50)
                    all_comments.extend(comments)

        res.total_comments = len(all_comments)
        res.all_comments = all_comments[:200]  # 最多保留200条

        if not all_comments:
            logger.warning("方向B: 无评论数据")
            return res

        # Gemini聚类分析
        await progress_fn(f"分析{len(all_comments)}条评论...", 0.82)

        comments_text = ""
        for i, c in enumerate(all_comments[:100], 1):  # 取前100条送给Gemini
            comments_text += f"{i}. [{c.get('digg_count', 0)}赞] {c.get('text', '')}\n"

        cluster_prompt = f"""你是消费者心理洞察专家+爆款内容策略师。以下是关于"{product_name}"({industry})相关视频的{len(all_comments)}条评论（按点赞排序）:

{comments_text}

请进行四层深度分析:

## 第1层：显性需求（人们说了什么）
- 高频痛点TOP5（标注出现频次估计）
- 最常被提到的购买决策因素

## 第2层：情绪暗流（人们怎么说的）
- 情绪分布: 正面/中立/负面/讽刺 各占比
- 最强情绪触发点TOP3（哪些话题让人反应最激烈？）
- 有没有"智商税""割韭菜""交了学费"等不信任信号？

## 第3层：争议极化（人们在吵什么）
- 找出评论区正反对立最激烈的1个话题
- 正方观点摘要 + 反方观点摘要
- 为什么这个话题最具传播力？（争议=注意力=互动=爆款）

## 第4层：钩子素材（可直接使用的评论原文）
- 挑出3条最适合做视频开头钩子的原始评论（要有情绪张力）
- 格式: "看到一条评论说'XXX'，今天我..."

## 最终输出：最佳脚本策略
- 推荐1个最具爆款潜力的脚本策略（基于争议点，不是痛点）
- 说明为什么这个角度比单纯回答痛点更有传播力
- 给出脚本叙事结构建议（审判式/翻盘式/挑战式）

请给出具体、可直接用于脚本创作的洞察。"""

        try:
            res.cluster_analysis = await self.gemini.generate(cluster_prompt, max_tokens=4096)
        except Exception as e:
            logger.error(f"方向B评论聚类失败: {e}")

        # Extract structured insights from the analysis
        if res.cluster_analysis:
            # Try to find controversy topic
            lines = res.cluster_analysis.split('\n')
            for i, line in enumerate(lines):
                if '争议' in line or '极化' in line or '对立' in line:
                    # Next few lines likely contain the controversy topic
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if lines[j].strip() and not lines[j].startswith('#'):
                            res.controversy_topic = lines[j].strip()[:200]
                            break
                    break

            # Extract hook comments (lines that look like quoted comments)
            import re
            hook_pattern = re.compile(r'["\u201c\u300c](.{10,80})["\u201d\u300d]')
            for match in hook_pattern.finditer(res.cluster_analysis):
                if len(res.real_comments_for_hook) < 3:
                    res.real_comments_for_hook.append(match.group(1))

        return res

    async def _research_creative(
        self,
        product_name: str,
        industry: str,
        product_detail: str,
        progress_fn,
    ) -> CreativeResearch:
        """
        方向C: 创意博主池 → 机制拆解 → 产品属性匹配 → 结构同构迁移

        1. 从创意博主池随机抽取2个不同类型的博主
        2. TikHub搜博主名字获取其爆款视频
        3. VideoAnalyzer深度分析（结构化输出）
        4. Gemini: 创意机制提取 + 产品属性分析 + 结构同构匹配
        """
        from .creative_pool import pick_creators

        res = CreativeResearch()

        # Step 1: 从创意博主池抽取2个不同类型
        creators = pick_creators(n=2)
        res.creator_info = [
            {"name": c["name"], "category": c["category"],
             "mechanism": c["mechanism"], "signature_device": c["signature_device"]}
            for c in creators
        ]
        creator_names = [c["name"] for c in creators]
        search_keywords = [c["search_keyword"] for c in creators]
        res.search_keyword = " | ".join(search_keywords)

        await progress_fn(f"抽取创意博主: {', '.join(creator_names)}", 0.40)

        # Step 2: 并行搜索每个博主的爆款视频
        search_tasks = [
            self.tikhub.search_videos(kw, count=5, sort_type=1)
            for kw in search_keywords
        ]
        search_results = await asyncio.gather(*search_tasks)

        # 每个博主取最佳1个视频
        top_videos = []
        for videos in search_results:
            valid = [v for v in videos if v.get("video_id")]
            if valid:
                top_videos.append(valid[0])

        if not top_videos:
            logger.warning(f"方向C: 博主视频搜索全部为空: {search_keywords}")
            return res

        res.videos = top_videos
        await progress_fn(f"找到{len(top_videos)}个创意博主爆款视频", 0.45)

        # Step 3: 并行深度分析
        vids = [v["video_id"] for v in top_videos]

        async def _on_c_progress(msg: str):
            await progress_fn(f"[C] {msg}", 0.50)

        analyses = await self.analyzer.analyze_videos_batch(vids, _on_c_progress, max_concurrent=2)
        res.analyses = [a.to_dict() for a in analyses]

        # Step 4: 创意机制提取 + 产品属性匹配 + 结构同构
        await progress_fn("拆解创意机制 + 匹配产品属性...", 0.65)

        if analyses:
            migration_prompt = self._build_creative_migration_prompt(
                analyses, product_name, industry, product_detail, creators
            )
            try:
                result = await self.gemini.generate(migration_prompt, max_tokens=4096)
                res.creative_patterns = result
                res.migration_ideas = result
            except Exception as e:
                logger.error(f"方向C创意迁移分析失败: {e}")

        return res

    def _build_pattern_extraction_prompt(
        self, analyses: List, product_name: str, industry: str
    ) -> str:
        """构建结构化DNA提取Prompt"""
        videos_info = ""
        for i, a in enumerate(analyses, 1):
            title = a.title[:50] if hasattr(a, 'title') else str(a.get('title', ''))[:50]
            asr = (a.asr_text if hasattr(a, 'asr_text') else a.get('asr_text', ''))[:300]
            deep = (a.deep_analysis if hasattr(a, 'deep_analysis') else a.get('deep_analysis', ''))[:500]
            play = a.play_count if hasattr(a, 'play_count') else a.get('play_count', 0)
            digg = a.digg_count if hasattr(a, 'digg_count') else a.get('digg_count', 0)
            structured = a.structured_analysis if hasattr(a, 'structured_analysis') else a.get('structured_analysis', {})

            videos_info += f"""
---
### 视频{i}: {title}
- 播放量: {play}, 点赞: {digg}
- 口播原文(节选): {asr}...
- 深度拆解: {deep}...
"""
            if structured:
                import json
                videos_info += f"- 结构化分析: {json.dumps(structured, ensure_ascii=False)[:500]}\n"

        return f"""你是抖音爆款内容DNA分析师。以下是"{industry}"行业TOP爆款视频的深度拆解:
{videos_info}

请提取可复用的结构DNA，直接输出JSON，不要其他文字:
{{
  "proven_structures": [
    {{
      "name": "结构模式名称",
      "beat_sequence": ["节拍1: 功能描述", "节拍2: 功能描述"],
      "frequency": "在几个视频中出现"
    }}
  ],
  "hook_arsenal": [
    {{
      "type": "钩子类型",
      "example": "原文示例",
      "mechanism": "留人原理",
      "effectiveness": "高/中/低"
    }}
  ],
  "selling_insertion_playbook": [
    {{
      "method": "植入方式",
      "best_timing": "最佳植入时机",
      "example": "实际案例"
    }}
  ],
  "speaking_dna": {{
    "common_tone": "共性语气特征",
    "effective_fragments": ["有效的口语碎片"],
    "rhythm_pattern": "节奏规律"
  }},
  "mutation_opportunities": [
    {{
      "gap": "现有视频没做到的点",
      "opportunity": "可以差异化的方向",
      "risk": "低/中/高"
    }}
  ],
  "recommended_skeleton": {{
    "structure": "推荐的脚本骨架描述",
    "mutation_point": "建议在哪个节拍注入变异/创新"
  }}
}}"""

    @staticmethod
    def _parse_json_result(text: str) -> Dict:
        """尝试从Gemini响应中解析JSON"""
        import json
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1].strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        # Try array
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return {"items": json.loads(text[start:end])}
            except json.JSONDecodeError:
                pass
        return {}

    def _build_creative_migration_prompt(
        self, analyses: List[VideoAnalysis], product_name: str, industry: str,
        product_detail: str, creators: List[Dict] = None
    ) -> str:
        """构建创意机制拆解+产品属性匹配+结构同构迁移Prompt"""
        videos_info = ""
        for i, a in enumerate(analyses, 1):
            title = a.title[:50] if hasattr(a, 'title') else str(a.get('title', ''))[:50]
            play = a.play_count if hasattr(a, 'play_count') else a.get('play_count', 0)
            digg = a.digg_count if hasattr(a, 'digg_count') else a.get('digg_count', 0)
            deep = (a.deep_analysis if hasattr(a, 'deep_analysis') else a.get('deep_analysis', ''))[:500]
            structured = a.structured_analysis if hasattr(a, 'structured_analysis') else a.get('structured_analysis', {})

            videos_info += f"\n---\n### 创意视频{i}: {title}\n- 播放量: {play}, 点赞: {digg}\n"
            if structured:
                import json
                cd = structured.get("creative_device", {})
                if cd:
                    videos_info += f"- 创意装置: {cd.get('type', '')} — {cd.get('description', '')}\n"
                    videos_info += f"- 可迁移公式: {cd.get('transferable_formula', '')}\n"
                hook = structured.get("hook", {})
                if hook:
                    videos_info += f"- 钩子: [{hook.get('type', '')}] {hook.get('text', '')[:60]}\n"
                ea = structured.get("emotional_arc", [])
                if ea:
                    videos_info += f"- 情绪弧线: {' → '.join(ea)}\n"
            else:
                videos_info += f"- 深度拆解: {deep}...\n"

        # 博主背景信息
        creator_context = ""
        if creators:
            for c in creators:
                creator_context += f"- {c['name']}({c['category']}): {c['mechanism']}\n  招牌手法: {c['signature_device']}\n"

        return f"""你是创意迁移大师。以下是从特定创意博主的爆款视频中拆解的创意机制:

{f"创意博主背景:{chr(10)}{creator_context}" if creator_context else ""}
{videos_info}

目标产品: "{product_name}" ({industry})
产品详情: {product_detail or '无'}

请完成三步分析:

## Step 1: 创意机制深度拆解
对每个视频，提取:
- 张力结构: 什么制造了好奇缺口？（信息不对称/认知冲突/悬念）
- Payoff设计: 观众"哇"的那一刻是什么？（视觉冲击/认知颠覆/情感释放/反预期）
- 可迁移公式: [X] x [Y] → [Z] 的通用结构

## Step 2: 产品可放大属性分析
"{product_name}"的哪些属性可以被极端化/可视化？
- 物理属性（防水/耐热/强度/质地...）
- 功效属性（修复/美白/清洁/保湿...）
- 情感属性（性价比/信任/身份认同/仪式感...）
选出最适合被创意机制放大的1-2个属性

## Step 3: 结构同构匹配
找到创意机制和产品属性之间的「桥」:
- 哪个创意机制的公式能承载这个产品属性？
- 具体怎么映射？（例: 极致实验x防水 = 泡水24小时测试）
- 给出2个结构同构迁移方案，每个包含:
  - 方案名称
  - 灵感来源（哪个博主的哪个机制）
  - 产品属性对接点
  - 具体执行方案（一句话描述画面）
  - 预期的哇哦时刻

请确保方案新颖到让人说"这个角度我没想到"。"""
