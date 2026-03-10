<script setup lang="ts">
import { ref } from 'vue'
import { Check, Close, RefreshRight, View } from '@element-plus/icons-vue'
import type { StoryboardFrame } from '../../../stores/storyboard'

const props = defineProps<{
  frame: StoryboardFrame
  index: number
}>()

const emit = defineEmits<{
  approve: [frameId: number]
  reject: [frameId: number, feedback: string]
  regenerate: [frameId: number, feedback: string]
  detail: [frameId: number]
}>()

const showFeedback = ref(false)
const feedbackText = ref('')

const statusConfig: Record<string, { color: string; text: string }> = {
  pending: { color: '#909399', text: '待生成' },
  generating: { color: '#e6a23c', text: '生成中' },
  generated: { color: '#409eff', text: '待审核' },
  approved: { color: '#67c23a', text: '已通过' },
  rejected: { color: '#f56c6c', text: '已驳回' },
  regenerating: { color: '#e6a23c', text: '重新生成中' },
}

const shotTypeLabels: Record<string, string> = {
  wide: '全景', medium: '中景', close_up: '特写', extreme_close: '极特写',
  pov: '主观', aerial: '航拍', low_angle: '仰拍', high_angle: '俯拍',
  over_shoulder: '过肩', extreme_wide: '大全景',
}

const cameraLabels: Record<string, string> = {
  static: '静止', zoom_in: '推进', zoom_out: '拉远', pan_left: '左摇',
  pan_right: '右摇', shake: '手持', breathe: '呼吸', slow_up: '上移',
  tracking: '跟踪', dolly_in: '推轨', crane_up: '摇臂',
}

const handleReject = () => {
  if (!showFeedback.value) {
    showFeedback.value = true
    return
  }
  emit('reject', props.frame.frame_id, feedbackText.value)
  showFeedback.value = false
  feedbackText.value = ''
}

const handleRegenerate = () => {
  emit('regenerate', props.frame.frame_id, feedbackText.value)
  showFeedback.value = false
  feedbackText.value = ''
}
</script>

<template>
  <div class="frame-card" :class="frame.status">
    <!-- 头部信息 -->
    <div class="frame-header">
      <div class="frame-id">
        <span class="frame-number">#{{ index + 1 }}</span>
        <el-tag :type="frame.status === 'approved' ? 'success' : frame.status === 'rejected' ? 'danger' : 'info'" size="small">
          {{ frame.duration }}s
        </el-tag>
      </div>
      <div class="frame-status">
        <span class="status-dot" :style="{ background: statusConfig[frame.status]?.color }"></span>
        <span class="status-text">{{ statusConfig[frame.status]?.text }}</span>
      </div>
    </div>

    <!-- 图片区域 -->
    <div class="frame-image" @click="emit('detail', frame.frame_id)">
      <img v-if="frame.image_url" :src="frame.image_url" :alt="`帧${frame.frame_id}`" />
      <div v-else-if="frame.status === 'generating' || frame.status === 'regenerating'" class="image-loading">
        <el-icon class="spinning"><RefreshRight /></el-icon>
        <span>生成中...</span>
      </div>
      <div v-else class="image-placeholder">
        <el-icon><View /></el-icon>
        <span>待生成</span>
      </div>
    </div>

    <!-- 分镜信息 -->
    <div class="frame-info">
      <p class="narration">{{ frame.narration }}</p>
      <div class="meta-tags">
        <el-tag size="small" effect="plain">{{ shotTypeLabels[frame.shot_type] || frame.shot_type }}</el-tag>
        <el-tag size="small" effect="plain" type="warning">{{ cameraLabels[frame.camera_movement] || frame.camera_movement }}</el-tag>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div v-if="frame.status === 'generated' || frame.status === 'rejected'" class="frame-actions">
      <el-button type="success" size="small" :icon="Check" @click="emit('approve', frame.frame_id)">通过</el-button>
      <el-button type="danger" size="small" :icon="Close" @click="handleReject" plain>驳回</el-button>
    </div>

    <!-- 反馈输入框 -->
    <div v-if="showFeedback" class="feedback-section">
      <el-input
        v-model="feedbackText"
        type="textarea"
        :rows="2"
        placeholder="描述不满意的地方，例如：光线太暗、角色表情不对..."
        size="small"
      />
      <div class="feedback-actions">
        <el-button type="primary" size="small" :icon="RefreshRight" @click="handleRegenerate">重新生成</el-button>
        <el-button size="small" @click="showFeedback = false; feedbackText = ''">取消</el-button>
      </div>
    </div>

    <!-- 驳回反馈显示 -->
    <div v-if="frame.feedback && frame.status === 'rejected'" class="rejected-feedback">
      <el-icon><Close /></el-icon>
      <span>{{ frame.feedback }}</span>
    </div>
  </div>
</template>

<style scoped>
.frame-card {
  background: white;
  border-radius: 12px;
  border: 2px solid #ebeef5;
  overflow: hidden;
  transition: all 0.3s;
}
.frame-card.approved { border-color: #67c23a; }
.frame-card.rejected { border-color: #f56c6c; }
.frame-card.generating, .frame-card.regenerating { border-color: #e6a23c; animation: pulse 1.5s infinite; }

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(230,162,60,0.3); }
  50% { box-shadow: 0 0 0 6px rgba(230,162,60,0); }
}

.frame-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px; border-bottom: 1px solid #f0f0f0;
}
.frame-id { display: flex; align-items: center; gap: 8px; }
.frame-number { font-weight: bold; font-size: 14px; color: #303133; }

.frame-status { display: flex; align-items: center; gap: 4px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; }
.status-text { font-size: 12px; color: #909399; }

.frame-image {
  aspect-ratio: 16/9; overflow: hidden; cursor: pointer;
  background: #f5f7fa; display: flex; align-items: center; justify-content: center;
}
.frame-image img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }
.frame-image:hover img { transform: scale(1.02); }

.image-loading, .image-placeholder {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  color: #c0c4cc; font-size: 13px;
}
.image-loading .el-icon, .image-placeholder .el-icon { font-size: 28px; }
.spinning { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.frame-info { padding: 10px 12px; }
.narration {
  margin: 0 0 8px; font-size: 13px; color: #606266;
  line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.meta-tags { display: flex; gap: 4px; flex-wrap: wrap; }

.frame-actions { display: flex; gap: 8px; padding: 0 12px 10px; }
.frame-actions .el-button { flex: 1; }

.feedback-section { padding: 0 12px 10px; }
.feedback-actions { display: flex; gap: 8px; margin-top: 8px; }

.rejected-feedback {
  display: flex; align-items: center; gap: 4px;
  padding: 6px 12px 10px; font-size: 12px; color: #f56c6c;
}
</style>
