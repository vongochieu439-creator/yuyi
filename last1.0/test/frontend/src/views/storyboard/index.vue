<script setup lang="ts">
import { ref, watch } from 'vue'
import { ArrowLeft, Refresh, VideoPlay, Check, Picture } from '@element-plus/icons-vue'
import { useStoryboardStore } from '../../stores/storyboard'
import StoryboardInput from './components/StoryboardInput.vue'
import FrameCard from './components/FrameCard.vue'
import FrameDetail from './components/FrameDetail.vue'
import CostPanel from './components/CostPanel.vue'

const store = useStoryboardStore()
const detailVisible = ref(false)
const detailFrame = ref<any>(null)

// 当进入review阶段时加载成本估算
watch(() => store.step, (val) => {
  if (val === 'review' || val === 'storyboard') {
    store.loadCostEstimate()
  }
})

const handleApprove = async (frameId: number) => {
  await store.submitReview([{ frame_id: frameId, action: 'approve' }])
}

const handleReject = async (frameId: number, feedback: string) => {
  await store.submitReview([{ frame_id: frameId, action: 'reject', feedback }])
}

const handleRegenerate = async (frameId: number, feedback: string) => {
  await store.regenFrame(frameId, feedback)
}

const openDetail = (frameId: number) => {
  const frame = store.frames.find(f => f.frame_id === frameId)
  if (frame) {
    detailFrame.value = frame
    detailVisible.value = true
  }
}

const stepLabels: Record<string, string> = {
  input: '输入', generating: '生成分镜', storyboard: '分镜就绪',
  images: '生成图片', review: '审核', producing: '制作视频', done: '完成',
}
</script>

