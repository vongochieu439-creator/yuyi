<script setup lang="ts">
import type { CostEstimate } from '../../../stores/storyboard'

defineProps<{
  cost: CostEstimate | null
  loading?: boolean
}>()
</script>

<template>
  <div class="cost-panel" v-if="cost">
    <h4>成本估算</h4>
    <div class="cost-items">
      <div class="cost-item">
        <span class="cost-label">分镜图 ({{ cost.image_count }}张 x ¥{{ cost.image_unit_cost }})</span>
        <span class="cost-value">¥{{ cost.image_total }}</span>
      </div>
      <div class="cost-item">
        <span class="cost-label">视频 ({{ cost.video_total_seconds }}秒)</span>
        <span class="cost-value">¥{{ cost.video_total }}</span>
      </div>
      <div class="cost-item">
        <span class="cost-label">TTS配音</span>
        <span class="cost-value free">免费</span>
      </div>
      <div class="cost-divider"></div>
      <div class="cost-item total">
        <span class="cost-label">总计</span>
        <span class="cost-value">¥{{ cost.grand_total }}</span>
      </div>
    </div>
  </div>
  <div v-else-if="loading" class="cost-panel">
    <el-skeleton :rows="3" animated />
  </div>
</template>

<style scoped>
.cost-panel {
  background: white; border-radius: 12px; padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.cost-panel h4 { margin: 0 0 12px; font-size: 15px; color: #303133; }
.cost-items { display: flex; flex-direction: column; gap: 8px; }
.cost-item { display: flex; justify-content: space-between; align-items: center; }
.cost-label { font-size: 13px; color: #606266; }
.cost-value { font-size: 14px; font-weight: 500; color: #303133; }
.cost-value.free { color: #67c23a; }
.cost-divider { height: 1px; background: #ebeef5; margin: 4px 0; }
.cost-item.total .cost-label { font-weight: bold; color: #303133; }
.cost-item.total .cost-value { font-size: 18px; color: #409eff; font-weight: bold; }
</style>
