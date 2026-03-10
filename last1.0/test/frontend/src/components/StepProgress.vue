<script setup lang="ts">
defineProps<{
  steps: string[]
  currentStep: number
  loading?: boolean
  title?: string
}>()
</script>

<template>
  <div style="text-align: center; padding: 60px; background: #fffbeb; border-radius: 12px;">
    <el-icon v-if="loading" class="is-loading" :size="50" style="color: #f59e0b;"><Loading /></el-icon>
    <h3 v-if="title" style="margin-top: 16px; color: #92400e;">{{ title }}</h3>
    <div style="display: flex; justify-content: center; gap: 24px; margin-top: 16px;">
      <div v-for="(step, i) in steps" :key="i" style="display: flex; align-items: center; gap: 6px;">
        <div :style="{
          width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '11px', fontWeight: 'bold',
          background: currentStep > i ? '#10b981' : (currentStep === i ? '#f59e0b' : '#e5e7eb'),
          color: currentStep >= i ? 'white' : '#909399'
        }">{{ currentStep > i ? '✓' : (i + 1) }}</div>
        <span :style="{ fontSize: '12px', color: currentStep === i ? '#92400e' : '#909399' }">{{ step }}</span>
      </div>
    </div>
  </div>
</template>
