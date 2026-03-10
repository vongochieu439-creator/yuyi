<script setup lang="ts">
import { ref } from 'vue'

const histTab = ref(0)
</script>

<template>
  <div class="hist-wrap">
    <div class="hist-hd">
      <div class="hist-hd-t">内容库</div>
      <div class="hist-hd-d">管理与回顾您的选题、脚本与视频，每一份创意都值得精准留存</div>
    </div>
    <div class="hist-tabs">
      <button v-for="(t, i) in ['选题', '脚本', '视频']" :key="i"
        class="hist-tab" :class="{ on: histTab === i }" @click="histTab = i">{{ t }}</button>
    </div>
    <div class="hist-empty">
      <div style="font-size:40px;margin-bottom:12px;opacity:.3;">
        {{ histTab === 0 ? '💡' : histTab === 1 ? '📝' : '🎬' }}
      </div>
      <div style="font-size:14px;font-weight:600;color:var(--t2);margin-bottom:4px;">
        暂无{{ ['选题', '脚本', '视频'][histTab] }}
      </div>
      <div style="font-size:12px;color:var(--t3);">去 AI 创作 生成你的第一个内容吧</div>
    </div>
  </div>
</template>
