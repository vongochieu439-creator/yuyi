<script setup lang="ts">
import { ref } from 'vue'
import { useScriptCreatorStore } from '../../../stores/scriptCreator'

const store = useScriptCreatorStore()
const selectedId = ref<number | null>(null)

const selectAndProceed = async () => {
  if (selectedId.value === null) return
  const dir = store.directions.find(d => d.direction_id === selectedId.value)
  if (dir) await store.selectDir(dir)
}
</script>

<template>
  <div style="max-width: 1100px; margin: 30px auto;">
    <!-- Competitor insights -->
    <div style="margin-bottom: 20px;">
      <h3>竞品洞察</h3>
      <el-card shadow="never" style="background: #f5f7fa;">
        <el-row :gutter="20">
          <el-col :span="8">
            <h4>成功模式</h4>
            <el-tag v-for="p in (store.competitorSummary as any)?.winning_patterns || []" :key="p" style="margin: 3px;" type="success">{{ p }}</el-tag>
          </el-col>
          <el-col :span="8">
            <h4>开场策略</h4>
            <el-tag v-for="h in (store.competitorSummary as any)?.hook_strategies || []" :key="h" style="margin: 3px;" type="warning">{{ h }}</el-tag>
          </el-col>
          <el-col :span="8">
            <h4>市场摘要</h4>
            <p style="font-size: 13px; color: #606266;">{{ ((store.marketSummary as any)?.summary || '').substring(0, 200) }}</p>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <h3 style="margin-bottom: 15px;">选择创意方向</h3>
    <el-row :gutter="20">
      <el-col :span="8" v-for="dir in store.directions" :key="dir.direction_id">
        <el-card
          shadow="hover"
          class="direction-card"
          :class="{ 'direction-selected': selectedId === dir.direction_id }"
          @click="selectedId = dir.direction_id"
          style="cursor: pointer; height: 100%;"
        >
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 18px; font-weight: bold;">{{ dir.name }}</span>
              <el-tag
                :type="dir.risk_level === 'safe' ? 'success' : dir.risk_level === 'moderate' ? 'warning' : 'danger'"
                size="small"
              >
                {{ dir.risk_level === 'safe' ? '低风险' : dir.risk_level === 'moderate' ? '中等风险' : '高风险高回报' }}
              </el-tag>
            </div>
          </template>
          <p style="color: #606266; margin-bottom: 12px;">{{ dir.description }}</p>
          <div style="background: #f0f9ff; padding: 10px; border-radius: 6px; margin-bottom: 12px;">
            <strong>开场钩子:</strong>
            <p style="color: #409eff; margin: 5px 0 0;">{{ dir.hook }}</p>
          </div>
          <div style="margin-bottom: 12px;">
            <strong>内容结构:</strong>
            <div v-for="s in dir.structure_preview" :key="s" style="font-size: 13px; color: #909399; padding: 2px 0;">{{ s }}</div>
          </div>
          <div v-if="dir.creative_techniques?.length">
            <strong>创意手法:</strong>
            <el-tag v-for="t in dir.creative_techniques" :key="t" size="small" type="danger" style="margin: 3px;">{{ t }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div style="text-align: center; margin-top: 30px;">
      <el-button @click="store.step = 0">重新输入</el-button>
      <el-button type="primary" size="large" @click="selectAndProceed" :disabled="selectedId === null" :loading="store.loading">
        确认方向，生成Hook →
      </el-button>
    </div>
  </div>
</template>
