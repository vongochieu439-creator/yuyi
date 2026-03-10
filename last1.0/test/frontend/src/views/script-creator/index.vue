<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useScriptCreatorStore } from '../../stores/scriptCreator'
import ProductInput from './components/ProductInput.vue'
import ResearchProgress from './components/ResearchProgress.vue'
import ScriptSelector from './components/ScriptSelector.vue'
import ScriptPolish from './components/ScriptPolish.vue'
import StoryboardPreview from './components/StoryboardPreview.vue'
import VideoProduction from './components/VideoProduction.vue'
import CompletionView from './components/CompletionView.vue'

const store = useScriptCreatorStore()
const route = useRoute()

onMounted(() => {
  const tid = route.query.template_id as string
  if (tid) store.selectedTemplate = { id: tid } as any
})

const stepLabels = ['产品信息', '生成脚本', '选择脚本', '脚本打磨', '分镜预览', '视频生成', '完成']
</script>

<template>
  <div class="page-wrap">
    <div class="page-centered">
      <!-- Wizard header -->
      <div class="wizard-header">
        <h2>AI 脚本创作</h2>

        <!-- Step indicator (styled to match new design) -->
        <div class="sc-steps">
          <template v-for="(label, idx) in stepLabels" :key="idx">
            <div
              class="sc-step"
              :class="{
                done: store.step > idx,
                active: store.step === idx,
              }"
            >
              <div class="sc-step-dot">
                <svg v-if="store.step > idx" width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span v-else>{{ idx + 1 }}</span>
              </div>
              <span class="sc-step-label">{{ label }}</span>
            </div>
            <div v-if="idx < stepLabels.length - 1" class="sc-step-line" :class="{ done: store.step > idx }" />
          </template>
        </div>
      </div>

      <!-- Step views -->
      <ProductInput       v-if="store.step === 0" />
      <ResearchProgress   v-else-if="store.step === 1" />
      <ScriptSelector     v-else-if="store.step === 2" />
      <ScriptPolish       v-else-if="store.step === 3" />
      <StoryboardPreview  v-else-if="store.step === 4" />
      <VideoProduction    v-else-if="store.step === 5" />
      <CompletionView     v-else-if="store.step >= 6" />
    </div>
  </div>
</template>

<style scoped>
.sc-steps {
  display: flex;
  align-items: center;
  gap: 0;
  flex-wrap: wrap;
}

.sc-step {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sc-step-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid var(--b);
  background: var(--s);
  color: var(--t3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  transition: all .25s ease;
}

.sc-step.active .sc-step-dot {
  background: var(--p);
  border-color: var(--p);
  color: #fff;
  box-shadow: 0 0 0 4px var(--pg);
}

.sc-step.done .sc-step-dot {
  background: var(--g);
  border-color: var(--g);
  color: #fff;
}

.sc-step-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--t3);
  white-space: nowrap;
  transition: color .25s;
}

.sc-step.active .sc-step-label { color: var(--p); font-weight: 700; }
.sc-step.done   .sc-step-label { color: var(--g); }

.sc-step-line {
  width: 24px;
  height: 2px;
  background: var(--b);
  flex-shrink: 0;
  margin: 0 4px;
  border-radius: 1px;
  transition: background .25s;
}

.sc-step-line.done { background: var(--g); }
</style>
