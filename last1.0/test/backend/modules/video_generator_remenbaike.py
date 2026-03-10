# -*- coding: utf-8 -*-
"""
全并发视频生成系统 - Remenbaike API版本
支持Veo、Kling、Grok三个平台，30-50个分镜同时生成
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from typing import List, Dict, Optional
from loguru import logger
import time
import os

from models import Shot, VideoScript, GenerationTask
from modules.video_api_remenbaike import RembaikeVideoAPI
from config_remenbaike import (
    MAX_CONCURRENT_SUBMISSIONS,
    MAX_CONCURRENT_DOWNLOADS,
    TASK_POLL_INTERVAL,
    TASK_MAX_WAIT_TIME
)


class RembaikeVideoGenerator:
    """Remenbaike全并发视频生成系统"""

    def __init__(self, api_key: Optional[str] = None):
        self.api = RembaikeVideoAPI(api_key)
        logger.info("🚀 Remenbaike全并发视频生成系统初始化完成")
        logger.info(f"   最大并发提交: {MAX_CONCURRENT_SUBMISSIONS}")
        logger.info(f"   最大并发下载: {MAX_CONCURRENT_DOWNLOADS}")

    async def generate_all(
        self,
        script: VideoScript,
        output_dir: str
    ) -> Dict:
        """
        生成所有分镜视频（全并发）

        Args:
            script: 视频脚本
            output_dir: 输出目录

        Returns:
            生成结果统计
        """
        all_shots = script.get_all_shots()
        total_count = len(all_shots)

        logger.info(f"🎬 开始全并发生成 {total_count} 个视频片段")
        logger.info(f"   预计时长: 3-10分钟 (基于Kling最快76秒)")

        os.makedirs(output_dir, exist_ok=True)

        start_time = time.time()

        # Step 1: 全并发提交所有任务
        logger.info(f"\n📤 Step 1/3: 提交所有任务...")
        tasks = await self._submit_all_tasks(all_shots)

        success_tasks = [t for t in tasks if t.status == "submitted"]
        failed_tasks = [t for t in tasks if t.status == "failed"]

        logger.info(f"   提交完成: {len(success_tasks)}/{total_count} 成功")
        if failed_tasks:
            logger.warning(f"   ⚠️  提交失败: {len(failed_tasks)} 个")

        if not success_tasks:
            logger.error("❌ 所有任务提交失败!")
            return {"success_count": 0, "failed_count": total_count, "total_duration": 0}

        # Step 2: 轮询等待所有任务完成
        logger.info(f"\n⏳ Step 2/3: 等待生成完成...")
        completed_tasks = await self._poll_all_tasks(success_tasks)

        success_count = len([t for t in completed_tasks if t.status == "completed"])
        failed_count = len([t for t in completed_tasks if t.status == "failed"])

        logger.info(f"   生成完成: {success_count} 成功, {failed_count} 失败")

        # Step 3: 批量下载所有成功的视频
        logger.info(f"\n⬇️  Step 3/3: 下载视频...")
        downloaded_count = await self._download_all_videos(completed_tasks, output_dir)

        logger.info(f"   下载完成: {downloaded_count}/{success_count}")

        total_duration = time.time() - start_time

        logger.info(f"\n✅ 全部完成!")
        logger.info(f"   总耗时: {total_duration/60:.1f}分钟")
        logger.info(f"   成功率: {downloaded_count/total_count*100:.1f}%")

        return {
            "success_count": downloaded_count,
            "failed_count": total_count - downloaded_count,
            "total_duration": total_duration,
            "tasks": completed_tasks
        }

    async def _submit_all_tasks(self, shots: List[Shot]) -> List[GenerationTask]:
        """全并发提交所有任务"""
        submit_coroutines = []

        for shot in shots:
            coroutine = self._submit_single_task(shot)
            submit_coroutines.append(coroutine)

        # 控制并发数
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_SUBMISSIONS)

        async def submit_with_semaphore(coro):
            async with semaphore:
                return await coro

        tasks = await asyncio.gather(
            *[submit_with_semaphore(coro) for coro in submit_coroutines]
        )

        return tasks

    async def _submit_single_task(self, shot: Shot) -> GenerationTask:
        """提交单个任务"""
        task = GenerationTask(
            task_id="",
            shot=shot,
            status="pending"
        )

        try:
            # 构建prompt
            prompt = self._build_prompt(shot)

            # 提交
            success, task_id, error = await self.api.submit_task(
                model_id=shot.assigned_model,
                prompt=prompt,
                duration=int(shot.duration),
                aspect_ratio="9:16"
            )

            if success:
                task.task_id = task_id
                task.status = "submitted"
                task.submitted_at = time.time()
                shot.task_id = task_id
                logger.debug(f"✅ [分镜{shot.id}] 已提交: {task_id}")
            else:
                task.status = "failed"
                shot.generation_error = error
                logger.error(f"❌ [分镜{shot.id}] 提交失败: {error}")

        except Exception as e:
            task.status = "failed"
            shot.generation_error = str(e)
            logger.error(f"❌ [分镜{shot.id}] 提交异常: {e}")

        return task

    async def _poll_all_tasks(self, tasks: List[GenerationTask]) -> List[GenerationTask]:
        """轮询所有任务状态"""
        pending_tasks = tasks.copy()
        completed_tasks = []

        elapsed = 0
        poll_count = 0

        while pending_tasks and elapsed < TASK_MAX_WAIT_TIME:
            await asyncio.sleep(TASK_POLL_INTERVAL)
            elapsed += TASK_POLL_INTERVAL
            poll_count += 1

            logger.info(f"   [轮询#{poll_count}] 检查 {len(pending_tasks)} 个任务... ({elapsed}s)")

            # 批量查询
            query_results = await self._query_batch(pending_tasks)

            # 更新状态
            still_pending = []
            for task, (status, video_url, error) in zip(pending_tasks, query_results):
                if status == 1:  # 成功
                    task.status = "completed"
                    task.completed_at = time.time()
                    task.shot.video_url = video_url
                    task.shot.generation_success = True
                    completed_tasks.append(task)
                    logger.info(f"   ✅ [分镜{task.shot.id}] 生成完成")
                elif status == 2:  # 失败
                    task.status = "failed"
                    task.shot.generation_error = error or "生成失败"
                    completed_tasks.append(task)
                    logger.error(f"   ❌ [分镜{task.shot.id}] 生成失败: {error}")
                else:  # 0，继续等待
                    still_pending.append(task)

            pending_tasks = still_pending

            progress = len(completed_tasks)
            total = len(tasks)
            logger.info(f"   进度: {progress}/{total} ({progress/total*100:.1f}%)")

        # 超时的任务标记为失败
        for task in pending_tasks:
            task.status = "failed"
            task.shot.generation_error = "生成超时"
            completed_tasks.append(task)
            logger.warning(f"   ⚠️  [分镜{task.shot.id}] 超时")

        return completed_tasks

    async def _query_batch(self, tasks: List[GenerationTask]) -> List[tuple]:
        """批量查询任务状态"""
        query_coroutines = []

        for task in tasks:
            coroutine = self.api.query_task(
                model_id=task.shot.assigned_model,
                task_id=task.task_id
            )
            query_coroutines.append(coroutine)

        results = await asyncio.gather(*query_coroutines)
        return results

    async def _download_all_videos(
        self,
        tasks: List[GenerationTask],
        output_dir: str
    ) -> int:
        """批量下载所有视频"""
        success_tasks = [t for t in tasks if t.status == "completed" and t.shot.video_url]

        if not success_tasks:
            return 0

        # 控制下载并发
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

        async def download_with_semaphore(task: GenerationTask):
            async with semaphore:
                return await self._download_single_video(task, output_dir)

        results = await asyncio.gather(
            *[download_with_semaphore(task) for task in success_tasks]
        )

        success_count = sum(results)
        return success_count

    async def _download_single_video(
        self,
        task: GenerationTask,
        output_dir: str
    ) -> bool:
        """下载单个视频"""
        shot = task.shot
        video_url = shot.video_url
        save_path = os.path.join(output_dir, f"scene_{shot.id:03d}.mp4")

        try:
            success = await self.api.download_video(video_url, save_path)
            if success:
                shot.video_path = save_path
                logger.debug(f"💾 [分镜{shot.id}] 保存成功")
                return True
            else:
                logger.error(f"❌ [分镜{shot.id}] 下载失败")
                return False
        except Exception as e:
            logger.error(f"❌ [分镜{shot.id}] 下载异常: {e}")
            return False

    def _build_prompt(self, shot: Shot) -> str:
        """构建优化的prompt"""
        base_prompt = shot.visual_description

        # 添加类型约束
        shot_type = shot.shot_type.value
        if shot_type == "talking_head":
            type_constraint = "人物特写镜头，正面对镜头，自然表情。"
        elif shot_type == "product":
            type_constraint = "产品特写镜头，干净背景，无人物，专业摄影。"
        elif shot_type == "scene":
            type_constraint = "环境场景镜头，中景或远景，展现氛围。"
        elif shot_type == "hands_on":
            type_constraint = "手部操作特写，展示使用过程，清晰展现动作。"
        elif shot_type == "effect":
            type_constraint = "效果展示镜头，对比或数据可视化，清晰明了。"
        else:
            type_constraint = ""

        # 中国场景约束
        chinese_constraint = "中国场景，中文环境，现代风格。"

        # 组合最终prompt
        final_prompt = f"{base_prompt}。{type_constraint}{chinese_constraint}"

        return final_prompt


# 测试
if __name__ == "__main__":
    from models import Shot, ShotType, ActType, Act, VideoScript

    async def test():
        generator = RembaikeVideoGenerator()

        # 创建测试脚本
        test_shots = [
            Shot(1, ShotType.TALKING_HEAD, ActType.ACT1, "年轻女性对镜头微笑", "你好", 5.0),
            Shot(2, ShotType.PRODUCT, ActType.ACT2, "产品特写", "这是产品", 5.0),
            Shot(3, ShotType.SCENE, ActType.ACT3, "办公室场景", "环境展示", 5.0),
        ]

        # 分配模型（使用最快的Kling）
        for shot in test_shots:
            shot.assigned_model = "kling-v2.5-turbo"

        act1 = Act(ActType.ACT1, shots=[test_shots[0]])
        act2 = Act(ActType.ACT2, shots=[test_shots[1]])
        act3 = Act(ActType.ACT3, shots=[test_shots[2]])

        script = VideoScript(
            title="测试视频",
            topic="测试",
            target_duration=15,
            acts=[act1, act2, act3]
        )

        # 生成
        result = await generator.generate_all(
            script=script,
            output_dir="./outputs/test_remenbaike"
        )

        print(f"\n生成结果:")
        print(f"  成功: {result['success_count']}")
        print(f"  失败: {result['failed_count']}")
        print(f"  耗时: {result['total_duration']/60:.1f}分钟")

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(test())
