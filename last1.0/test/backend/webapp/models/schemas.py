# -*- coding: utf-8 -*-
"""
API数据模型（Pydantic Schemas）
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class ExportStatus(str, Enum):
    """导出状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class KeyframeStatus(str, Enum):
    """关键帧状态"""
    PENDING = "pending"          # 等待生成
    GENERATING = "generating"    # 生成中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 生成失败
    APPROVED = "approved"       # 用户已批准


class GenerationStage(str, Enum):
    """生成阶段"""
    SCRIPT = "script"           # 脚本阶段
    KEYFRAMES = "keyframes"     # 关键帧图片阶段
    VIDEOS = "videos"           # 视频生成阶段
    EXPORT = "export"           # 导出合并阶段


# ==================== 关键帧相关 ====================

class KeyframeVersion(BaseModel):
    """关键帧版本（单个图片）"""
    version_id: int = Field(..., description="版本ID (1, 2, 3)")
    image_url: str = Field(..., description="图片URL")
    prompt: str = Field(..., description="生成提示词")
    model: str = Field(..., description="使用的模型 (flux-pro, midjourney)")
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="AI质量评分")
    is_selected: bool = Field(default=False, description="是否被用户选中")
    cost: float = Field(default=0.1, description="生成成本（元）")
    created_at: datetime = Field(default_factory=datetime.now)


class KeyframeInfo(BaseModel):
    """关键帧信息（包含多个版本）"""
    shot_id: int = Field(..., description="分镜ID")
    status: KeyframeStatus = Field(default=KeyframeStatus.PENDING)
    versions: List[KeyframeVersion] = Field(default_factory=list, description="所有版本")
    selected_version_id: Optional[int] = Field(None, description="用户选中的版本ID")
    visual_description: str = Field(default="", description="视觉描述")
    narration: str = Field(default="", description="口播文案")
    duration: float = Field(..., description="预期时长（秒）")

    @property
    def selected_version(self) -> Optional[KeyframeVersion]:
        """获取选中的版本"""
        if self.selected_version_id is None:
            return None
        for v in self.versions:
            if v.version_id == self.selected_version_id:
                return v
        return None


# ==================== 分镜相关 ====================

class ShotInfo(BaseModel):
    """分镜信息（视频生成后）"""
    shot_id: int = Field(..., description="分镜ID")
    filename: str = Field(..., description="文件名 (scene_001.mp4)")
    duration: float = Field(..., description="时长（秒）")
    visual_description: str = Field(default="", description="视觉描述")
    narration: str = Field(default="", description="口播文案")
    file_size: int = Field(..., description="文件大小（字节）")
    video_url: str = Field(..., description="视频URL")
    shot_type: Optional[str] = Field(None, description="分镜类型")
    keyframe_url: Optional[str] = Field(None, description="关键帧图片URL")


class ShotList(BaseModel):
    """分镜列表"""
    project_id: str
    shots: List[ShotInfo]
    total_count: int


class ReorderRequest(BaseModel):
    """重排序请求"""
    shot_order: List[int] = Field(..., description="新的分镜顺序 [3, 1, 2, 4]")


# ==================== 创建项目 ====================

class CreateProjectRequest(BaseModel):
    """创建项目请求"""
    topic: str = Field(..., description="视频主题", min_length=1)
    target_duration: int = Field(default=60, ge=30, le=600, description="目标时长（秒）")
    style: str = Field(default="marketing", description="视频风格 (marketing / documentary / narrative)")
    selling_points: Optional[str] = Field(None, description="产品卖点文本")


class ScriptShotItem(BaseModel):
    """脚本镜头项"""
    shot_id: int = Field(..., description="镜头ID")
    shot_type: str = Field(default="broll", description="镜头类型")
    act_type: str = Field(default="main", description="幕类型")
    visual_description: str = Field(default="", description="视觉描述(英文)")
    narration: str = Field(default="", description="口播文案(中文)")
    duration: float = Field(default=5.0, description="时长(秒)")
    use_product_image: bool = Field(default=False, description="是否使用产品图")


class ScriptResponse(BaseModel):
    """脚本响应"""
    project_id: str
    shots: List[ScriptShotItem]
    product_images: List[str] = Field(default_factory=list)


# ==================== 项目相关 ====================

