<script setup lang="ts">
const props = defineProps<{
  phases: Array<{ key: string; label: string; desc: string }>
  currentPhase: string
  theme?: 'warm' | 'voice'
}>()

const phaseOrder = (phase: string) => {
  return props.phases.findIndex(p => p.key === phase)
}
</script>

<template>
  <div class="phase-progress">
    <div v-for="(phase, idx) in phases" :key="phase.key" class="phase-item">
      <div
        class="phase-dot"
        :class="{
          active: currentPhase === phase.key && theme !== 'voice',
          done: phaseOrder(currentPhase) > idx,
          'voice-active': currentPhase === phase.key && theme === 'voice'
        }"
      >
        {{ phaseOrder(currentPhase) > idx ? '✓' : (idx + 1) }}
      </div>
      <div class="phase-info">
        <div
          class="phase-label"
          :class="{
            active: currentPhase === phase.key && theme !== 'voice',
            done: phaseOrder(currentPhase) > idx,
            'voice-active': currentPhase === phase.key && theme === 'voice'
          }"
        >{{ phase.label }}</div>
        <div class="phase-desc">{{ phase.desc }}</div>
      </div>
      <div v-if="idx < phases.length - 1" class="phase-line" />
    </div>
  </div>
</template>
