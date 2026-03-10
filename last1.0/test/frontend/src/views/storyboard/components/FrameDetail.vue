<script setup lang="ts">
import { ref } from 'vue'
import { Check, Close, RefreshRight } from '@element-plus/icons-vue'
import type { StoryboardFrame } from '../../../stores/storyboard'

const props = defineProps<{
  frame: StoryboardFrame | null
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [val: boolean]
  approve: [frameId: number]
  reject: [frameId: number, feedback: string]
  regenerate: [frameId: number, feedback: string]
}>()

const feedbackText = ref('')

const handleRegenerate = () => {
  if (props.frame) {
    emit('regenerate', props.frame.frame_id, feedbackText.value)
    feedbackText.value = ''
    emit('update:visible', false)
  }
}

const shotTypeLabels: Record<string, string> = {
  wide: '全景', medium: '中景', close_up: '特写', extreme_close: '极特写',
  pov: '主观视角', aerial: '航拍', low_angle: '仰拍', high_angle: '俯拍',
  over_shoulder: '过肩', extreme_wide: '大全景',
}
const cameraLabels: Record<string, string> = {
  static: '静止', zoom_in: '推进', zoom_out: '拉远', pan_left: '左摇',
  pan_right: '右摇', shake: '手持抖动', breathe: '呼吸感', slow_up: '上移',
  tracking: '跟踪', dolly_in: '推轨', crane_up: '摇臂上升',
}
const lightingLabels: Record<string, string> = {
  golden_hour: '黄金时段', blue_hour: '蓝调冷光', high_key: '高调明亮',
  low_key: '低调暗影', rim_light: '轮廓光', neon: '霓虹光',
  natural: '自然光', dramatic: '戏剧光', soft: '柔光', spotlight: '聚光',
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    width="720px"
    :title="`帧 #${frame?.frame_id} 详情`"
    destroy-on-close
  >
    <div v-if="frame" class="detail-content">
      <!-- 大图 -->
      <div class="detail-image">
        <img v-if="frame.image_url" :src="frame.image_url" />
        <div v-else class="no-image">暂无图片</div>
      </div>

      <!-- 信息 -->
      <div class="detail-info">
        <div class="info-row">
          <label>旁白</label>
          <p>{{ frame.narration }}</p>
        </div>
        <div class="info-row">
          <label>视觉描述</label>
          <p class="visual-prompt">{{ frame.visual_prompt }}</p>
        </div>
        <div class="info-tags">
          <el-tag>{{ frame.duration }}s</el-tag>
          <el-tag type="info">{{ shotTypeLabels[frame.shot_type] || frame.shot_type }}</el-tag>
          <el-tag type="warning">{{ cameraLabels[frame.camera_movement] || frame.camera_movement }}</el-tag>
          <el-tag type="success">{{ lightingLabels[frame.lighting] || frame.lighting }}</el-tag>
          <el-tag type="danger">{{ frame.mood }}</el-tag>
        </div>
      </div>

      <!-- 反馈重新生成 -->
      <div v-if="frame.status === 'generated' || frame.status === 'rejected'" class="detail-feedback">
        <el-input
          v-model="feedbackText"
          type="textarea"
          :rows="2"
          placeholder="输入反馈后重新生成，例如：光线改为暖色调、角色表情改为微笑..."
        />
        <div class="detail-actions">
          <el-button type="success" :icon="Check" @click="emit('approve', frame.frame_id); emit('update:visible', false)">
            通过
          </el-button>
          <el-button type="primary" :icon="RefreshRight" @click="handleRegenerate">
            重新生成
          </el-button>
          <el-button :icon="Close" @click="emit('update:visible', false)">关闭</el-button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<style scoped>
.detail-content { display: flex; flex-direction: column; gap: 16px; }
.detail-image { border-radius: 8px; overflow: hidden; background: #000; }
.detail-image img { width: 100%; display: block; }
.no-image {
  aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center;
  color: #c0c4cc; font-size: 16px;
}
.info-row { margin-bottom: 12px; }
.info-row label { font-size: 13px; color: #909399; font-weight: 500; }
.info-row p { margin: 4px 0 0; font-size: 14px; color: #303133; line-height: 1.6; }
.visual-prompt { font-size: 12px; color: #606266; font-style: italic; }
.info-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.detail-feedback { border-top: 1px solid #ebeef5; padding-top: 12px; }
.detail-actions { display: flex; gap: 8px; margin-top: 10px; justify-content: flex-end; }
</style>