class ProjectSummary(BaseModel):
    """项目摘要（列表页）"""
    project_id: str = Field(..., description="项目ID (video_20260208_221834)")
    title: str = Field(..., description="项目标题")
    topic: str = Field(default="", description="主题")
    shot_count: int = Field(..., description="分镜数量")
    total_duration: float = Field(..., description="总时长（秒）")
    viral_score: float = Field(default=0.0, description="爆款分数 0-100")
    created_at: datetime = Field(..., description="创建时间")
    thumbnail_url: str = Field(..., description="缩略图URL")
    generation_stage: GenerationStage = Field(default=GenerationStage.SCRIPT, description="当前阶段")
    keyframes_ready: int = Field(default=0, description="已完成的关键帧数")
    videos_ready: int = Field(default=0, description="已完成的视频数")


class ProjectDetail(BaseModel):
    """项目详情（编辑页）"""
    project_id: str
    title: str
    topic: str
    shots: List[ShotInfo]
    total_duration: float
    total_shots: int
    viral_score: float = 0.0
    viral_probability: float = 0.0
    viral_breakdown: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None


# ==================== 导出相关 ====================

class ExportConfig(BaseModel):
    """导出配置"""
    output_filename: str = Field(default="final_video.mp4", description="输出文件名")
    resolution: str = Field(default="1920x1080", description="分辨率")
    fps: int = Field(default=30, ge=24, le=60, description="帧率")
    bitrate: str = Field(default="5M", description="码率")
    add_bgm: bool = Field(default=False, description="是否添加背景音乐")
    bgm_path: Optional[str] = Field(None, description="BGM文件路径")
    bgm_volume: float = Field(default=0.3, ge=0.0, le=1.0, description="BGM音量")
    add_transitions: bool = Field(default=False, description="是否添加转场效果")


class ExportTask(BaseModel):
    """导出任务"""
    task_id: str = Field(..., description="任务ID")
    project_id: str = Field(..., description="项目ID")
    status: ExportStatus = Field(..., description="任务状态")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="进度 0.0-1.0")
    message: str = Field(default="", description="状态消息")
    output_url: Optional[str] = Field(None, description="输出视频URL")
    created_at: datetime = Field(default_factory=datetime.now)


class ProgressUpdate(BaseModel):
    """进度更新（WebSocket）"""
    task_id: str
    progress: float = Field(ge=0.0, le=1.0)
    current_step: str = Field(..., description="当前步骤描述")
    status: ExportStatus
    estimated_time: Optional[int] = Field(None, description="预计剩余时间（秒）")


# ==================== 响应模型 ====================

class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: str
    detail: Optional[str] = None


# ==================== 关键帧生成相关 ====================

class KeyframeGenerationConfig(BaseModel):
    """关键帧生成配置"""
    model: str = Field(default="flux-pro", description="图片生成模型")
    quality: str = Field(default="high", description="质量 (high/medium/low)")
    style: Optional[str] = Field(None, description="风格偏好")
    aspect_ratio: str = Field(default="16:9", description="宽高比")
    optimize_prompt: bool = Field(default=True, description="是否使用AI优化提示词")


class KeyframeGenerationTask(BaseModel):
    """关键帧生成任务"""
    task_id: str
    project_id: str
    status: str = Field(default="pending", description="任务状态")
    total_shots: int = Field(..., description="总分镜数")
    completed_shots: int = Field(default=0, description="已完成分镜数")
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str = Field(default="等待开始...")
    estimated_cost: float = Field(..., description="预估成本（元）")
    actual_cost: float = Field(default=0.0, description="实际成本（元）")
    created_at: datetime = Field(default_factory=datetime.now)


class RegenerateKeyframeRequest(BaseModel):
    """重新生成关键帧请求"""
    shot_id: int = Field(..., description="要重新生成的分镜ID")
    version_count: int = Field(default=3, ge=1, le=5, description="生成版本数（1-5）")
    model: str = Field(default="flux-pro", description="图片生成模型")
    custom_prompt: Optional[str] = Field(None, description="自定义提示词（可选）")
    optimize_prompt: bool = Field(default=True, description="是否优化提示词")


class ImageToVideoRequest(BaseModel):
    """图生视频请求"""
    shot_ids: Optional[List[int]] = Field(None, description="指定分镜ID列表（None=全部）")
    model: str = Field(default="kling", description="视频生成模型")
    duration: int = Field(default=5, ge=3, le=10, description="视频时长（秒）")
    motion_strength: float = Field(default=0.5, ge=0.0, le=1.0, description="运镜强度")


class KeyframeListResponse(BaseModel):
    """关键帧列表响应"""
    project_id: str
    keyframes: List[KeyframeInfo]
    total_count: int
    generation_stage: GenerationStage
    estimated_total_cost: float = Field(..., description="预估总成本（元）")


class PromptOptimizationRequest(BaseModel):
    """提示词优化请求"""
    original_prompt: str = Field(..., description="原始提示词")
    shot_type: Optional[str] = Field(None, description="分镜类型")
    style_preference: Optional[str] = Field(None, description="风格偏好")


