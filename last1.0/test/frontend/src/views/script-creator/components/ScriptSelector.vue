<template>
  <div class="script-selector">
    <div class="header">
      <h3>{{ store.dataDrivenMode ? '选择脚本方向（数据驱动）' : '选择创意方向' }}</h3>
      <el-button :loading="store.loading" @click="handleRegenerate" v-if="!store.dataDrivenMode">换一批</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="8" v-for="script in displayScripts" :key="script.script_id">
        <el-card
          :class="['script-card', { selected: store.selectedScriptId === script.script_id }]"
          shadow="hover"
          @click="store.selectedScriptId = script.script_id"
        >
          <template #header>
            <div class="card-header">
              <el-tag
                :type="directionTagType(script)"
                size="small"
              >{{ script.name || script.direction_label || '方案' }}</el-tag>
              <el-tag v-if="script.direction_label" size="small" type="info" style="margin-left: 4px;">
                {{ script.direction_label }}
              </el-tag>
            </div>
          </template>

          <!-- 数据驱动模式：展示数据依据 -->
          <template v-if="store.dataDrivenMode && script.data_source">
            <div class="data-source">
              <span class="badge">数据依据</span>
              <span class="text">{{ script.data_source }}</span>
            </div>

            <!-- 参考视频 -->
            <div v-if="script.reference_videos?.length" class="ref-videos">
              <span class="label">参考视频:</span>
              <div v-for="(v, i) in script.reference_videos.slice(0, 2)" :key="i" class="ref-item">
                <span class="ref-title">{{ v.title?.slice(0, 25) || '视频' }}{{ v.title?.length > 25 ? '...' : '' }}</span>
                <span class="ref-stats">{{ formatCount(v.play_count) }}播放</span>
              </div>
            </div>

            <!-- 方向特色描述 -->
            <div class="direction-hint">
              <template v-if="script.direction === 'industry'">
                学习同行业爆款的成功模式，创作同水准脚本
              </template>
              <template v-else-if="script.direction === 'comments'">
                直接回应评论区高频痛点，精准引发共鸣
              </template>
              <template v-else-if="script.direction === 'creative'">
                跨行业创意迁移，打造差异化内容
              </template>
            </div>
          </template>

          <!-- 非数据驱动模式：保留原有展示 -->
          <template v-else>
            <p class="description">{{ script.description }}</p>

            <div v-if="script.hook" class="hook-preview">
              <span class="label">开场钩子:</span>
              <span class="hook-text">{{ script.hook }}</span>
            </div>

            <div v-if="script.structure_preview?.length" class="structure-preview">
              <span class="label">内容结构:</span>
              <div class="structure-list">
                <el-tag
                  v-for="(s, i) in script.structure_preview.slice(0, 5)"
                  :key="i"
                  size="small"
                  type="info"
                  class="struct-tag"
                >{{ s }}</el-tag>
              </div>
            </div>

            <div v-if="script.creative_techniques?.length" class="techniques">
              <span class="label">创意手法:</span>
              <el-tag
                v-for="t in script.creative_techniques.slice(0, 3)"
                :key="t"
                size="small"
                type="warning"
                class="tech-tag"
              >{{ t }}</el-tag>
            </div>
          </template>

          <!-- 镜头预览（如果有shots） -->
          <div v-if="script.shots?.length" class="shots-preview">
            <span class="label">{{ script.shots.length }}个镜头 · {{ Math.round(script.total_duration || 0) }}秒</span>
            <div class="shots-narration-list">
              <div v-for="(shot, si) in script.shots.slice(0, 4)" :key="si" class="shot-narration-item">
                <el-tag size="small" :type="shot.act_type === 'hook' ? 'danger' : shot.act_type === 'cta' ? 'success' : 'info'" class="shot-label">
                  {{ shot.act_type === 'hook' ? '开场' : shot.act_type === 'cta' ? '结尾' : `镜头${Number(si) + 1}` }}
                </el-tag>
                <span class="shot-text">{{ shot.narration?.slice(0, 30) }}{{ (shot.narration?.length || 0) > 30 ? '...' : '' }}</span>
              </div>
              <div v-if="script.shots.length > 4" class="shot-narration-item more">
                <span class="shot-text">...还有{{ script.shots.length - 4 }}个镜头</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="action-bar" v-if="store.selectedScriptId !== null">
      <el-button
        type="primary"
        size="large"
        :loading="store.loading"
        @click="handleSelect"
      >
        选择「{{ selectedName }}」{{ store.dataDrivenMode ? '并创建项目' : hasPreGeneratedShots ? '使用此脚本' : '并生成完整脚本' }}
      </el-button>
      <span class="hint">
        {{ store.dataDrivenMode ? '创建项目后进入脚本打磨阶段' : hasPreGeneratedShots ? '脚本已就绪，直接进入打磨阶段' : '选中后AI将生成完整分镜脚本（约30秒）' }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useScriptCreatorStore } from '../../../stores/scriptCreator'

