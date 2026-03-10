<script setup lang="ts">
import { computed } from 'vue'
import { useComicDramaStore } from '../../../stores/comicDrama'

const store = useComicDramaStore()

const progressPercent = computed(() => {
  const total = store.storyboard?.scenes.length || 6
  switch (store.step) {
    case 'input': return 5
    case 'storyboard': return 10
    case 'images': {
      const count = Object.keys(store.imageUrls).length
      return 10 + Math.round((count / total) * 25)
    }
    case 'video_gen': {
      const vcount = store.videoGenCount || 0
      return 35 + Math.round((vcount / total) * 45)
    }
    case 'composing': return 85
    case 'done': return 100
    default: return 0
  }
})

const stepLabels = [
  { key: 'storyboard', label: '剧本创作' },
  { key: 'images', label: '画面生成' },
  { key: 'video_gen', label: '视频生成' },
  { key: 'composing', label: '合成输出' },
  { key: 'done', label: '完成' },
]

const currentStepIdx = computed(() => {
  const map: Record<string, number> = { input: 0, storyboard: 0, images: 1, video_gen: 2, composing: 3, done: 4 }
  return map[store.step] ?? 0
})
</script>

<template>
  <div class="gen-progress">
    <!-- 进度条 -->
    <div class="progress-bar-wrap">
      <div class="progress-bar" :style="{ width: progressPercent + '%' }"></div>
    </div>
    <div class="progress-text">{{ store.progress }}</div>

    <!-- 步骤指示器 -->
    <div class="steps">
      <div
        v-for="(s, i) in stepLabels"
        :key="s.key"
        class="step-item"
        :class="{ active: i === currentStepIdx, done: i < currentStepIdx }"
      >
        <div class="step-dot">{{ i < currentStepIdx ? '✓' : i + 1 }}</div>
        <span class="step-label">{{ s.label }}</span>
      </div>
    </div>

    <!-- 分镜卡片 -->
    <div v-if="store.storyboard" class="storyboard-section">
      <h3 class="section-title">{{ store.storyboard.title }}</h3>
      <div class="scene-grid">
        <div
          v-for="scene in store.storyboard.scenes"
          :key="scene.scene_id"
          class="scene-card"
        >
          <div class="scene-image-wrap">
            <img
              v-if="store.imageUrls[scene.scene_id]"
              :src="store.imageUrls[scene.scene_id]"
              class="scene-image"
              :alt="'场景' + scene.scene_id"
            />
            <div v-else class="scene-skeleton">
              <div class="skeleton-pulse"></div>
              <span class="skeleton-text">{{ store.generating ? '生成中...' : '等待' }}</span>
            </div>
          </div>
          <div class="scene-info">
            <span class="scene-id">#{{ scene.scene_id }}</span>
            <span class="scene-camera">{{ scene.camera }}</span>
          </div>
          <p class="scene-narration">{{ scene.narration }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.gen-progress { margin-top: 20px; }
.progress-bar-wrap {
  height: 6px;
  background: #e4e7ed;
  border-radius: 3px;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 3px;
  transition: width 0.5s ease;
}
.progress-text {
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
  text-align: center;
}
.steps {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin: 20px 0;
}
.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.step-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e4e7ed;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s;
}
.step-item.active .step-dot {
  background: #409eff;
  color: white;
  box-shadow: 0 2px 8px rgba(64,158,255,0.4);
}
.step-item.done .step-dot {
  background: #67c23a;
  color: white;
}
.step-label { font-size: 12px; color: #909399; }
.step-item.active .step-label { color: #409eff; font-weight: 600; }
.step-item.done .step-label { color: #67c23a; }

.section-title {
  text-align: center;
  font-size: 20px;
  margin: 16px 0;
  color: #303133;
}

.scene-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 12px;
}
.scene-card {
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  overflow: hidden;
  background: white;
  transition: transform 0.3s;
}
.scene-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }

.scene-image-wrap {
  width: 100%;
  aspect-ratio: 16/9;
  overflow: hidden;
  background: #f0f0f0;
}
.scene-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  animation: fadeIn 0.6s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: scale(1.05); } to { opacity: 1; transform: scale(1); } }

.scene-skeleton {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}
.skeleton-pulse {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: pulse 1.5s infinite;
}
@keyframes pulse { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.skeleton-text { position: relative; z-index: 1; font-size: 12px; color: #c0c4cc; }

.scene-info {
  display: flex;
  justify-content: space-between;
  padding: 6px 10px;
  font-size: 12px;
}
.scene-id { color: #409eff; font-weight: 600; }
.scene-camera { color: #909399; background: #f5f7fa; padding: 1px 6px; border-radius: 4px; }
.scene-narration {
  padding: 0 10px 10px;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  margin: 0;
}
</style>