class PromptOptimizationResponse(BaseModel):
    """提示词优化响应"""
    original_prompt: str
    optimized_prompt: str
    improvements: List[str] = Field(..., description="改进点列表")
    estimated_success_rate: float = Field(..., ge=0.0, le=1.0, description="预估成功率")


# ==================== 智能脚本创作相关 ====================

class CreativeDirection(BaseModel):
    """创意方向"""
    direction_id: int
    name: str = Field(..., description="方向名称: 稳妥款/优化款/创意款")
    risk_level: str = Field(..., description="风险等级: safe/moderate/creative")
    description: str = Field(..., description="策略描述")
    hook: str = Field(..., description="开场钩子示例")
    structure_preview: List[str] = Field(default_factory=list, description="内容结构预览")
    creative_techniques: List[str] = Field(default_factory=list, description="创意手法")


class HookCandidate(BaseModel):
    """Hook候选项"""
    hook_id: int
    style: str = Field(..., description="悬念型/痛点型/数据型/反常识型/场景代入型")
    hook_text: str = Field(..., description="开场口播文案")
    visual_hint: str = Field(..., description="开场画面建议(英文)")
    rationale: str = Field(..., description="创作依据")


class SelectHookRequest(BaseModel):
    """选择Hook请求"""
    hook_id: int


class QualityCheckResult(BaseModel):
    """质量自检结果"""
    word_duration_match: bool = Field(..., description="字数时长匹配")
    selling_point_coverage: List[str] = Field(default_factory=list, description="已覆盖卖点")
    missing_selling_points: List[str] = Field(default_factory=list, description="缺失卖点")
    rhythm_score: float = Field(..., ge=0.0, le=1.0, description="节奏评分")
    issues: List[str] = Field(default_factory=list, description="问题列表")
    auto_fixes: List[str] = Field(default_factory=list, description="自动修复说明")


class SmartCreateRequest(BaseModel):
    """智能创建请求"""
    product_name: str = Field(..., description="产品名称", min_length=1)
    industry: Optional[str] = Field(None, description="行业")
    target_duration: int = Field(default=60, ge=30, le=300, description="目标时长(秒)")
    reference_text: Optional[str] = Field(None, description="参考文案")
    brand_profile_id: Optional[str] = Field(None, description="品牌档案ID")
    product_detail: Optional[str] = Field(None, description="产品详细信息：核心功能、目标用户、与竞品最大区别（填写越详细，脚本越具体）")
    mode: str = Field(default="quick", description="生成模式: quick=快速模式(秒出结果), detailed=详细模式(联网调研慢工出细活)")
    template_id: Optional[str] = Field(None, description="选用的内容模板ID，来自模板库（可选，不填则自动生成结构）")


class SmartCreateResponse(BaseModel):
    """智能创建响应 - 研究+方向"""
    session_id: str
    competitor_summary: Dict = Field(default_factory=dict, description="竞品摘要")
    market_summary: Dict = Field(default_factory=dict, description="市场摘要")
    directions: List[CreativeDirection] = Field(default_factory=list)


class SelectDirectionRequest(BaseModel):
    """选择方向请求"""
    direction_id: int


class ScriptChatRequest(BaseModel):
    """对话修改请求"""
    message: str = Field(..., description="用户消息", min_length=1)
    chat_history: List[Dict] = Field(default_factory=list, description="对话历史")


class ScriptChatResponse(BaseModel):
    """对话修改响应"""
    ai_response: str
    changes_made: List[str] = Field(default_factory=list)
    updated_shots: List[Dict] = Field(default_factory=list)


class BrandProfile(BaseModel):
    """品牌档案"""
    profile_id: str
    brand_name: str
    brand_tone: str = Field(default="", description="品牌调性")
    forbidden_words: List[str] = Field(default_factory=list, description="禁用词")
    preferred_expressions: List[str] = Field(default_factory=list, description="偏好表达")
    visual_style: str = Field(default="", description="视觉风格")
    target_audience: str = Field(default="", description="目标受众")


class CreateBrandProfileRequest(BaseModel):
    """创建品牌档案请求"""
    brand_name: str = Field(..., description="品牌名称", min_length=1)
    brand_tone: str = Field(default="", description="品牌调性")
    forbidden_words: List[str] = Field(default_factory=list)
    preferred_expressions: List[str] = Field(default_factory=list)
    visual_style: str = Field(default="")
    target_audience: str = Field(default="")


# ==================== 分镜审核相关 ====================

