<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useIPStudioStore } from '../../../stores/ipStudio'
import StepProgress from '../../../components/StepProgress.vue'

const store = useIPStudioStore()
const scriptDuration = ref(90)
const rejectedIds = ref<Set<string>>(new Set())
const editingId = ref<string | null>(null)
const editText = ref('')
const edits = ref<Array<{ original_text: string; edited_text: string; paragraph_index: number; topic_title: string }>>([])
const feedbackNotes = ref('')
const feedbackSubmitted = ref(false)
const feedbackResult = ref<any>(null)

const script = computed(() => store.generatedScript)
const scriptSteps = ['思考', '写稿', '去AI味']
const scriptStep = ref(0)
const scriptStepText = computed(() => {
  const texts = ['Step1: 以你的身份思考这个话题...', 'Step2: 基于思考写稿...', 'Step3: 去除AI味，匹配你的表达方式...']
  return texts[scriptStep.value] || '生成中...'
})

const generateScript = async () => {
  if (!store.currentProfile) return
  // Find current topic from store
  const topic = store.topics.find(t => t.title === script.value?.topic_title) || store.topics[0]
  if (!topic) { ElMessage.warning('请先选择一个选题'); return }

  scriptStep.value = 0
  const stepTimer = setInterval(() => {
    if (scriptStep.value < 2) scriptStep.value++
  }, 5000)

  try {
    await store.generateScriptFromTopic(store.currentProfile.profile_id, topic, scriptDuration.value)
  } finally {
    clearInterval(stepTimer)
    scriptStep.value = 3
  }
}

const toggleReject = (paraId: string) => {
  if (rejectedIds.value.has(paraId)) rejectedIds.value.delete(paraId)
  else rejectedIds.value.add(paraId)
}

const startEdit = (paraId: string, text: string) => {
  editingId.value = paraId
  editText.value = text
}

const saveEdit = (para: any) => {
  if (editText.value !== para.text) {
    edits.value.push({
      original_text: para.text, edited_text: editText.value,
      paragraph_index: para.index, topic_title: script.value?.topic_title || '',
    })
    para.text = editText.value
  }
  editingId.value = null
}

const hasChanges = computed(() => rejectedIds.value.size > 0 || edits.value.length > 0)

const submitFeedback = async () => {
  if (!store.currentProfile || !script.value) return
  const rejected = script.value.paragraphs
    .filter(p => rejectedIds.value.has(p.paragraph_id))
    .map(p => p.text)

  const result = await store.submitScriptFeedback(
    store.currentProfile.profile_id, rejected, edits.value, feedbackNotes.value
  )
  feedbackResult.value = result
  feedbackSubmitted.value = true
  ElMessage.success('反馈已提交，IP档案已更新')
}

const copyScript = () => {
  if (script.value?.full_script) {
    navigator.clipboard.writeText(script.value.full_script)
    ElMessage.success('已复制到剪贴板')
  }
}
</script>

