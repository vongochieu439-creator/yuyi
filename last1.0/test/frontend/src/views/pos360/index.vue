<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const posMain = ref('')
const posInd = ref('')
const posDepth = ref('standard')
const posDouyinLink = ref('')
const posCompLinks = ref('')
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

      <div class="tool-hd purple">
        <div class="tool-hd-t">360° 行业定位分析</div>
        <div class="tool-hd-d">输入你的行业，AI帮你搞清楚：客户在抖音上想看什么、谁做得好、什么内容能带来生意</div>
      </div>

      <div class="tool-form">
        <div class="tool-fg">
          <div class="tool-fg-l">你的主要业务 <span class="rq">*</span></div>
          <input class="tool-inp" v-model="posMain" placeholder="请输入你的主要业务，例如：美妆护肤、健身私教、咖啡馆等" />
        </div>
        <div class="tool-row">
          <div class="tool-fg">
            <div class="tool-fg-l">所属行业</div>
            <select class="tool-sel" v-model="posInd">
              <option value="">选择目标行业</option>
              <option>美妆护肤</option><option>食品保健</option>
              <option>数码3C</option><option>教育培训</option>
              <option>服装鞋包</option><option>家居生活</option>
            </select>
            <input class="tool-inp" style="margin-top:6px;" placeholder="或输入自定义行业，如：新茶饮" />
          </div>
          <div class="tool-fg">
            <div class="tool-fg-l">分析深度 <span class="rq">*</span></div>
            <div style="display:flex;gap:6px;">
              <button
                v-for="d in [{k:'fast',l:'快速'},{k:'standard',l:'标准版'},{k:'deep',l:'深度'}]"
                :key="d.k"
                class="tool-hd-tag"
                :class="{ on: posDepth === d.k }"
                @click="posDepth = d.k"
              >{{ d.l }}</button>
            </div>
          </div>
        </div>
        <div class="tool-row">
          <div class="tool-fg">
            <div class="tool-fg-l">你的抖音主页链接</div>
            <input class="tool-inp" v-model="posDouyinLink" placeholder="例如：https://www.douyin.com/user/xxxxxx" />
          </div>
        </div>
        <div class="tool-fg">
          <div class="tool-fg-l">竞品抖音链接（选填）</div>
          <textarea class="tool-inp" rows="3" v-model="posCompLinks" placeholder="可填写1~3个竞品抖音视频或主页链接，每行一个" style="resize:vertical;" />
        </div>
        <button class="tool-btn purple">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
          开始定位分析
        </button>
      </div>

      <div class="tool-empty">
        <div class="tool-empty-ic">🎯</div>
        <div class="tool-empty-t">请先填写你的主要业务，选择行业与分析深度</div>
        <div class="tool-empty-d">例如：主要业务"线下皮肤管理工作室" + 行业"美妆/护肤" + 分析深度"标准版"</div>
      </div>
    </div>
  </div>
</template>
