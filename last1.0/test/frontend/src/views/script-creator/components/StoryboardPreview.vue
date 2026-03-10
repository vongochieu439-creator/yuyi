<template>
  <div class="storyboard-preview">
    <div class="header">
      <h3>分镜预览</h3>
      <div class="actions">
        <el-button
          :loading="store.previewGenerating"
          @click="store.generatePreview()"
          type="primary"
        >
          {{ store.previewFrames.some(f => f.image_url) ? '重新生成全部' : '生成分镜图' }}
        </el-button>
        <el-button
          type="success"
          :disabled="store.previewGenerating || !store.previewFrames.some(f => f.image_url)"
          @click="handleStartVideo"
        >
          生成视频
        </el-button>
      </div>
    </div>

    <!-- 全局风格输入区 -->
    <GlobalPromptInput
      v-model="store.globalStyle"
      :total-frames="store.previewFrames.length"
    />

    <!-- AI 优化提示词状态 -->
    <el-alert
      v-if="store.promptEngineeringStatus"
      :title="store.promptEngineeringStatus"
      type="info"
      :closable="false"
      show-icon
      class="pe-status"
    />

    <el-row :gutter="16">
      <el-col
        :span="8"
        v-for="frame in store.previewFrames"
        :key="frame.shot_id"
        class="frame-col"
      >
        <el-card class="frame-card" shadow="hover">
          <!-- 图片区域 -->
          <div class="frame-image" @click="openEditor(frame)">
            <el-image
              v-if="frame.image_url"
              :src="getImageUrl(frame.image_url)"
              fit="cover"
              class="preview-img"
            />
            <div v-else-if="frame.generating" class="placeholder loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>生成中...</span>
            </div>
            <div v-else-if="frame.error" class="placeholder error">
              <span>{{ frame.error }}</span>
              <el-button size="small" @click.stop="store.regenerateFrameImage(frame.shot_id)">
                重试
              </el-button>
            </div>
            <div v-else class="placeholder empty">
              <span>点击生成按钮</span>
            </div>
          </div>

          <!-- 信息区域 -->
          <div class="frame-info">
            <div class="frame-meta">
              <el-tag size="small">{{ frame.shot_type }}</el-tag>
              <span class="frame-dur">{{ frame.duration }}s</span>
              <span class="frame-id">#{{ frame.shot_id }}</span>
            </div>
            <p class="frame-narration">{{ frame.narration }}</p>
          </div>

          <!-- 操作按钮 -->
          <div class="frame-actions">
            <el-button size="small" text @click="openEditor(frame)">编辑</el-button>
            <el-button
              size="small"
              text
              :loading="frame.generating"
              @click="store.regenerateFrameImage(frame.shot_id)"
            >重新生成</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑镜头" width="600px">
      <el-form v-if="editingFrame" label-position="top">
        <el-form-item label="口播文案">
          <el-input
            v-model="editNarration"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="画面描述 (English)">
          <el-input
            v-model="editVisualDesc"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="重新生成反馈 (可选)">
          <el-input v-model="regenFeedback" placeholder="描述你想要的修改方向..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button @click="handleSaveAndRegen" type="warning">保存并重新生成图片</el-button>
        <el-button @click="handleSave" type="primary">仅保存文案</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useScriptCreatorStore } from '../../../stores/scriptCreator'
import type { PreviewFrame } from '../../../types'
import GlobalPromptInput from './GlobalPromptInput.vue'

const store = useScriptCreatorStore()
const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

const editDialogVisible = ref(false)
const editingFrame = ref<PreviewFrame | null>(null)
const editNarration = ref('')
const editVisualDesc = ref('')
const regenFeedback = ref('')

const getImageUrl = (url: string) => {
  if (url.startsWith('http')) return url
  return `${baseUrl}${url}`
}

const openEditor = (frame: PreviewFrame) => {
  editingFrame.value = frame
  editNarration.value = frame.narration
  editVisualDesc.value = frame.visual_description
  regenFeedback.value = ''
  editDialogVisible.value = true
}

const handleSave = async () => {
  if (!editingFrame.value) return
  await store.updateFrame(
    editingFrame.value.shot_id,
    editNarration.value,
    editVisualDesc.value,
  )
  editDialogVisible.value = false
  ElMessage.success('已保存')
}

const handleSaveAndRegen = async () => {
  if (!editingFrame.value) return
  await store.updateFrame(
    editingFrame.value.shot_id,
    editNarration.value,
    editVisualDesc.value,
  )
  await store.regenerateFrameImage(editingFrame.value.shot_id, regenFeedback.value || undefined)
  editDialogVisible.value = false
  ElMessage.success('已保存并开始重新生成')
}

const handleStartVideo = () => {
  store.startVideoProduction()
}
</script>

<style scoped>
.storyboard-preview { padding: 20px 0; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.pe-status { margin-bottom: 14px; }
.actions { display: flex; gap: 8px; }
.frame-col { margin-bottom: 16px; }
.frame-card { overflow: hidden; }
.frame-image { width: 100%; aspect-ratio: 16/9; cursor: pointer; overflow: hidden; border-radius: 4px; }
.preview-img { width: 100%; height: 100%; }
.placeholder {
  width: 100%; height: 100%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: #f5f7fa; color: #999; font-size: 13px; gap: 8px;
}
.placeholder.loading { background: #ecf5ff; color: #409eff; }
.placeholder.error { background: #fef0f0; color: #f56c6c; }
.frame-info { padding: 8px 0; }
.frame-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.frame-dur { font-size: 12px; color: #999; }
.frame-id { font-size: 12px; color: #ccc; margin-left: auto; }
.frame-narration { font-size: 13px; color: #666; line-height: 1.4; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.frame-actions { display: flex; gap: 4px; border-top: 1px solid #f0f0f0; padding-top: 8px; }
</style>