<template>
  <div style="max-width: 900px; margin: 0 auto;">
    <!-- Duration + generate -->
    <el-card style="margin-bottom: 20px;">
      <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
        <span style="font-size: 14px; color: #303133; font-weight: bold;">脚本时长：</span>
        <el-radio-group v-model="scriptDuration">
          <el-radio-button :value="60">60秒</el-radio-button>
          <el-radio-button :value="90">90秒</el-radio-button>
          <el-radio-button :value="120">2分钟</el-radio-button>
          <el-radio-button :value="180">3分钟</el-radio-button>
        </el-radio-group>
        <el-button type="warning" size="large" @click="generateScript" :loading="store.loading" style="margin-left: auto;">
          {{ store.loading ? scriptStepText : (script ? '🔄 重新生成' : '✨ 生成脚本') }}
        </el-button>
      </div>
      <div style="font-size: 12px; color: #909399; margin-top: 8px;">
        约 {{ Math.round(scriptDuration * 3.2) }} 字口播量 · 3步生成：思考→写稿→去AI味
      </div>
    </el-card>

    <!-- Generating progress -->
    <StepProgress v-if="store.loading" :steps="scriptSteps" :current-step="scriptStep" :loading="true" :title="scriptStepText" />

    <!-- Script result -->
    <template v-if="script && !store.loading">
      <!-- Thinking memo -->
      <el-card v-if="script.thinking_memo" style="margin-bottom: 16px; border: 1px solid #e0e7ff;">
        <template #header>
          <span style="font-size: 14px; font-weight: bold;">💭 思考备忘录</span>
        </template>
        <p style="font-size: 14px; color: #606266; line-height: 1.8; white-space: pre-line;">{{ script.thinking_memo }}</p>
      </el-card>

      <!-- Stats bar -->
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
        <el-tag type="warning">{{ script.word_count }} 字</el-tag>
        <el-tag type="info">约 {{ script.duration }} 秒</el-tag>
        <el-tag>{{ script.paragraphs.length }} 段</el-tag>
        <el-button text type="primary" @click="copyScript" style="margin-left: auto;">📋 复制全文</el-button>
      </div>

      <!-- Paragraphs -->
      <div v-for="para in script.paragraphs" :key="para.paragraph_id"
        :style="{
          padding: '16px', marginBottom: '12px', background: rejectedIds.has(para.paragraph_id) ? '#fff5f5' : 'white',
          border: '1px solid ' + (rejectedIds.has(para.paragraph_id) ? '#fca5a5' : '#e4e7ed'),
          borderRadius: '8px', borderLeft: rejectedIds.has(para.paragraph_id) ? '4px solid #ef4444' : '4px solid #e4e7ed',
        }">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-size: 12px; font-weight: 600; color: #909399;">P{{ para.index + 1 }}</span>
          <div style="display: flex; gap: 6px;">
            <el-button size="small" :type="rejectedIds.has(para.paragraph_id) ? 'danger' : ''" plain @click="toggleReject(para.paragraph_id)">
              {{ rejectedIds.has(para.paragraph_id) ? '✓ 已标记' : '👎 不像我' }}
            </el-button>
            <el-button size="small" plain @click="startEdit(para.paragraph_id, para.text)">✏️ 编辑</el-button>
          </div>
        </div>
        <div v-if="editingId === para.paragraph_id">
          <el-input v-model="editText" type="textarea" :rows="3" />
          <div style="margin-top: 8px; display: flex; gap: 6px;">
            <el-button size="small" type="primary" @click="saveEdit(para)">保存</el-button>
            <el-button size="small" @click="editingId = null">取消</el-button>
          </div>
        </div>
        <p v-else style="font-size: 14px; line-height: 1.8; color: #303133;">{{ para.text }}</p>
      </div>

      <!-- Feedback area -->
      <el-card v-if="hasChanges && !feedbackSubmitted" style="margin-top: 20px; border: 1px solid #fde68a;">
        <h4 style="margin-bottom: 12px;">提交反馈</h4>
        <p style="font-size: 13px; color: #606266; margin-bottom: 12px;">
          {{ rejectedIds.size }} 段标记"不像我" + {{ edits.length }} 处编辑 — 提交后AI会更新你的声音指纹
        </p>
        <el-input v-model="feedbackNotes" type="textarea" :rows="2" placeholder="可选：补充说明哪里不像你..." style="margin-bottom: 12px;" />
        <el-button type="warning" @click="submitFeedback" :loading="store.loading">提交反馈，优化我的IP</el-button>
      </el-card>

      <!-- Feedback result -->
      <el-card v-if="feedbackSubmitted && feedbackResult" style="margin-top: 20px; border: 1px solid #86efac;">
        <h4 style="color: #10b981; margin-bottom: 12px;">✅ 反馈已处理</h4>
        <div v-if="feedbackResult.new_forbidden_words?.length" style="margin-bottom: 8px;">
          <span style="font-size: 13px; font-weight: bold;">新增禁用词：</span>
          <el-tag v-for="w in feedbackResult.new_forbidden_words" :key="w" size="small" type="danger" style="margin: 2px;">{{ w }}</el-tag>
        </div>
        <div v-if="feedbackResult.suggestions" style="font-size: 13px; color: #606266;">
          <strong>建议：</strong>{{ feedbackResult.suggestions }}
        </div>
        <div style="margin-top: 12px;">
          <el-button type="warning" @click="store.goToView('detail')">返回工作台</el-button>
          <el-button @click="generateScript">重新生成脚本</el-button>
        </div>
      </el-card>
    </template>
  </div>
</template>
