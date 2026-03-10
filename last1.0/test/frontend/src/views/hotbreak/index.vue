<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const hotLink = ref('')
const hotIndustry = ref('')
const hotProduct = ref('')
const hotReq = ref('')
</script>

<template>
  <div class="sc">
    <div class="tool-pg">
      <div style="margin-bottom:20px;">
        <span style="font-size:12px;color:var(--t3);cursor:pointer;display:inline-flex;align-items:center;gap:4px;" @click="router.push('/dashboard')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
          返回工作台
        </span>
      </div>

      <div class="tool-hd blue">
        <div class="tool-hd-t">爆款深度解析</div>
        <div class="tool-hd-d">一键提取爆款视频文案，深度拆解脚本结构，生成复刻脚本</div>
      </div>

      <div class="tool-form">
        <div class="tool-fg">
          <div class="tool-fg-l">请粘贴抖音分享链接（完整分享链接） <span class="rq">*</span></div>
          <input class="tool-inp" v-model="hotLink" placeholder="请粘贴抖音分享链接（完整分享链接）" />
        </div>
        <div class="tool-row">
          <div class="tool-fg">
            <div class="tool-fg-l">所属行业</div>
            <select class="tool-sel" v-model="hotIndustry">
              <option value="">选择目标行业</option>
              <option>美妆护肤</option><option>食品保健</option>
              <option>数码3C</option><option>教育培训</option>
              <option>服装鞋包</option><option>家居生活</option>
            </select>
          </div>
          <div class="tool-fg">
            <div class="tool-fg-l">你的产品/服务是什么？</div>
            <input class="tool-inp" v-model="hotProduct" placeholder="例如：补水保湿面膜 / 线上英语课程" />
          </div>
        </div>
        <div class="tool-fg">
          <div class="tool-fg-l">对改写脚本的具体要求</div>
          <textarea class="tool-inp" rows="4" v-model="hotReq" placeholder="例如：30秒以内、适合信息流投放、语气专业可信、突出痛点和解决方案等" style="resize:vertical;" />
        </div>
        <button class="tool-btn blue">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          生成爆款拆解报告
        </button>
        <div class="tool-hint">AI将为您深度分析视频结构、情绪曲线及爆款逻辑，并生成6份优化脚本<br>支持抖音和小红书分享链接</div>
      </div>

      <div class="tool-empty">
        <div class="tool-empty-ic">📊</div>
        <div class="tool-empty-t">粘贴视频链接，开始拆解爆款密码</div>
        <div class="tool-empty-d">分析结果将在此处展示</div>
      </div>
    </div>
  </div>
</template>