const store = useScriptCreatorStore()

const displayScripts = computed((): any[] => {
  if (store.dataDrivenMode && store.dataDrivenScripts.length) {
    return store.dataDrivenScripts as any[]
  }
  return store.generatedScripts as any[]
})

const directionTagType = (script: any) => {
  if (script.direction === 'industry' || script.risk_level === 'safe') return 'success'
  if (script.direction === 'comments' || script.risk_level === 'moderate') return 'warning'
  if (script.direction === 'creative' || script.risk_level === 'creative') return 'danger'
  return ''
}

const hasPreGeneratedShots = computed(() => {
  return displayScripts.value.some((s: any) => s.shots?.length > 0)
})

const selectedName = computed(() => {
  const scripts = displayScripts.value
  const s = scripts.find((s: any) => s.script_id === store.selectedScriptId)
  return (s as any)?.name || (s as any)?.direction_label || ''
})

const formatCount = (count: number) => {
  if (count >= 10000) return (count / 10000).toFixed(1) + '万'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'k'
  return String(count || 0)
}

const handleSelect = async () => {
  if (store.selectedScriptId === null) {
    ElMessage.warning('请先选择一个方向')
    return
  }
  if (store.dataDrivenMode) {
    await store.selectDataDrivenScript(store.selectedScriptId)
  } else {
    await store.selectScript(store.selectedScriptId)
  }
  ElMessage.success('脚本生成完成，进入打磨阶段')
}

const handleRegenerate = async () => {
  await store.regenerateScripts()
  ElMessage.info('已生成新的创意方向')
}
</script>

<style scoped>
.script-selector { padding: 20px 0; max-width: 900px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.script-card { cursor: pointer; transition: all 0.3s; margin-bottom: 16px; min-height: 200px; }
.script-card.selected { border-color: var(--el-color-primary); box-shadow: 0 0 8px rgba(64, 158, 255, 0.3); }
.card-header { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
.description { font-size: 14px; color: #666; margin-bottom: 12px; line-height: 1.6; }

/* 数据驱动模式样式 */
.data-source { margin-bottom: 12px; padding: 8px; background: #f0f7ff; border-radius: 6px; font-size: 13px; }
.data-source .badge { display: inline-block; background: #409eff; color: #fff; font-size: 11px; padding: 1px 6px; border-radius: 3px; margin-right: 6px; }
.data-source .text { color: #333; }

.ref-videos { margin-bottom: 10px; }
.ref-videos .label { font-size: 12px; color: #999; display: block; margin-bottom: 4px; }
.ref-item { display: flex; justify-content: space-between; font-size: 12px; padding: 3px 0; color: #666; }
.ref-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ref-stats { color: #f56c6c; margin-left: 8px; white-space: nowrap; }

.direction-hint { font-size: 12px; color: #909399; font-style: italic; margin-top: 8px; line-height: 1.5; }

.shots-preview { margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee; }
.shots-preview .label { font-size: 12px; color: #999; display: block; margin-bottom: 6px; }
.shots-narration-list { display: flex; flex-direction: column; gap: 4px; }
.shot-narration-item { display: flex; align-items: center; gap: 6px; font-size: 12px; }
.shot-narration-item .shot-label { flex-shrink: 0; }
.shot-narration-item .shot-text { color: #606266; line-height: 1.4; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.shot-narration-item.more .shot-text { color: #909399; font-style: italic; }

/* 原有样式保留 */
.hook-preview { margin-bottom: 10px; }
.hook-preview .label { font-size: 12px; color: #999; display: block; margin-bottom: 4px; }
.hook-preview .hook-text { font-size: 13px; color: #409eff; font-style: italic; }
.structure-preview { margin-bottom: 10px; }
.structure-preview .label { font-size: 12px; color: #999; display: block; margin-bottom: 4px; }
.structure-list { display: flex; flex-wrap: wrap; gap: 4px; }
.struct-tag { margin: 0; }
.techniques { margin-bottom: 8px; }
.techniques .label { font-size: 12px; color: #999; margin-right: 6px; }
.tech-tag { margin: 2px; }
.action-bar { text-align: center; margin-top: 24px; }
.action-bar .hint { display: block; font-size: 12px; color: #999; margin-top: 8px; }
</style>
