<script setup lang="ts">
defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const styles = [
  { id: 'cinematic', name: '电影写实', icon: '🎬', desc: '好莱坞级别光影质感' },
  { id: 'ink_wash', name: '国风水墨', icon: '🏯', desc: '传统水墨意境之美' },
  { id: 'anime', name: '日系动漫', icon: '🌸', desc: '精致赛璐璐动漫画风' },
  { id: 'comedy', name: '沙雕搞笑', icon: '🤡', desc: '夸张表情包风格' },
]
</script>

<template>
  <div class="style-grid">
    <div
      v-for="s in styles"
      :key="s.id"
      class="style-card"
      :class="{ active: modelValue === s.id }"
      @click="emit('update:modelValue', s.id)"
    >
      <span class="style-icon">{{ s.icon }}</span>
      <span class="style-name">{{ s.name }}</span>
      <span class="style-desc">{{ s.desc }}</span>
    </div>
  </div>
</template>

<style scoped>
.style-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.style-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 12px;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s;
  background: #fafafa;
}
.style-card:hover {
  border-color: #b0b0ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.style-card.active {
  border-color: #409eff;
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f0ff 100%);
  box-shadow: 0 4px 16px rgba(64,158,255,0.2);
}
.style-icon { font-size: 32px; }
.style-name { font-size: 15px; font-weight: 600; color: #303133; }
.style-desc { font-size: 12px; color: #909399; text-align: center; }
</style>
