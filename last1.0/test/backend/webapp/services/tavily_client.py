# -*- coding: utf-8 -*-
"""
Tavily AI搜索客户端 - 产品市场调研
"""
import asyncio
import httpx
from typing import Dict, Optional
from loguru import logger

from ..config import TAVILY_API_KEY, TAVILY_BASE_URL


class TavilyClient:
    """Tavily API客户端 - AI搜索引擎"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or TAVILY_API_KEY
        self.base_url = base_url or TAVILY_BASE_URL

    async def search(self, query: str, max_results: int = 5, include_answer: bool = True) -> Dict:
        """
        执行AI搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数
            include_answer: 是否包含AI总结

        Returns:
            {answer, results: [{url, title, content, score}]}
        """
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": include_answer,
                "search_depth": "basic"
            }

            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                resp = await client.post(
                    f"{self.base_url}/search",
                    json=payload
                )

                if resp.status_code != 200:
                    logger.error(f"Tavily搜索失败: status={resp.status_code}, body={resp.text[:200]}")
                    return {"answer": "", "results": []}

                data = resp.json()
                results = []
                for r in data.get("results", []):
                    results.append({
                        "url": r.get("url", ""),
                        "title": r.get("title", ""),
                        "content": r.get("content", ""),
                        "score": r.get("score", 0)
                    })

                logger.info(f"Tavily搜索'{query}'返回{len(results)}条结果")
                return {
                    "answer": data.get("answer", ""),
                    "results": results
                }

        except Exception as e:
            logger.error(f"Tavily搜索异常: {e}")
            return {"answer": "", "results": []}

    async def research_product(self, product_name: str, industry: Optional[str] = None) -> Dict:
        """
        多维度产品调研

        Args:
            product_name: 产品名称
            industry: 行业(可选)

        Returns:
            {summary, key_findings: [], sources: []}
        """
        industry_prefix = f"{industry} " if industry else ""

        queries = [
            f"{industry_prefix}{product_name} 卖点 优势 特色",
            f"{industry_prefix}{product_name} 用户评价 口碑",
            f"{industry_prefix}{product_name} 竞品 对比 市场"
        ]

        try:
            tasks = [self.search(q, max_results=3) for q in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_findings = []
            all_sources = []
            summaries = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Tavily调研查询{i+1}失败: {result}")
                    continue

                if result.get("answer"):
                    summaries.append(result["answer"])

                for r in result.get("results", []):
                    if r.get("content"):
                        all_findings.append(r["content"][:200])
                    if r.get("url"):
                        all_sources.append({
                            "url": r["url"],
                            "title": r.get("title", "")
                        })

            summary = " ".join(summaries) if summaries else f"关于{product_name}的市场调研数据"

            logger.info(f"Tavily产品调研完成: {len(all_findings)}条发现, {len(all_sources)}个来源")
            return {
                "summary": summary,
                "key_findings": all_findings[:10],
                "sources": all_sources[:10]
            }

        except Exception as e:
            logger.error(f"Tavily产品调研异常: {e}")
            return {
                "summary": f"关于{product_name}的市场调研（数据获取失败）",
                "key_findings": [],
                "sources": []
            }
