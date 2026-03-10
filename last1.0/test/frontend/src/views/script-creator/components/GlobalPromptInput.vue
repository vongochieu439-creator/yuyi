<template>
  <div class="global-prompt-panel">
    <div class="panel-header">
      <div class="title-row">
        <span class="icon">🎨</span>
        <span class="title">全局画面风格</span>
        <el-tooltip content="输入你想要的画面风格，AI 会将其融入每一帧分镜图的生成提示词中" placement="top">
          <el-icon class="help-icon"><QuestionFilled /></el-icon>
        </el-tooltip>
      </div>
      <el-tag size="small" type="info" class="ai-badge">AI 提示词优化</el-tag>
    </div>

    <!-- 快捷风格预设 -->
    <div class="presets">
      <span class="preset-label">快捷预设：</span>
      <el-tag
        v-for="p in presets"
        :key="p.label"
        :class="['preset-tag', { active: modelValue === p.label }]"
        size="small"
        @click="selectPreset(p)"
      >{{ p.label }}</el-tag>
      <el-tag
        v-if="modelValue && !presets.find(p => p.label === modelValue)"
        class="preset-tag active custom-active"
        size="small"
      >自定义</el-tag>
    </div>

    <!-- 输入框 -->
    <div class="input-row">
      <el-input
        :model-value="modelValue"
        @update:model-value="$emit('update:modelValue', $event)"
        placeholder="描述你想要的画面风格，例如：温暖的阳光感，电影质感，浅景深，写实摄影风格..."
        clearable
        maxlength="200"
        show-word-limit
        class="style-input"
      >
        <template #prefix>
          <el-icon><EditPen /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 提示说明 -->
    <div class="hint-row">
      <el-icon class="hint-icon"><InfoFilled /></el-icon>
      <span class="hint-text">
        {{ modelValue
          ? `将对所有 ${totalFrames} 帧分镜图应用"${modelValue}"风格`
          : '留空则直接使用脚本中的原始视觉描述生成图片' }}
      </span>
    </div>

    <!-- 预设说明展开 -->
    <el-collapse-transition>
      <div v-if="activePreset" class="preset-detail">
        <el-icon><StarFilled /></el-icon>
        <span>{{ activePreset.description }}</span>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { QuestionFilled, EditPen, InfoFilled, StarFilled } from '@element-plus/icons-vue'

interface Preset {
  label: string
  value: string
  description: string
}

const props = defineProps<{
  modelValue: string
  totalFrames?: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const presets: Preset[] = [
  {
    label: '商业广告',
    value: '商业广告',
    description: '高度抛光的广告质感，专业棚拍布光，品牌级视觉呈现',
  },
  {
    label: '电影质感',
    value: '电影质感',
    description: '电影色调，宽银幕感，胶片颗粒，大光比，沉浸式氛围',
  },
  {
    label: 'ins写真',
    value: 'ins写真',
    description: '自然光感，生活气息，instagram 流行美学，真实质感',
  },
  {
    label: '极简白',
    value: '极简白',
    description: '纯白背景，极简构图，产品突出，高端简约',
  },
  {
    label: '科技感',
    value: '科技感',
    description: '未来感，深色背景，蓝色光效，数字科技氛围',
  },
  {
    label: '国风写意',
    value: '国风写意',
    description: '中式美学，水墨意境，优雅传统氛围',
  },
]

const activePreset = computed(() =>
  presets.find(p => p.label === props.modelValue) ?? null
)

const selectPreset = (p: Preset) => {
  if (props.modelValue === p.label) {
    // 再次点击取消选择
    emit('update:modelValue', '')
  } else {
    emit('update:modelValue', p.label)
  }
}
</script>

<style scoped>
.global-prompt-panel {
  background: linear-gradient(135deg, #f0f7ff 0%, #f8f0ff 100%);
  border: 1px solid #d0e8ff;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon {
  font-size: 18px;
  line-height: 1;
}

.title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
}

.help-icon {
  color: #909399;
  cursor: help;
  font-size: 14px;
}

.ai-badge {
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  color: #fff;
  border: none;
  font-size: 11px;
}

.presets {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.preset-label {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.preset-tag {
  cursor: pointer;
  transition: all 0.2s;
  border-color: #c0d6ff;
  color: #4a6fa5;
  background: #fff;
}

.preset-tag:hover {
  border-color: #6366f1;
  color: #6366f1;
}

.preset-tag.active {
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  color: #fff;
  border-color: transparent;
}

.preset-tag.custom-active {
  background: linear-gradient(90deg, #f59e0b, #ef4444);
}

.input-row {
  margin-bottom: 8px;
}

.style-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  box-shadow: 0 0 0 1px #d0e8ff;
}

.style-input :deep(.el-input__wrapper:hover),
.style-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1.5px #6366f1;
}

.hint-row {
  display: flex;
  align-items: center;
  gap: 5px;
}

.hint-icon {
  color: #6366f1;
  font-size: 13px;
  flex-shrink: 0;
}

.hint-text {
  font-size: 12px;
  color: #6366f1;
  line-height: 1.5;
}

.preset-detail {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 8px;
  padding: 6px 10px;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 6px;
  font-size: 12px;
  color: #6366f1;
}
</style>
