# -*- coding: utf-8 -*-
"""
项目相关API路由
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from loguru import logger

from ..services.project_manager import ProjectManager
from ..services.gemini_client import GeminiClient
from ..models.schemas import (
    ProjectSummary, ProjectDetail, CreateProjectRequest,
    SuccessResponse, ScriptShotItem, ScriptResponse
)
from ..config import PROJECT_ROOT, OUTPUTS_DIR

# 将项目根目录加入 sys.path，以便导入顶层的 engines/models/config
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engines.director import Director

router = APIRouter(prefix="/api/projects", tags=["projects"])

# 创建项目管理器实例
project_manager = ProjectManager()
gemini_client = GeminiClient()


@router.post("/create", response_model=SuccessResponse)
async def create_project(request: CreateProjectRequest):
    """
    创建新视频项目

    流程：
    1. 用 Director 生成视频规划和脚本结构
    2. 用 Gemini 填充脚本内容（visual_description + narration）
    3. 创建项目目录 outputs/video_{timestamp}/
    4. 将脚本数据保存为 metadata.json
    5. 返回项目信息
    """
    try:
        logger.info(f"开始创建项目: 主题={request.topic}, 时长={request.target_duration}s, 风格={request.style}")

        # Step 1: 用 Director 生成视频规划
        director = Director()
        video_plan = director.create_video_plan(
            topic=request.topic,
            target_duration=request.target_duration,
            style=request.style
        )

        # Step 2: 生成脚本结构
        script = director.generate_script_structure(video_plan)

        # Step 3: 创建项目目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_id = f"video_{timestamp}"
        project_dir = Path(OUTPUTS_DIR) / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # Step 4: 准备镜头结构数据
        shots_data = []
        shots_structure = []
        for shot in script.get_all_shots():
            shot_dict = {
                "id": shot.id,
                "shot_type": shot.shot_type.value,
                "act_type": shot.act_type.value,
                "visual_description": shot.visual_description,
                "narration": shot.narration,
                "duration": shot.duration,
                "emotion_score": shot.emotion_score
            }
            shots_data.append(shot_dict)
            shots_structure.append({
                "id": shot.id,
                "shot_type": shot.shot_type.value,
                "act_type": shot.act_type.value,
                "duration": shot.duration
            })

        # Step 5: 用 Gemini 生成脚本内容
        try:
            logger.info("调用Gemini生成脚本内容...")
            script_content = await gemini_client.generate_script_content(
                topic=request.topic,
                shots_structure=shots_structure,
                style=request.style,
                product_info=request.selling_points
            )

            # 将Gemini生成的内容写入shots_data
            content_map = {item["shot_id"]: item for item in script_content}
            for shot in shots_data:
                content = content_map.get(shot["id"])
                if content:
                    shot["visual_description"] = content.get("visual_description", shot["visual_description"])
                    shot["narration"] = content.get("narration", shot["narration"])

            logger.info(f"Gemini脚本内容生成成功, 共{len(script_content)}个镜头")

        except Exception as e:
            logger.warning(f"Gemini生成失败，使用Director原始内容: {e}")

        # Step 6: 标记产品镜头
        for shot in shots_data:
            shot["use_product_image"] = shot.get("shot_type") in ("product", "hands_on")

        metadata = {
            "title": script.title,
            "topic": script.topic,
            "target_duration": script.target_duration,
            "total_duration": script.total_duration,
            "shot_count": script.shot_count,
            "viral_score": script.viral_score,
            "generation_stage": "script",
            "style": request.style,
            "selling_points": request.selling_points,
            "shots": shots_data,
            "product_images": [],
            "keyframes": [],
            "created_at": datetime.now().isoformat()
        }

        # Step 7: 保存 metadata.json
        metadata_path = project_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"项目创建成功: {project_id}, 共 {script.shot_count} 个分镜")

        return SuccessResponse(
            success=True,
            message=f"项目创建成功，共 {script.shot_count} 个分镜",
            data={
                "project_id": project_id,
                "title": script.title,
                "shot_count": script.shot_count,
                "total_duration": script.total_duration,
                "generation_stage": "script"
            }
        )

    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.post("/{project_id}/upload-images", response_model=SuccessResponse)
async def upload_product_images(project_id: str, files: List[UploadFile] = File(...)):
    """
    上传产品图片

    保存到 outputs/{project_id}/products/
    """
    project_dir = Path(OUTPUTS_DIR) / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="项目不存在")

    products_dir = project_dir / "products"
    products_dir.mkdir(exist_ok=True)

    saved_urls = []
    for i, file in enumerate(files):
        ext = Path(file.filename).suffix or ".jpg"
        filename = f"product_{i+1:02d}{ext}"
        save_path = products_dir / filename

        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        url = f"/videos/{project_id}/products/{filename}"
        saved_urls.append(url)
        logger.info(f"产品图已保存: {save_path}")

    # 更新metadata
    metadata_path = project_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        metadata["product_images"] = saved_urls
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    return SuccessResponse(
        success=True,
        message=f"成功上传 {len(saved_urls)} 张产品图",
        data={"product_images": saved_urls}
    )


@router.get("/{project_id}/script", response_model=ScriptResponse)
async def get_project_script(project_id: str):
    """
    获取项目脚本数据
    """
    project_dir = Path(OUTPUTS_DIR) / project_id
    metadata_path = project_dir / "metadata.json"

    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="项目不存在")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    shots = []
    for i, shot in enumerate(metadata.get("shots", [])):
        # 健壮解析 shot_id: 可能是 int, str("1"), 或 str("Shot 1")
        raw_id = shot.get("id", shot.get("shot_id", i + 1))
        try:
            shot_id = int(raw_id)
        except (ValueError, TypeError):
            # 尝试从字符串中提取数字，如 "Shot 1" -> 1
            import re
            nums = re.findall(r'\d+', str(raw_id))
            shot_id = int(nums[0]) if nums else i + 1
        shots.append(ScriptShotItem(
            shot_id=shot_id,
            shot_type=shot.get("shot_type", "broll"),
            act_type=shot.get("act_type", "main"),
            visual_description=shot.get("visual_description", ""),
            narration=shot.get("narration", ""),
            duration=float(shot.get("duration", 5.0)),
            use_product_image=shot.get("use_product_image", False)
        ))

    return ScriptResponse(
        project_id=project_id,
        shots=shots,
        product_images=metadata.get("product_images", [])
    )


@router.put("/{project_id}/script", response_model=SuccessResponse)
async def update_project_script(project_id: str, shots: List[ScriptShotItem]):
    """
    保存用户编辑后的脚本
    """
    project_dir = Path(OUTPUTS_DIR) / project_id
    metadata_path = project_dir / "metadata.json"

    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="项目不存在")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # 更新shots数据
    existing_shots = metadata.get("shots", [])
    shot_map = {s.shot_id: s for s in shots}

    for existing in existing_shots:
        updated = shot_map.get(existing.get("id"))
        if updated:
            existing["visual_description"] = updated.visual_description
            existing["narration"] = updated.narration
            existing["use_product_image"] = updated.use_product_image

    metadata["shots"] = existing_shots

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return SuccessResponse(
        success=True,
        message="脚本已保存",
        data={"shot_count": len(shots)}
    )


@router.delete("/{project_id}", response_model=SuccessResponse)
async def delete_project(project_id: str):
    """删除项目及其所有文件"""
    import shutil
    project_dir = Path(OUTPUTS_DIR) / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="项目不存在")

    try:
        shutil.rmtree(project_dir)
        logger.info(f"项目已删除: {project_id}")
        return SuccessResponse(
            success=True,
            message="项目已删除",
            data={"project_id": project_id}
        )
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")


@router.get("/", response_model=List[ProjectSummary])
async def list_projects():
    """获取所有视频项目列表"""
    try:
        projects = await project_manager.list_all_projects()
        return projects
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project_detail(project_id: str):
    """获取项目详情"""
    try:
        project = await project_manager.get_project_detail(project_id)

        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")

        return project

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败 {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")