class FrameStatus(str, Enum):
    """分镜帧状态"""
    PENDING = "pending"
    GENERATING = "generating"
    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"
    REGENERATING = "regenerating"


class StoryboardFrame(BaseModel):
    """分镜帧"""
    frame_id: int = Field(..., description="帧ID")
    visual_prompt: str = Field(default="", description="英文视觉描述prompt")
    narration: str = Field(default="", description="中文旁白")
    duration: float = Field(default=5.0, ge=2.0, le=15.0, description="时长(秒)")
    shot_type: str = Field(default="medium", description="镜头类型")
    camera_movement: str = Field(default="static", description="运镜方式")
    lighting: str = Field(default="natural", description="光线风格")
    mood: str = Field(default="neutral", description="情绪氛围")
    status: FrameStatus = Field(default=FrameStatus.PENDING, description="帧状态")
    feedback: Optional[str] = Field(None, description="用户驳回反馈")
    image_url: Optional[str] = Field(None, description="分镜图URL")
    video_url: Optional[str] = Field(None, description="视频URL")
    cost_estimate: Dict = Field(default_factory=dict, description="成本估算")


class EnhancedStoryboard(BaseModel):
    """增强版分镜脚本"""
    project_id: str = Field(default="", description="项目ID")
    title: str = Field(default="", description="标题")
    frames: List[StoryboardFrame] = Field(default_factory=list, description="帧列表")
    total_duration: float = Field(default=0.0, description="总时长")
    total_cost_estimate: Dict = Field(default_factory=dict, description="总成本估算")
    hook_type: str = Field(default="suspense", description="Hook类型")
    psychology_framework: str = Field(default="hook_retain_reward", description="心理学框架")
    character: Dict = Field(default_factory=dict, description="角色描述")
    style: str = Field(default="cinematic", description="视觉风格")
    analysis: Dict = Field(default_factory=dict, description="话题分析结果")
    user_input: str = Field(default="", description="用户原始输入")
    created_at: Optional[str] = Field(None, description="创建时间")


class FrameReviewAction(BaseModel):
    """单帧审核动作"""
    frame_id: int = Field(..., description="帧ID")
    action: str = Field(..., description="动作: approve / reject")
    feedback: Optional[str] = Field(None, description="驳回反馈(reject时必填)")


class StoryboardReviewRequest(BaseModel):
    """批量审核请求"""
    actions: List[FrameReviewAction] = Field(..., description="审核动作列表")


class StoryboardGenerateRequest(BaseModel):
    """生成分镜请求"""
    user_input: str = Field(..., description="产品名称", min_length=2)
    style: str = Field(default="cinematic", description="视频风格")
    hook_type: Optional[str] = Field(None, description="指定Hook类型(可选)")
    total_duration: int = Field(default=45, ge=10, le=120, description="目标总时长(秒)")
    character_description: Optional[str] = Field(None, description="行业(可选)")
    product_detail: Optional[str] = Field(None, description="产品卖点/详情(可选)")


# ==================== 一体化脚本视频流水线 ====================

class FullScriptShot(BaseModel):
    """完整脚本中的单个镜头"""
    shot_id: int
    shot_type: str = Field(default="medium", description="镜头类型")
    act_type: str = Field(default="main", description="幕类型")
    visual_description: str = Field(default="", description="英文视觉描述")
    narration: str = Field(default="", description="中文口播文案")
    duration: float = Field(default=5.0, description="时长(秒)")
    camera_movement: str = Field(default="static", description="运镜方式")
    lighting: str = Field(default="natural", description="光线")
    mood: str = Field(default="neutral", description="情绪")
    text_overlay: str = Field(default="", description="文字贴片")
    use_product_image: bool = Field(default=False)


class FullScriptOption(BaseModel):
    """完整脚本选项（3选1）"""
    script_id: int = Field(..., description="脚本ID (0, 1, 2)")
    name: str = Field(..., description="脚本名称: 稳妥款/优化款/创意款")
    risk_level: str = Field(..., description="safe/moderate/creative")
    description: str = Field(default="", description="策略简述")
    shots: List[FullScriptShot] = Field(default_factory=list, description="完整镜头列表")
    total_duration: float = Field(default=0.0, description="总时长")
    selling_points: List[str] = Field(default_factory=list, description="覆盖的卖点")
    quality_report: Dict = Field(default_factory=dict, description="质量报告")


class SmartCreateResponseV2(BaseModel):
    """智能创建响应V2 — 直接返回3个完整脚本"""
    session_id: str
    competitor_summary: Dict = Field(default_factory=dict)
    market_summary: Dict = Field(default_factory=dict)
    scripts: List[FullScriptOption] = Field(default_factory=list, description="3个完整脚本")


