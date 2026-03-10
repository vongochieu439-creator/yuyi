<script setup lang="ts">
import { ref, watch } from 'vue'
import { listTemplates } from '../../../api/templates'
import type { Template } from '../../../types'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'select', template: Template): void
}>()

const templates = ref<Template[]>([])
const searchText = ref('')
const category = ref('')
const loading = ref(false)

const categories = ['KOL', 'MCN', '方法论', '用户自建']

const loadTemplates = async () => {
  loading.value = true
  try {
    const res: any = await listTemplates({ category: category.value || undefined, search: searchText.value || undefined })
    templates.value = res.templates || []
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (val) => {
  if (val) loadTemplates()
})

const handleSelect = (t: Template) => {
  emit('select', t)
  emit('update:modelValue', false)
}
</script>

<template>
  <el-dialog :model-value="modelValue" title="选择脚本模板" width="700px" @update:model-value="emit('update:modelValue', $event)">
    <div style="display: flex; gap: 8px; margin-bottom: 16px;">
      <el-input v-model="searchText" placeholder="搜索模板..." clearable @keyup.enter="loadTemplates" style="flex: 1;" />
      <el-select v-model="category" placeholder="分类" clearable @change="loadTemplates" style="width: 140px;">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
    </div>
    <div v-loading="loading" class="template-list">
      <div v-for="t in templates" :key="t.id" class="template-item" @click="handleSelect(t)">
        <div class="t-header">
          <strong>{{ t.name }}</strong>
          <el-tag size="small">{{ t.category || t.source }}</el-tag>
        </div>
        <p>{{ t.core_strategy || t.description }}</p>
        <span class="use-count">使用 {{ t.use_count || 0 }} 次</span>
      </div>
      <el-empty v-if="!loading && templates.length === 0" description="暂无匹配模板" />
    </div>
  </el-dialog>
</template>

<style scoped lang="scss">
.template-list { max-height: 400px; overflow-y: auto; }
.template-item {
  padding: 12px; border-bottom: 1px solid var(--border-color); cursor: pointer;
  &:hover { background: var(--bg-color); }
  .t-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
  p { font-size: 13px; color: var(--text-secondary); margin-bottom: 4px; }
  .use-count { font-size: 12px; color: var(--text-muted); }
}
</style>
