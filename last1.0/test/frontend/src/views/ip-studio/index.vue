<script setup lang="ts">
import { onMounted } from 'vue'
import { useIPStudioStore } from '../../stores/ipStudio'
import InterviewChat from './components/InterviewChat.vue'
import VoiceInterview from './components/VoiceInterview.vue'
import Workspace from './components/Workspace.vue'
import ScriptView from './components/ScriptView.vue'

const store = useIPStudioStore()
onMounted(() => store.loadProfiles())
</script>

<template>
  <div class="sc">
    <div class="ipc2">
      <!-- List view: show IP profile overview -->
      <template v-if="store.currentView === 'list'">
        <div class="iph">
          <div class="iph-a">IP</div>
          <div class="iph-n">我的创作者人设</div>
          <div class="iph-d">基于AI访谈生成的个性化IP画像，自动融入脚本创作</div>
          <div class="iph-ts">
            <span v-for="t in ['专业测评','亲和力强','干货分享','真实体验','数据说话']" :key="t" class="iph-t">{{ t }}</span>
          </div>
          <div class="iph-ac">
            <button class="bt bt-p" @click="store.goToView('interview')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/></svg>
              重新访谈
            </button>
            <button class="bt bt-g">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              手动编辑
            </button>
          </div>
        </div>
        <div class="ips">
          <div class="ips-t">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            人设基本信息
          </div>
          <div class="ipg">
            <div v-for="x in profileFields" :key="x.l" class="ipi">
              <div class="ipi-l">{{ x.l }}</div>
              <div class="ipi-v">{{ x.v }}</div>
            </div>
          </div>
        </div>
        <div class="ips">
          <div class="ips-t">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z"/></svg>
            创作偏好
          </div>
          <div style="font-size:12px;color:var(--t2);line-height:1.8;">
            <p style="margin-bottom:8px;">开头习惯用反问句或痛点切入，善于用数据对比突出产品优势。文案风格偏口语化。</p>
            <p>结尾通常以限时优惠或个人推荐作为转化钩子，偏好30-60秒的短视频节奏。</p>
          </div>
        </div>
        <div class="ips">
          <div class="ips-t">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            IP应用效果
          </div>
          <div class="ipg">
            <div v-for="x in statsFields" :key="x.l" class="ipi">
              <div class="ipi-l">{{ x.l }}</div>
              <div class="ipi-v" style="color:var(--p);font-weight:700;">{{ x.v }}</div>
            </div>
          </div>
        </div>
      </template>

      <!-- Other views: delegate to existing components -->
      <InterviewChat v-else-if="store.currentView === 'interview'" />
      <VoiceInterview v-else-if="store.currentView === 'voice'" />
      <Workspace v-else-if="store.currentView === 'detail' || store.currentView === 'topics'" />
      <ScriptView v-else-if="store.currentView === 'script' || store.currentView === 'feedback'" />
    </div>
  </div>
</template>

<script lang="ts">
export default {
  data() {
    return {
      profileFields: [
        { l: '表达风格', v: '轻松幽默、接地气' },
        { l: '专业领域', v: '美妆护肤、个人护理' },
        { l: '目标受众', v: '18-35岁女性用户' },
        { l: '内容调性', v: '真实测评+干货分享' },
        { l: '常用平台', v: '抖音、小红书' },
        { l: '视频风格', v: '对镜口播+实测对比' },
      ],
      statsFields: [
        { l: 'IP融合脚本数', v: '18个' },
        { l: '平均匹配度',   v: '92%' },
        { l: '完播率提升',   v: '+15%' },
        { l: '转化率提升',   v: '+8%' },
      ],
    }
  },
}
</script>
