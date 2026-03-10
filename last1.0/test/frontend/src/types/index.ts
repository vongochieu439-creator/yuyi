// ==================== 脚本创作类型 ====================
export interface ProductInfo {
  product_name: string
  category: string
  price_range: string
  core_features: string[]
  target_audience: string
  use_cases: string[]
  differentiators: string[]
  brand_tone: string
  raw_content: string
}

export interface Direction {
  direction_id: number
  name: string
  risk_level: 'safe' | 'moderate' | 'creative'
  description: string
  hook: string
  structure_preview: string[]
  creative_techniques: string[]
}

export interface Hook {
  hook_id: number
  style: string
  hook_text: string
  visual_hint: string
  rationale: string
}

export interface Shot {
  id: number
  shot_type: string
  act_type: string
  visual_description: string
  narration: string
  rationale: string
  duration: number
  emotion_score: number
  use_product_image: boolean
}

export interface QualityCheck {
  covered_selling_points: string[]
  missing_selling_points: string[]
  total_duration: number
  shot_count: number
  brand_violations?: Array<{ shot_id: number; word: string }>
}

export interface ChatMessage {
  role: 'user' | 'ai'
  content: string
}

export interface Template {
  id: string
  name: string
  category: string
  description: string
  core_strategy: string
  source: string
  use_count: number
}

// ==================== IP工作室类型 ====================
export interface ProfileSummary {
  profile_id: string
  name: string
  industry: string
  role: string
  ip_positioning: string
  content_pillars: string[]
  created_at: string
  topic_count: number
}

export interface Profile extends ProfileSummary {
  interview_qa: ChatMessage[]
  background_summary: string
  key_stories: string[]
  unique_insights: string[]
  speaking_style: string
  signature_phrases: string[]
  target_audience: string
  values: string
  thinking_models: string[]
  decision_framework: string
  emotional_triggers: {
    anger: string[]
    passion: string[]
    pride: string[]
  }
  contrarian_views: string[]
  voice_fingerprint: {
    sentence_pattern: string
    rhetoric_preference: string
    argument_structure: string
    metaphor_domain: string
    forbidden_words: string[]
    raw_quotes: string[]
  }
  business_intent: {
    primary_goal: string
    target_perception: string
    competitive_context: string
  }
  identity_attitude: {
    status_level: string
    communication_tone: string
    hook_preference: string
  }
  opinion_bank: OpinionEntry[]
  expression_patterns: ExpressionPatterns
  edit_history: EditEntry[]
}

export interface OpinionEntry {
  opinion_id: string
  topic: string
  stance: string
  reasoning: string
  raw_expression: string
  emotion: string
  confidence: number
  topic_source: string
  created_at: string
  used_count: number
}

export interface ExpressionPatterns {
  preferred_openings: string[]
  preferred_transitions: string[]
  preferred_closings: string[]
  favorite_phrases: Array<{ phrase: string; context: string }>
  argument_templates: Array<{ pattern: string; example: string }>
}

export interface EditEntry {
  edit_id: string
  original_text: string
  edited_text: string
  topic_title: string
  timestamp: string
}

export interface Topic {
  topic_id: string
  profile_id: string
  index: number
  title: string
  type: string
  hook_opening: string
  core_angle: string
  story_materials: string
  content_outline: string[]
  why_viral: string
  estimated_duration: string
  strategic_angle: string
  created_at: string
}

export interface GeneratedScript {
  profile_id: string
  topic_title: string
  duration: number
  word_count: number
  full_script: string
  paragraphs: ScriptParagraph[]
  thinking_memo: string
  generated_at: string
}

export interface ScriptParagraph {
  index: number
  text: string
  paragraph_id: string
}

// ==================== 产品档案类型 ====================
export interface ProductProfile {
  id: string
  product_name: string
  category: string
  price_range: string
  core_features: string[]
  target_audience: string
  use_cases: string[]
  differentiators: string[]
  brand_tone: string
  raw_content: string
  created_at: string
  updated_at: string
}

export interface IntakeMessage {
  role: 'user' | 'ai'
  content: string
}

// ==================== V2: 一体化流水线类型 ====================

export interface FullScriptShot {
  shot_id: number
  shot_type: string
  act_type: string
  visual_description: string
  narration: string
  duration: number
  camera_movement: string
  lighting: string
  mood: string
  text_overlay: string
  use_product_image: boolean
  preview_image?: string
}

export interface FullScript {
  script_id: number
  name: string
  risk_level: 'safe' | 'moderate' | 'creative'
  description: string
  shots: FullScriptShot[]
  total_duration: number
  selling_points: string[]
  quality_report: Record<string, any>
  hook?: string
  structure_preview?: string[]
  creative_techniques?: string[]
}

export interface PreviewFrame {
  shot_id: number
  image_url: string | null
  narration: string
  visual_description: string
  duration: number
  shot_type: string
  generating: boolean
  error?: string
}

// ==================== V3: 数据驱动类型 ====================

export interface VideoAnalysisResult {
  aweme_id: string
  title: string
  author: string
  play_count: number
  digg_count: number
  comment_count: number
  duration: number
  cover_url: string
  asr_text: string
  structure_analysis: string
  creative_device: string
  success_factors: string
}

export interface ResearchProgress {
  phase: 'searching' | 'downloading' | 'analyzing' | 'generating' | 'done' | 'error'
  progress: number
  details: string[]
}

export interface DataDrivenScript {
  script_id: number
  direction: 'industry' | 'comments' | 'creative'
  direction_label: string
  name: string
  data_source: string
  reference_videos: Array<{
    title: string
    play_count: number
    digg_count: number
  }>
  shots: FullScriptShot[]
  total_duration: number
  selling_points: string[]
  quality_report: Record<string, any>
  hook?: string
  structure_preview?: string[]
  creative_techniques?: string[]
}

export interface ResearchData {
  industry: {
    search_keyword: string
    videos: any[]
    analyses: VideoAnalysisResult[]
    success_patterns: string
  }
  comments: {
    total_comments: number
    cluster_analysis: string
    top_pain_points: string[]
    best_angles: string[]
  }
  creative: {
    search_keyword: string
    videos: any[]
    analyses: VideoAnalysisResult[]
    creative_patterns: string
    migration_ideas: string
  }
}
