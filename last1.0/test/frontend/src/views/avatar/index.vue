<script setup lang="ts">
import { ref } from 'vue'

const avSel = ref(0)
const avTheme = ref('')
const avScript = ref('')
const avType = ref('数字人口播')
const avScreen = ref('竖屏')
const avDur = ref('15s-30s')

const avatars = [
  { nm: '商务男', tags: '商务 | 正式 | 专业', res: '2K' },
  { nm: '知性女', tags: '知性 | 优雅 | 职场', pro: true },
  { nm: '活力少女', tags: '青春 | 活泼 | 亲和', res: '2K' },
  { nm: '儒雅大叔', tags: '稳重 | 信赖 | 权威', res: '4K' },
  { nm: '甜美主播', tags: '甜美 | 种草 | 带货', pro: true },
]
</script>

<template>
  <div class="av-wrap">
    <!-- Left: avatar selection -->
    <div class="av-left">
      <div class="av-left-t">选择数字人</div>
      <div v-for="(av, i) in avatars" :key="i" class="av-card" :class="{ on: avSel === i }" @click="avSel = i">
        <div class="av-card-img">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--t3)" stroke-width="1.5" style="opacity:.4"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span v-if="av.res" class="av-res">{{ av.res }}</span>
          <span v-if="av.pro" class="av-pro">Pro</span>
        </div>
        <div class="av-card-info">
          <div class="av-card-nm">{{ av.nm }}</div>
          <div class="av-card-tags">{{ av.tags }}</div>
        </div>
      </div>
    </div>

    <!-- Center: phone preview -->
    <div class="av-center">
      <div class="av-phone" :class="{ landscape: avScreen === '横屏' }">
        <div class="av-phone-inner">
          <div v-if="avScreen === '竖屏'" class="av-phone-notch" />
          <div class="av-phone-play">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--t2)" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
          </div>
          <div class="av-phone-bar" />
        </div>
      </div>
    </div>

    <!-- Right: config -->
    <div class="av-right">
      <div class="av-right-t">视频配置</div>
      <div class="av-right-d">自定义您的数字人视频内容</div>

      <div class="av-fg">
        <div class="av-fg-l">视频主题</div>
        <input class="av-inp" v-model="avTheme" placeholder="例如：2024年Q3季度财报分析..." />
      </div>

      <div class="av-fg">
        <div class="av-fg-l">
          口播文案
          <span class="av-fg-tag">AI 润色</span>
        </div>
        <textarea class="av-inp" rows="5" v-model="avScript" placeholder="请输入或粘贴您的脚本文案，AI将根据文本自动生成口型和表情..." style="resize:vertical;" />
        <div style="text-align:right;font-size:10px;color:var(--t3);margin-top:4px;">{{ avScript.length }} / 2000 字</div>
      </div>

      <button class="av-ai-btn">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z"/></svg>
        AI 生成文案
      </button>

      <div class="av-row">
        <div class="av-fg">
          <div class="av-fg-l">数字人类型</div>
          <select class="av-sel" v-model="avType">
            <option>数字人口播</option><option>数字人对话</option><option>数字人讲解</option>
          </select>
        </div>
        <div class="av-fg">
          <div class="av-fg-l">屏幕模式</div>
          <div class="av-screen-btns">
            <button class="av-scr" :class="{ on: avScreen === '竖屏' }" @click="avScreen = '竖屏'">📱 竖屏</button>
            <button class="av-scr" :class="{ on: avScreen === '横屏' }" @click="avScreen = '横屏'">🖥 横屏</button>
          </div>
        </div>
      </div>

      <div class="av-fg">
        <div class="av-fg-l">视频时长</div>
        <select class="av-sel" v-model="avDur">
          <option>15s-30s</option><option>30s-60s</option><option>60s-120s</option><option>120s-180s</option>
        </select>
      </div>

      <div class="av-bottom">
        <button class="av-b ghost">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          重新生成
        </button>
        <button class="av-b primary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          生成视频
        </button>
      </div>
    </div>
  </div>
</template>
