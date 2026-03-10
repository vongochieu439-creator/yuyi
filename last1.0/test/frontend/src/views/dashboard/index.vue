<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goCreate() {
  router.push('/script-creator')
}
</script>

<template>
  <div class="dash-wrap">
    <div class="dash-inner">
      <!-- Hero -->
      <div class="dash-hero">
        <div class="dash-hero-t"><span>Wing AI</span> · 一站式内容创作</div>
        <div class="dash-hero-d">从脚本创作到数字人生成，从排期发布到数据复盘，全链路AI赋能</div>
      </div>

      <!-- Bento Grid -->
      <div class="bento">
        <!-- AI创作 - main hero card -->
        <div class="bn-main">
          <div class="bn-main-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            核心功能
          </div>
          <div class="bn-main-t">智能创作</div>
          <div class="bn-main-d">AI一键生成爆款短视频脚本，从灵感到分镜全流程覆盖</div>
          <div class="bn-modes">
            <div class="bn-mode" @click="goCreate()">
              <div class="bn-mode-ic">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
              </div>
              <div class="bn-mode-t">快速模式</div>
              <div class="bn-mode-d">30秒生成脚本，填写信息即可</div>
            </div>
            <div class="bn-mode" @click="goCreate()">
              <div class="bn-mode-ic">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><line x1="12" y1="7" x2="12" y2="11"/></svg>
              </div>
              <div class="bn-mode-t">深度定制</div>
              <div class="bn-mode-d">AI顾问对话式深度挖掘需求</div>
            </div>
          </div>
        </div>

        <!-- IP工作室 -->
        <div class="bn-card bn-ip" @click="router.push('/ip-studio')">
          <div class="bn-card-top">
            <div class="bn-card-ic">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </div>
            <div class="bn-card-nm">IP工作室</div>
            <div class="bn-card-arrow">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </div>
          </div>
          <div class="bn-card-d">AI深度访谈生成专属人设，让脚本带有你的个人风格</div>
          <div class="bn-card-tags">
            <span>AI访谈</span><span>人设画像</span><span>风格融合</span>
          </div>
        </div>

        <!-- 模板库 -->
        <div class="bn-card bn-tmpl" @click="router.push('/templates')">
          <div class="bn-card-top">
            <div class="bn-card-ic">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
            </div>
            <div class="bn-card-nm">模板库</div>
            <div class="bn-card-arrow">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </div>
          </div>
          <div class="bn-card-d">50+爆款脚本模板，一键复用千万级变现逻辑</div>
          <div class="bn-card-tags">
            <span>KOL风格</span><span>营销方法论</span><span>行业专属</span>
          </div>
        </div>

        <!-- 爆款深度解析 -->
        <div class="bn-card bn-hot" @click="router.push('/hotbreak')">
          <div class="bn-card-top">
            <div class="bn-card-ic">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </div>
            <div class="bn-card-nm">爆款深度解析</div>
            <div class="bn-card-arrow">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </div>
          </div>
          <div class="bn-card-d">一键提取爆款视频文案，深度拆解脚本结构，生成复刻脚本</div>
          <div class="bn-card-tags">
            <span>视频结构</span><span>情绪曲线</span><span>爆款逻辑</span>
          </div>
        </div>

        <!-- 360° 定位 -->
        <div class="bn-card bn-pos" @click="router.push('/pos360')">
          <div class="bn-card-top">
            <div class="bn-card-ic">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
            </div>
            <div class="bn-card-nm">360° 行业定位分析</div>
            <div class="bn-card-arrow">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </div>
          </div>
          <div class="bn-card-d">AI帮你找准内容方向，分析竞品策略</div>
          <div class="bn-card-tags">
            <span>用户需求</span><span>竞品拆解</span><span>内容策略</span>
          </div>
        </div>
      </div>

      <!-- Recent projects section -->
      <div style="margin-top: 32px;">
        <div class="sh">
          <div class="sh-t">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            最近项目
          </div>
          <div class="sh-l" @click="router.push('/project-list')">
            查看全部
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
        </div>
        <div class="pg">
          <div v-for="p in recentProjects" :key="p.id" class="pj fn" @click="router.push('/script-creator')">
            <div class="pj-tp">
              <span class="pj-tg">{{ p.tmpl }}</span>
              <span class="pj-s" :class="p.status">{{ p.st }}</span>
            </div>
            <div class="pj-t">{{ p.title }}</div>
            <div class="pj-d">{{ p.desc }}</div>
            <div class="pj-m">
              <span class="pj-mi">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                {{ p.date }}
              </span>
              <span class="pj-mi">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                {{ p.shots }}个镜头
              </span>
            </div>
          </div>

          <!-- New project card -->
          <div class="pj fn" style="border-style:dashed;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;min-height:120px;" @click="router.push('/script-creator')">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--t3)" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            <span style="font-size:12px;color:var(--t3);font-weight:500;">新建项目</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  data() {
    return {
      recentProjects: [
        { id: 1, title: '玻尿酸面膜 · 种草视频', desc: '实验对比型 · 60秒', status: 'done',     st: '已完成', tmpl: '实验对比型', date: '3天前', shots: 8 },
        { id: 2, title: '美白精华 · 测评脚本',   desc: '专家测评型 · 45秒', status: 'progress', st: '生成中', tmpl: '专家测评型', date: '1天前', shots: 12 },
        { id: 3, title: '胶原蛋白粉 · 痛点故事', desc: '痛点故事型 · 50秒', status: 'draft',    st: '草稿',   tmpl: '痛点故事型', date: '5天前', shots: 10 },
      ],
    }
  },
}
</script>
