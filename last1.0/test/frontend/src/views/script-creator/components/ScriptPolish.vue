<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useScriptCreatorStore } from '../../../stores/scriptCreator'
import { useDebounce } from '../../../composables/useDebounce'

const store = useScriptCreatorStore()
const showRationale = ref(false)
const showOtherScripts = ref(false)
const chatInput = ref('')
const { debounce } = useDebounce(300)

const quickCommands = [
  '让开头更吸引人',
  '加强产品卖点的呈现',
  '让结尾更有行动力',
  '整体语言更口语化',
  '用第一个脚本的开头',
  '把第三个脚本的CTA换过来',
]

const handleSend = () => {
  debounce(() => {
    if (!chatInput.value.trim()) return
    store.sendChatMessage(chatInput.value.trim())
    chatInput.value = ''
  })
}

const applyQuickCommand = (cmd: string) => {
  chatInput.value = cmd
  handleSend()
}

const handleConfirmPreview = async () => {
  await store.confirmAndPreview()
  ElMessage.success('脚本已确认，进入分镜预览！')
}
</script>

<template>
  <div style="max-width: 1100px; margin: 30px auto;">
    <el-row :gutter="20">
      <!-- Left: Script preview -->
      <el-col :span="15">
        <el-card shadow="always">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h3 style="margin: 0; font-size: 16px;">脚本预览</h3>
              <el-switch v-model="showRationale" active-text="显示创作依据" />
            </div>
          </template>

          <div style="max-height: 500px; overflow-y: auto;">
            <div v-for="shot in store.scriptShots" :key="shot.shot_id || shot.id" style="padding: 12px 0; border-bottom: 1px solid #ebeef5;">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <el-tag size="small" type="info">{{ shot.shot_type }}</el-tag>
                <span style="font-size: 12px; color: #909399;">{{ shot.duration }}s</span>
              </div>
              <p style="font-size: 14px; line-height: 1.6; color: #303133;">{{ shot.narration }}</p>
              <p v-if="showRationale && shot.rationale" style="font-size: 12px; color: #909399; margin-top: 4px; font-style: italic;">{{ shot.rationale }}</p>
            </div>
          </div>

          <!-- Quality check -->
          <div v-if="store.qualityCheck" style="margin-top: 16px; padding: 12px; background: #f5f7fa; border-radius: 8px;">
            <h4 style="margin-bottom: 8px; font-size: 14px;">质量自检</h4>
            <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 4px;">
              <span style="font-size: 13px; color: #606266; min-width: 70px;">覆盖卖点:</span>
              <el-tag v-for="sp in store.qualityCheck.covered_selling_points" :key="sp" size="small" type="success">{{ sp }}</el-tag>
            </div>
            <div v-if="store.qualityCheck.missing_selling_points?.length" style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
              <span style="font-size: 13px; color: #606266; min-width: 70px;">缺失卖点:</span>
              <el-tag v-for="sp in store.qualityCheck.missing_selling_points" :key="sp" size="small" type="danger">{{ sp }}</el-tag>
            </div>
          </div>

          <!-- Confirm and Preview button -->
          <div style="margin-top: 16px;">
            <el-button type="primary" size="large" style="width: 100%;" @click="handleConfirmPreview" :loading="store.loading">
              确认并预览分镜
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- Right: Chat polish + Other scripts -->
      <el-col :span="9">
        <!-- Other scripts reference -->
        <el-card v-if="store.allScriptsContext.length > 1" shadow="hover" style="margin-bottom: 16px;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center; cursor: pointer;" @click="showOtherScripts = !showOtherScripts">
              <h3 style="margin: 0; font-size: 14px;">其他脚本参考</h3>
              <el-icon><component :is="showOtherScripts ? 'ArrowUp' : 'ArrowDown'" /></el-icon>
            </div>
          </template>

          <div v-show="showOtherScripts">
            <div
              v-for="script in store.allScriptsContext.filter(s => s.script_id !== store.selectedScriptId)"
              :key="script.script_id"
              style="margin-bottom: 12px; padding: 8px; background: #f5f7fa; border-radius: 6px;"
            >
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <el-tag size="small" :type="script.risk_level === 'safe' ? 'success' : script.risk_level === 'moderate' ? 'warning' : 'danger'">
                  {{ script.name }}
                </el-tag>
                <span style="font-size: 12px; color: #999;">{{ Math.round(script.total_duration) }}s</span>
              </div>
              <div v-for="shot in script.shots.slice(0, 3)" :key="shot.shot_id" style="font-size: 12px; color: #666; line-height: 1.4; margin-bottom: 2px;">
                {{ shot.narration.slice(0, 30) }}...
              </div>
              <span v-if="script.shots.length > 3" style="font-size: 11px; color: #aaa;">+{{ script.shots.length - 3 }}个镜头</span>
            </div>
          </div>
        </el-card>

        <!-- Chat polish -->
        <el-card shadow="hover">
          <template #header>
            <h3 style="margin: 0; font-size: 16px;">对话打磨</h3>
          </template>

          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
            <el-button v-for="cmd in quickCommands" :key="cmd" size="small" plain @click="applyQuickCommand(cmd)">{{ cmd }}</el-button>
          </div>

          <div style="max-height: 350px; overflow-y: auto; margin-bottom: 12px;">
            <div v-for="(msg, i) in store.chatMessages" :key="i" style="margin-bottom: 14px;">
              <div v-if="msg.role === 'ai'" style="display: flex; align-items: flex-start; gap: 10px;">
                <div style="width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #409eff, #67c23a); display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: bold; flex-shrink: 0;">AI</div>
                <div style="background: #f5f7fa; border: 1px solid #e4e7ed; border-radius: 2px 10px 10px 10px; padding: 8px 12px; max-width: 85%; font-size: 13px; color: #303133; line-height: 1.6; white-space: pre-line;">{{ msg.content }}</div>
              </div>
              <div v-else style="display: flex; justify-content: flex-end;">
                <div style="background: #409eff; border-radius: 10px 2px 10px 10px; padding: 8px 12px; max-width: 85%; font-size: 13px; color: white; line-height: 1.6;">{{ msg.content }}</div>
              </div>
            </div>
          </div>

          <div style="display: flex; gap: 8px;">
            <el-input v-model="chatInput" placeholder="输入修改指令（支持混搭：用第一个脚本的开头）..." @keyup.enter="handleSend" />
            <el-button type="primary" :loading="store.loading" @click="handleSend">发送</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
