<script setup lang="ts">
import { ref } from 'vue'

const anaTab = ref(2)
</script>

<template>
  <div class="ana-wrap">
    <div class="ana-hd">
      <div>
        <div class="ana-hd-t">账号资产管理</div>
        <div class="ana-hd-d">当前已同步 0 个社交平台账号，AI 将为您实时监控数据。</div>
      </div>
      <div class="ana-hd-acts">
        <button class="ana-hd-btn">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          数据刷新
        </button>
        <button class="ana-hd-btn">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          登录器下载
        </button>
        <button class="ana-hd-btn pri">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          添加账号
        </button>
      </div>
    </div>

    <div class="ana-tabs">
      <button v-for="(t, i) in ['平台账号连接','团队成员管理','全团队业绩看板']" :key="i"
        class="ana-tab" :class="{ on: anaTab === i }" @click="anaTab = i">{{ t }}</button>
    </div>

    <!-- Tab 0: Platform connect -->
    <div v-if="anaTab === 0" class="ana-connect" style="margin-top:20px;">
      <div class="ana-connect-ic">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      </div>
      <div class="ana-connect-t">点击关联更多平台账号</div>
      <div class="ana-connect-d">支持抖音、快手、视频号等主流平台</div>
    </div>

    <!-- Tab 1: Team members -->
    <div v-else-if="anaTab === 1">
      <div class="ana-team-hd">
        <div class="ana-team-t">团队成员 <span class="ana-team-ct">(0)</span></div>
        <div class="ana-team-r">
          <input class="ana-team-search" placeholder="搜索成员姓名或邮箱..." />
          <button class="ana-hd-btn pri">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            邀请新成员
          </button>
        </div>
      </div>
      <div style="text-align:center;padding:60px;color:var(--t3);font-size:13px;">暂无成员</div>
    </div>

    <!-- Tab 2: Team dashboard -->
    <div v-else>
      <div class="ana-dash-hd">
        <div class="ana-dash-t">团队业绩看板</div>
        <div class="ana-live">数据实时更新中</div>
      </div>
      <div class="ana-filters">
        <div class="ana-fil">👥 团队成员：全队 (12人)</div>
        <div class="ana-fil">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          时间范围：2026年3月
        </div>
        <div class="ana-fil">全平台</div>
      </div>

      <div class="ana-stats">
        <div v-for="s in stats" :key="s.label" class="ana-stat">
          <div class="ana-stat-top">
            <span class="ana-stat-l">{{ s.label }}</span>
            <span class="ana-stat-badge g">{{ s.badge }}</span>
          </div>
          <div class="ana-stat-v">{{ s.value }}</div>
          <div class="ana-stat-sub">较上周期 {{ s.sub }}</div>
        </div>
      </div>

      <div class="ana-body">
        <div class="ana-chart">
          <div class="ana-chart-hd">
            <div class="ana-chart-t">成员绩效对比</div>
            <div class="ana-chart-legend">
              <span class="cl-pub">发布量</span>
              <span class="cl-exp">曝光量</span>
            </div>
          </div>
          <div v-for="m in members" :key="m.nm" class="ana-bar-row">
            <div class="ana-bar-nm">{{ m.nm }}</div>
            <div class="ana-bar-track"><div class="ana-bar-fill" :style="{ width: m.w }" /></div>
            <div class="ana-bar-grade">{{ m.g }}</div>
          </div>
        </div>

        <div class="ana-ai">
          <div class="ana-ai-card">
            <div class="ana-ai-hd">
              <div class="ana-ai-ic">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z"/></svg>
              </div>
              <div class="ana-ai-t">AI 效能点评</div>
            </div>
            <div class="ana-ai-body">
              <p style="margin-bottom:8px;">AI 洞察：本月成员张三发布的视频曝光量显著高于平均值 <span class="ana-ai-hl">15.2%</span>。</p>
              <p>数据表明，其在视频前3秒使用了"悬念式提问"技巧，有效提升了完播率。</p>
              <div class="ana-ai-tip">
                <div class="ana-ai-tip-l">建议行动</div>
                建议全队在下周例会复盘其脚本结构，并尝试复制该模式。
              </div>
            </div>
          </div>
          <div class="ana-ai-card">
            <div class="ana-pred-t">下月预测</div>
            <div class="ana-pred-d">基于当前趋势，预计下月总曝光量将突破 3.0M</div>
            <button class="ana-pred-btn">查看预测模型</button>
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
      stats: [
        { label: '本月发布', badge: '0%', value: '0', sub: '+0%' },
        { label: '总曝光量', badge: '0%', value: '0', sub: '+0%' },
        { label: '平均互动率', badge: '0%', value: '0%', sub: '+0%' },
        { label: '团队效率', badge: '0%', value: '0%', sub: '+0%' },
      ],
      members: [
        { nm: '张三', w: '85%', g: 'A+' },
        { nm: '李四', w: '65%', g: 'B' },
        { nm: '王五', w: '50%', g: 'B+' },
        { nm: '刘明', w: '35%', g: 'C' },
      ],
    }
  },
}
</script>