class SelectScriptRequest(BaseModel):
    """选择脚本请求"""
    script_id: int = Field(..., description="选中的脚本ID (0, 1, 2)")
    script_data: Optional[Dict[str, Any]] = Field(None, description="完整脚本数据（session重启后recovery用）")
    product_name: Optional[str] = Field(None, description="产品名称（session重启后recovery用）")
    product_detail: Optional[str] = Field(None, description="产品详情（session重启后recovery用）")
    industry: Optional[str] = Field(None, description="行业（session重启后recovery用）")


class RegenerateScriptsRequest(BaseModel):
    """换一批脚本请求"""
    feedback: Optional[str] = Field(None, description="用户反馈/偏好")


class UpdateFrameRequest(BaseModel):
    """更新单帧请求"""
    shot_id: int = Field(..., description="镜头ID")
    narration: Optional[str] = Field(None, description="更新口播文案")
    visual_description: Optional[str] = Field(None, description="更新视觉描述")


class RegenerateFrameImageRequest(BaseModel):
    """重新生成单帧图片请求"""
    feedback: Optional[str] = Field(None, description="修改反馈")
    global_style: str = Field(default="", description="全局风格提示词")


class SkipToPreviewRequest(BaseModel):
    """用户自带脚本跳转预览"""
    user_script: str = Field(..., description="用户自由文本脚本", min_length=10)
    target_duration: int = Field(default=60, ge=15, le=300, description="目标时长(秒)")


# ==================== 数据驱动脚本生成 ====================

class VideoAnalysisResult(BaseModel):
    """视频分析结果"""
    aweme_id: str = Field(..., description="视频ID")
    title: str = Field(default="", description="视频标题")
    author: str = Field(default="", description="作者")
    play_count: int = Field(default=0, description="播放量")
    digg_count: int = Field(default=0, description="点赞量")
    comment_count: int = Field(default=0, description="评论数")
    duration: int = Field(default=0, description="时长(毫秒)")
    cover_url: str = Field(default="", description="封面URL")
    asr_text: str = Field(default="", description="口播原文")
    structure_analysis: str = Field(default="", description="结构拆解")
    creative_device: str = Field(default="", description="创意装置")
    success_factors: str = Field(default="", description="成功因素")


class ResearchProgress(BaseModel):
    """调研进度"""
    phase: str = Field(..., description="阶段: searching|downloading|analyzing|generating|done|error")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="进度 0-1")
    details: List[str] = Field(default_factory=list, description="进度明细")


class DataDrivenScript(BaseModel):
    """数据驱动脚本"""
    script_id: int = Field(..., description="脚本ID (0, 1, 2)")
    direction: str = Field(..., description="方向标识: industry|comments|creative")
    direction_label: str = Field(..., description="方向名称: 同行业模仿|评论区需求|创意迁移")
    name: str = Field(..., description="脚本名称")
    data_source: str = Field(default="", description="数据依据描述")
    reference_videos: List[Dict] = Field(default_factory=list, description="参考视频信息")
    shots: List[Dict] = Field(default_factory=list, description="镜头列表")
    total_duration: float = Field(default=0.0, description="总时长")
    selling_points: List[str] = Field(default_factory=list, description="卖点")
    quality_report: Dict = Field(default_factory=dict, description="质量报告")


class SmartCreateV2Request(BaseModel):
    """数据驱动智能创建请求"""
    product_name: str = Field(..., description="产品名称", min_length=1)
    industry: Optional[str] = Field(None, description="行业")
    target_duration: int = Field(default=60, ge=30, le=300, description="目标时长(秒)")
    reference_text: Optional[str] = Field(None, description="参考文案")
    brand_profile_id: Optional[str] = Field(None, description="品牌档案ID")
    product_detail: Optional[str] = Field(None, description="产品详情")


class SmartCreateV2Response(BaseModel):
    """数据驱动智能创建响应"""
    session_id: str
    phase: str = Field(default="researching", description="当前阶段")


class ResearchStatusResponse(BaseModel):
    """调研状态响应"""
    session_id: str
    phase: str = Field(..., description="searching|analyzing|generating|done|error")
    progress: float = Field(default=0.0)
    details: List[str] = Field(default_factory=list)
    error: Optional[str] = Field(None)


class ResearchResultResponse(BaseModel):
    """调研结果响应"""
    session_id: str
    scripts: List[DataDrivenScript] = Field(default_factory=list, description="3个数据驱动脚本")
    research_data: Dict = Field(default_factory=dict, description="调研数据（方向A/B/C）")