<template>
  <div class="page-centered">
    <!-- Header -->
    <div class="list-header">
      <el-button @click="$router.push('/')" :icon="ArrowLeft">返回</el-button>
      <h2>AI卖货分镜工作台</h2>
      <el-button v-if="store.step !== 'input'" @click="store.reset()" :icon="Refresh" type="info" plain>
        重新开始
      </el-button>
    </div>

    <!-- 进度条 -->
    <div v-if="store.step !== 'input'" class="step-bar">
      <el-steps :active="['input','generating','storyboard','images','review','producing','done'].indexOf(store.step)" finish-status="success" align-center>
        <el-step title="分镜脚本" />
        <el-step title="生成图片" />
        <el-step title="审核调整" />
        <el-step title="视频制作" />
        <el-step title="完成" />
      </el-steps>
      <div v-if="store.progress" class="progress-text">
        <el-icon v-if="store.generating" class="spinning"><Refresh /></el-icon>
        {{ store.progress }}
      </div>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="store.errorMessage"
      :title="store.errorMessage"
      type="error"
      show-icon
      closable
      @close="store.errorMessage = ''"
      style="margin-bottom: 16px;"
    />

    <!-- Step 1: 输入 -->
    <StoryboardInput v-if="store.step === 'input' || store.step === 'error'" />

    <!-- Step 2: 分镜脚本就绪 / 审核模式 -->
    <div v-if="['storyboard', 'images', 'review'].includes(store.step)" class="storyboard-section">
      <!-- 标题信息 -->
      <div class="storyboard-header">
        <div class="header-left">
          <h3>{{ store.title || '分镜脚本' }}</h3>
          <div class="header-tags">
            <el-tag v-if="store.hookTypeResult" size="small" type="warning">{{ store.hookTypeResult }}</el-tag>
            <el-tag v-if="store.frameworkResult" size="small">{{ store.frameworkResult }}</el-tag>
            <el-tag size="small" type="info">{{ store.frames.length }}帧</el-tag>
            <el-tag size="small" type="success">{{ store.approvedCount }}/{{ store.frames.length }} 通过</el-tag>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            v-if="store.step === 'storyboard'"
            type="primary"
            :icon="Picture"
            :loading="store.generating"
            @click="store.startGenerateImages()"
          >
            生成分镜图
          </el-button>
          <el-button
            v-if="store.step === 'review'"
            @click="store.approveAll()"
            type="success"
            :icon="Check"
            :disabled="store.allApproved"
          >
            全部通过
          </el-button>
          <el-button
            v-if="store.step === 'review' && store.allApproved"
            type="primary"
            :icon="VideoPlay"
            @click="store.startProduce()"
          >
            确认制作视频
          </el-button>
        </div>
      </div>

      <!-- 帧网格 -->
      <div class="frame-grid">
        <FrameCard
          v-for="(frame, i) in store.frames"
          :key="frame.frame_id"
          :frame="frame"
          :index="i"
          @approve="handleApprove"
          @reject="handleReject"
          @regenerate="handleRegenerate"
          @detail="openDetail"
        />
      </div>

      <!-- 成本面板 -->
      <CostPanel :cost="store.costEstimate" :loading="!store.costEstimate" />
    </div>

    <!-- Step 3: 正在生成中（分镜/图片） -->
    <div v-if="store.step === 'generating'" class="loading-section">
      <el-icon class="spinning large-icon"><Refresh /></el-icon>
      <p>{{ store.progress }}</p>
    </div>

    <!-- Step 4: 视频制作中 -->
    <div v-if="store.step === 'producing'" class="loading-section">
      <el-icon class="spinning large-icon"><Refresh /></el-icon>
      <p>{{ store.progress }}</p>
      <el-progress :percentage="0" :indeterminate="true" style="width: 300px; margin-top: 12px;" />
    </div>

    <!-- Step 5: 完成 -->
    <div v-if="store.step === 'done' && store.videoUrl" class="video-section">
      <div class="video-header">
        <h3>视频制作完成!</h3>
        <span class="elapsed">用时 {{ store.elapsedSeconds }}s</span>
      </div>
      <div class="video-player-wrap">
        <video :src="store.videoUrl" controls autoplay class="video-player"></video>
      </div>
      <div class="video-actions">
        <el-button type="primary" @click="store.reset()">制作新视频</el-button>
      </div>
    </div>

    <!-- 帧详情弹窗 -->
    <FrameDetail
      v-model:visible="detailVisible"
      :frame="detailFrame"
      @approve="handleApprove"
      @reject="handleReject"
      @regenerate="handleRegenerate"
    />
  </div>
</template>

<style scoped>
.page-centered { max-width: 1100px; margin: 0 auto; padding: 20px; }

.list-header {
  display: flex; align-items: center; gap: 16px; margin-bottom: 20px;
}
.list-header h2 { flex: 1; margin: 0; }

.step-bar {
  background: white; border-radius: 12px; padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 20px;
}
.progress-text {
  text-align: center; margin-top: 8px; font-size: 13px; color: #909399;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}

.storyboard-section { display: flex; flex-direction: column; gap: 16px; }

.storyboard-header {
  background: white; border-radius: 12px; padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 12px;
}
.header-left h3 { margin: 0 0 8px; font-size: 18px; }
.header-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.header-actions { display: flex; gap: 8px; }

.frame-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;
}
@media (max-width: 900px) { .frame-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .frame-grid { grid-template-columns: 1fr; } }

.loading-section {
  display: flex; flex-direction: column; align-items: center;
  padding: 60px 20px; color: #909399;
}
.large-icon { font-size: 40px; color: #409eff; margin-bottom: 16px; }
.spinning { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.video-section {
  background: white; border-radius: 12px; padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.video-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
}
.video-header h3 { margin: 0; color: #67c23a; }
.elapsed { color: #909399; font-size: 14px; }
.video-player-wrap { border-radius: 8px; overflow: hidden; background: #000; }
.video-player { width: 100%; max-height: 540px; display: block; }
.video-actions { display: flex; justify-content: center; gap: 12px; margin-top: 16px; }
</style>
