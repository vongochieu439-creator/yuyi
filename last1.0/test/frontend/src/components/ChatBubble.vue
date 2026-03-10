<script setup lang="ts">
defineProps<{
  role: 'ai' | 'user' | 'phase-transition'
  content: string
  avatarText?: string
  avatarGradient?: string
  userName?: string
}>()
</script>

<template>
  <!-- Phase transition -->
  <div v-if="role === 'phase-transition'" style="text-align: center; padding: 12px; margin: 8px 0;">
    <div style="display: inline-block; padding: 8px 20px; background: linear-gradient(135deg, #fef3c7, #fde68a); border-radius: 20px; font-size: 13px; color: #92400e; font-weight: bold;">
      {{ content }}
    </div>
  </div>

  <!-- AI message -->
  <div v-else-if="role === 'ai'" class="chat-bubble-row ai">
    <div class="bubble-avatar" :style="{ background: avatarGradient || 'linear-gradient(135deg, #f59e0b, #ef4444)' }">
      {{ avatarText || '记' }}
    </div>
    <div class="bubble-content ai">{{ content }}</div>
  </div>

  <!-- User message -->
  <div v-else class="chat-bubble-row user">
    <div class="bubble-content user">{{ content }}</div>
    <div class="bubble-avatar" style="background: #6b7280;">
      {{ userName?.[0] || '我' }}
    </div>
  </div>
</template>

<style scoped>
.chat-bubble-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 16px;
}
.chat-bubble-row.user {
  justify-content: flex-end;
}
.bubble-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 11px;
  font-weight: bold;
  flex-shrink: 0;
}
.bubble-content {
  max-width: 85%;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-line;
}
.bubble-content.ai {
  background: white;
  border: 1px solid #fde68a;
  border-radius: 2px 12px 12px 12px;
  color: #303133;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.bubble-content.user {
  background: #f59e0b;
  border-radius: 12px 2px 12px 12px;
  color: white;
}
</style>
