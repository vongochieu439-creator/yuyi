<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { useIPStudioStore } from '../../../stores/ipStudio'
import PhaseProgress from '../../../components/PhaseProgress.vue'
import ChatBubble from '../../../components/ChatBubble.vue'

const store = useIPStudioStore()
const userInput = ref('')
const chatBox = ref<HTMLElement>()
const nameInput = ref('')
const industryInput = ref('')
const roleInput = ref('创始人')
const started = ref(false)

const phases = [
  { key: 'background', label: '背景采集', desc: '事实信息' },
  { key: 'hot_topics', label: '热点观点', desc: '立场态度' },
  { key: 'cognitive', label: '认知挖掘', desc: '深层思维' },
  { key: 'voice', label: '表达采样', desc: '语言风格' },
]

const roundCount = computed(() => store.chatHistory.filter(m => m.role === 'user').length)

const interviewDone = computed(() => {
  const lastMsg = store.chatHistory[store.chatHistory.length - 1]
  return store.interviewPhase === 'voice' && lastMsg?.role === 'ai' && roundCount.value >= 12
})

const syncIntervieweeInfo = () => {
  store.intervieweeName = nameInput.value
  store.intervieweeIndustry = industryInput.value
  store.intervieweeRole = roleInput.value
}

const beginInterview = async () => {
  if (!nameInput.value.trim() || !industryInput.value.trim()) return
  started.value = true
  syncIntervieweeInfo()
  await store.askNextQuestion(nameInput.value, industryInput.value)
  await nextTick()
  scrollBottom()
}

const submitAnswer = async () => {
  if (!userInput.value.trim() || store.loading) return
  const msg = userInput.value.trim()
  userInput.value = ''
  store.addUserMessage(msg)
  await nextTick()
  scrollBottom()
  await store.askNextQuestion(nameInput.value, industryInput.value)
  await nextTick()
  scrollBottom()
}

const undoLastAnswer = () => {
  if (store.chatHistory.length >= 2) {
    store.chatHistory.pop()
    store.chatHistory.pop()
  }
}

const finalizeProfile = async () => {
  await store.finalizeProfile(nameInput.value, industryInput.value, roleInput.value)
}

const scrollBottom = () => {
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}
</script>

<template>
  <div class="page-narrow">
    <el-card shadow="always">
      <template #header>
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #f59e0b, #ef4444); display: flex; align-items: center; justify-content: center; color: white; font-size: 14px; font-weight: bold; flex-shrink: 0;">记</div>
          <div style="flex: 1;">
            <div style="font-weight: bold; font-size: 15px;">AI记者 · 正在访谈</div>
            <div style="font-size: 12px; color: #909399;">约10-15分钟，请认真作答，答案越真实脚本越像你</div>
          </div>
          <el-tag v-if="interviewDone" type="success">全部完成</el-tag>
          <el-tag v-else-if="started" type="warning">第 {{ roundCount }} 轮</el-tag>
        </div>
      </template>

      <!-- Phase progress -->
      <PhaseProgress v-if="started" :phases="phases" :current-phase="store.interviewPhase" theme="warm" />

      <!-- Setup form -->
      <div v-if="!started" style="margin-bottom: 20px;">
        <p style="color: #606266; margin-bottom: 16px; font-size: 14px;">访谈开始前，先告诉我你的基本信息：</p>
        <el-form label-width="80px">
          <el-form-item label="你的名字" required>
            <el-input v-model="nameInput" placeholder="如：张总、李总、老王" size="large" />
          </el-form-item>
          <el-form-item label="所在行业" required>
            <el-input v-model="industryInput" placeholder="如：餐饮、教育、制造业" size="large" />
          </el-form-item>
          <el-form-item label="你的角色">
            <el-input v-model="roleInput" placeholder="如：创始人、总经理" size="large" />
          </el-form-item>
        </el-form>
        <div style="display: flex; gap: 10px;">
          <el-button type="warning" size="large" @click="beginInterview"
            :disabled="!nameInput.trim() || !industryInput.trim()"
            style="flex: 1; font-size: 15px;">
            🎙️ 开始接受访谈
          </el-button>
          <el-button @click="() => { syncIntervieweeInfo(); store.goToView('voice') }">语音访谈</el-button>
        </div>
      </div>

      <!-- Chat area -->
      <div v-if="started">
        <div ref="chatBox" style="height: 420px; overflow-y: auto; padding: 16px; background: #f8f9fa; border-radius: 8px; margin-bottom: 14px;">
          <ChatBubble
            v-for="(msg, i) in store.chatHistory" :key="i"
            :role="msg.role" :content="msg.content" :user-name="nameInput"
          />
          <div v-if="store.loading" style="display: flex; gap: 10px; align-items: center;">
            <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #f59e0b, #ef4444); display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; flex-shrink: 0;">记</div>
            <div style="background: white; border: 1px solid #fde68a; border-radius: 2px 12px 12px 12px; padding: 12px 16px; font-size: 14px; color: #909399;">
              <el-icon class="is-loading"><Loading /></el-icon> 思考下一个问题...
            </div>
          </div>
        </div>

        <!-- Input -->
        <div v-if="!interviewDone" style="display: flex; gap: 8px;">
          <el-input v-model="userInput" type="textarea" :rows="3"
            placeholder="认真作答，答案越具体真实，最终脚本越像你自己写的...（Ctrl+Enter发送）"
            @keydown.ctrl.enter="submitAnswer" :disabled="store.loading" />
          <div style="display: flex; flex-direction: column; gap: 4px; flex-shrink: 0;">
            <el-button type="warning" @click="submitAnswer"
              :disabled="!userInput.trim() || store.loading"
              style="height: 50px; width: 80px; font-size: 13px;">
              发送<br>(Ctrl+↵)
            </el-button>
            <el-button v-if="roundCount > 0 && !store.loading" type="info" plain size="small"
              @click="undoLastAnswer" style="height: 26px; width: 80px; font-size: 11px;">
              ↩ 重答
            </el-button>
          </div>
        </div>

        <!-- Finalize -->
        <div v-if="interviewDone" style="text-align: center; padding: 16px; background: #fef3c7; border-radius: 8px; border: 1px solid #fde68a;">
          <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">🎉 四阶段访谈全部完成！</div>
          <div style="color: #92400e; font-size: 13px; margin-bottom: 16px;">AI将基于你的背景、观点、思维方式和表达习惯，提炼专属IP档案...</div>
          <el-button type="warning" size="large" @click="finalizeProfile" :loading="store.loading" style="font-size: 15px; padding: 12px 40px;">
            {{ store.loading ? '正在提炼IP档案...' : '生成我的IP档案 →' }}
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>
