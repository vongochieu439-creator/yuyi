<script setup lang="ts">
import { ref } from 'vue'
import { useScriptCreatorStore } from '../../../stores/scriptCreator'

const store = useScriptCreatorStore()
const selectedId = ref<number | null>(null)

const styleMap: Record<string, string> = {
  '悬念型': '🔮',
  '痛点型': '💢',
  '数据型': '📊',
  '反常识型': '🔄',
  '场景代入型': '🎬',
}

const selectAndGenerate = async () => {
  if (selectedId.value === null) return
  const hook = store.hooks.find(h => h.hook_id === selectedId.value)
  if (hook) await store.selectHookAndGenerate(hook)
}
</script>

<template>
  <div style="max-width: 1100px; margin: 30px auto;">
    <!-- Selling points -->
    <div v-if="store.sellingPoints.length" style="margin-bottom: 20px;">
      <h3>核心卖点</h3>
      <el-tag v-for="sp in store.sellingPoints" :key="sp" style="margin: 3px;" type="warning" effect="light">{{ sp }}</el-tag>
    </div>

    <h3 style="margin-bottom: 15px;">选择开场Hook</h3>
    <el-row :gutter="16">
      <el-col :span="12" v-for="hook in store.hooks" :key="hook.hook_id" style="margin-bottom: 16px;">
        <el-card
          shadow="hover"
          class="direction-card"
          :class="{ 'direction-selected': selectedId === hook.hook_id }"
          @click="selectedId = hook.hook_id"
          style="cursor: pointer;"
        >
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-size: 20px;">{{ styleMap[hook.style] || '📝' }}</span>
            <el-tag size="small">{{ hook.style }}</el-tag>
          </div>
          <p style="font-size: 15px; font-weight: 500; margin-bottom: 8px; line-height: 1.6; color: #303133;">"{{ hook.hook_text }}"</p>
          <p style="font-size: 13px; color: #909399;">{{ hook.rationale }}</p>
        </el-card>
      </el-col>
    </el-row>

    <div style="text-align: center; margin-top: 20px;">
      <el-button @click="store.step = 2">返回选方向</el-button>
      <el-button type="primary" size="large" @click="selectAndGenerate" :disabled="selectedId === null" :loading="store.loading">
        确认Hook，生成完整脚本 →
      </el-button>
    </div>
  </div>
</template>
