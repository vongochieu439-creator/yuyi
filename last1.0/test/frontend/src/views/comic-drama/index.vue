<script setup lang="ts">
import { ref } from 'vue'
import { ArrowLeft, VideoPlay, Refresh } from '@element-plus/icons-vue'
import { useComicDramaStore } from '../../stores/comicDrama'
import StyleSelector from './components/StyleSelector.vue'
import GenerationProgress from './components/GenerationProgress.vue'

const store = useComicDramaStore()
const videoRef = ref<HTMLVideoElement | null>(null)

const examples = [
  '末日少年觉醒超能力，独自对抗入侵的暗影军团',
  '古代女将军在战场上以少胜多的传奇故事',
  '一只流浪猫在城市中寻找温暖的家的奇幻旅程',
  '赛博朋克都市中AI觉醒自我意识的故事',
]

const fillExample = (text: string) => {
  store.userInput = text
}

const handleGenerate = () => {
  store.startGeneration()
}
</script>

<template>
  <div class="page-centered">
    <!-- Header -->
    <div class="list-header">
      <el-button @click="$router.push('/')" :icon="ArrowLeft">返回</el-button>
      <h2>AI漫剧一键生成</h2>
      <el-button v-if="store.step !== 'input'" @click="store.reset()" :icon="Refresh" type="info" plain>
        重新开始
      </el-button>
    </div>

    <!-- 输入区域 -->
    <div v-if="store.step === 'input' || !store.generating && store.step === 'error'" class="input-section">
      <div class="input-card">
        <h3>故事概念</h3>
        <el-input
          v-model="store.userInput"
          type="textarea"
          :rows="3"
          placeholder="输入你的故事概念，例如：末日少年觉醒超能力..."
          maxlength="200"
          show-word-limit
          :disabled="store.generating"
        />
        <div class="examples">
          <span class="examples-label">灵感:</span>
          <el-tag
            v-for="(ex, i) in examples"
            :key="i"
            class="example-tag"
            effect="plain"
            @click="fillExample(ex)"
          >
            {{ ex.slice(0, 15) }}...
          </el-tag>
        </div>
      </div>

      <div class="input-card">
        <h3>视觉风格</h3>
        <StyleSelector v-model="store.style" />
      </div>

      <div class="generate-btn-wrap">
        <el-button
          type="primary"
          size="large"
          :loading="store.generating"
          :disabled="!store.userInput.trim()"
          @click="handleGenerate"
          class="generate-btn"
        >
          <VideoPlay v-if="!store.generating" style="margin-right:6px" />
          {{ store.generating ? '生成中...' : '一键生成漫剧' }}
        </el-button>
      </div>

      <!-- 错误提示 -->
      <el-alert
        v-if="store.errorMessage"
        :title="store.errorMessage"
        type="error"
        show-icon
        closable
        style="margin-top: 16px;"
      />
    </div>

    <!-- 生成进度 -->
    <GenerationProgress v-if="store.step !== 'input'" />

    <!-- 视频播放器 -->
    <div v-if="store.step === 'done' && store.videoUrl" class="video-section">
      <div class="video-header">
        <h3>生成完成!</h3>
        <span class="elapsed">用时 {{ store.elapsedSeconds }}s</span>
      </div>
      <div class="video-player-wrap">
        <video
          ref="videoRef"
          :src="store.videoUrl"
          controls
          autoplay
          class="video-player"
        ></video>
      </div>
      <div class="video-actions">
        <el-button type="primary" @click="handleGenerate">再来一个</el-button>
        <el-button @click="store.reset()">重新开始</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-centered {
  max-width: 960px;
  margin: 0 auto;
  padding: 20px;
}
.list-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.list-header h2 { flex: 1; margin: 0; }

.input-section { display: flex; flex-direction: column; gap: 20px; }
.input-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.input-card h3 { margin: 0 0 12px; font-size: 16px; color: #303133; }

.examples {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
}
.examples-label { font-size: 13px; color: #909399; }
.example-tag { cursor: pointer; }
.example-tag:hover { color: #409eff; border-color: #409eff; }

.generate-btn-wrap { text-align: center; padding: 8px 0; }
.generate-btn {
  min-width: 240px;
  height: 48px;
  font-size: 16px;
  border-radius: 24px;
}

.video-section {
  margin-top: 24px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.video-header h3 { margin: 0; color: #67c23a; }
.elapsed { color: #909399; font-size: 14px; }

.video-player-wrap {
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}
.video-player {
  width: 100%;
  max-height: 540px;
  display: block;
}

.video-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
}
</style>
