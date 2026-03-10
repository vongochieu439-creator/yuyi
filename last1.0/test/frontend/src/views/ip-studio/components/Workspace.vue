<script setup lang="ts">
import { ref, computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useIPStudioStore } from '../../../stores/ipStudio'
import type { Topic } from '../../../types'

const store = useIPStudioStore()
const p = computed(() => store.currentProfile)
const showDetails = ref(false)
const generatingTopics = ref(false)
const generatingScript = ref(false)

const hasEnhanced = computed(() => {
  if (!p.value) return false
  return p.value.thinking_models || p.value.voice_fingerprint || p.value.business_intent ||
    (p.value.opinion_bank && p.value.opinion_bank.length > 0)
})

const topicTypeTag = (type: string) => {
  const map: Record<string, string> = {
    '故事型': '', '观点型': 'warning', '干货型': 'success', '日常型': 'info', '争议型': 'danger'
  }
  return map[type] || ''
}

const generateTopics = async () => {
  if (!p.value) return
  generatingTopics.value = true
  try {
    await store.generateNewTopics(p.value.profile_id, 15)
    ElMessage.success(`已生成 ${store.topics.length} 个选题`)
  } catch (e: any) {
    ElMessage.error('选题生成失败: ' + e.message)
  } finally {
    generatingTopics.value = false
  }
}

const openScriptGenerator = (topic: Topic) => {
  store.generatedScript = null
  ;(store as any)._currentTopic = topic
  store.goToView('script')
}

const autoFlow = async () => {
  if (!p.value) return
  generatingTopics.value = true
  try {
    await store.generateNewTopics(p.value.profile_id, 15)
    if (store.topics.length > 0) {
      openScriptGenerator(store.topics[0]!)
    }
  } catch (e: any) {
    ElMessage.error('生成失败: ' + e.message)
  } finally {
    generatingTopics.value = false
  }
}

const startSupplementInterview = () => {
  store.resetInterview()
  store.goToView('interview')
}
</script>

<template>
  <div v-if="p">
    <!-- Top: IP info card with warm gradient -->
    <el-card style="margin-bottom: 20px; background: linear-gradient(135deg, #fffbeb, #fef3c7); border: 1px solid #fde68a;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
        <div style="flex: 1;">
          <div style="font-size: 22px; font-weight: bold; margin-bottom: 4px;">{{ p.name }}</div>
          <div style="color: #92400e; font-size: 14px; margin-bottom: 10px;">{{ p.industry }} · {{ p.role }}</div>
          <div style="font-size: 14px; color: #78350f; line-height: 1.6; margin-bottom: 10px;">
            <strong>IP定位：</strong>{{ p.ip_positioning }}
          </div>
          <div style="font-size: 13px; color: #92400e;">
            <strong>说话风格：</strong>{{ p.speaking_style }}
          </div>
        </div>
        <div style="min-width: 200px;">
          <div style="margin-bottom: 8px; font-size: 12px; color: #92400e; font-weight: bold;">内容支柱</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
            <el-tag v-for="c in (p.content_pillars || [])" :key="c" type="warning" effect="light" size="small">{{ c }}</el-tag>
          </div>
          <div style="font-size: 12px; color: #92400e; font-weight: bold; margin-bottom: 6px;">目标受众</div>
          <div style="font-size: 13px; color: #78350f;">{{ p.target_audience }}</div>
        </div>
      </div>
    </el-card>

    <!-- Cognitive model + voice fingerprint -->
    <el-card v-if="hasEnhanced" shadow="hover" style="margin-bottom: 20px;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: bold; font-size: 15px;">🧠 认知模型 & 声音指纹</span>
          <el-button text size="small" @click="showDetails = !showDetails">{{ showDetails ? '收起' : '展开详情' }}</el-button>
        </div>
      </template>
      <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
        <el-tag v-for="tm in (p.thinking_models || []).slice(0, 4)" :key="tm" type="danger" effect="plain" size="small">{{ tm }}</el-tag>
        <el-tag v-for="cv in (p.contrarian_views || []).slice(0, 2)" :key="cv" effect="plain" size="small">{{ cv }}</el-tag>
      </div>
      <div v-if="showDetails" style="margin-top: 16px;">
        <!-- Thinking models -->
        <div style="margin-bottom: 16px;">
          <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 8px;">思维模型</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <el-tag v-for="tm in (p.thinking_models || [])" :key="tm" type="danger" effect="light">{{ tm }}</el-tag>
          </div>
        </div>
        <!-- Emotional triggers -->
        <div v-if="p.emotional_triggers" style="margin-bottom: 16px;">
          <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 8px;">情绪触发点</div>
          <div style="display: flex; gap: 16px; flex-wrap: wrap;">
            <div v-if="(p.emotional_triggers.anger || []).length">
              <div style="font-size: 12px; color: #ef4444; margin-bottom: 4px;">😡 愤怒</div>
              <div v-for="a in p.emotional_triggers.anger" :key="a" style="font-size: 12px; color: #606266;">· {{ a }}</div>
            </div>
            <div v-if="(p.emotional_triggers.passion || []).length">
              <div style="font-size: 12px; color: #f59e0b; margin-bottom: 4px;">🔥 热情</div>
              <div v-for="pp in p.emotional_triggers.passion" :key="pp" style="font-size: 12px; color: #606266;">· {{ pp }}</div>
            </div>
            <div v-if="(p.emotional_triggers.pride || []).length">
              <div style="font-size: 12px; color: #10b981; margin-bottom: 4px;">💪 骄傲</div>
              <div v-for="pr in p.emotional_triggers.pride" :key="pr" style="font-size: 12px; color: #606266;">· {{ pr }}</div>
            </div>
          </div>
        </div>
        <!-- Contrarian views -->
        <div v-if="(p.contrarian_views || []).length" style="margin-bottom: 16px;">
          <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 8px;">逆主流观点</div>
          <div v-for="cv in p.contrarian_views" :key="cv" style="font-size: 13px; color: #78350f; padding: 6px 10px; background: #fffbeb; border-radius: 6px; margin-bottom: 4px; border-left: 3px solid #f59e0b;">
            {{ cv }}
          </div>
        </div>
        <!-- Voice fingerprint -->
        <div v-if="p.voice_fingerprint" class="ip-info-block voice-block">
          <div class="block-title">🎤 声音指纹</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
            <div><span style="color: #0369a1; font-weight: bold;">句式：</span><span style="color: #475569;">{{ p.voice_fingerprint.sentence_pattern }}</span></div>
            <div><span style="color: #0369a1; font-weight: bold;">修辞：</span><span style="color: #475569;">{{ p.voice_fingerprint.rhetoric_preference }}</span></div>
            <div><span style="color: #0369a1; font-weight: bold;">论证：</span><span style="color: #475569;">{{ p.voice_fingerprint.argument_structure }}</span></div>
            <div><span style="color: #0369a1; font-weight: bold;">比喻：</span><span style="color: #475569;">{{ p.voice_fingerprint.metaphor_domain }}</span></div>
          </div>
          <div v-if="(p.voice_fingerprint.forbidden_words || []).length" style="margin-top: 10px;">
            <span style="font-size: 12px; color: #ef4444; font-weight: bold;">🚫 禁用词：</span>
            <el-tag v-for="fw in p.voice_fingerprint.forbidden_words" :key="fw" size="small" type="danger" effect="plain" style="margin: 2px;">{{ fw }}</el-tag>
          </div>
          <div v-if="(p.voice_fingerprint.raw_quotes || []).length" style="margin-top: 10px;">
            <div style="font-size: 12px; color: #0369a1; font-weight: bold; margin-bottom: 6px;">📝 原话摘录：</div>
            <div v-for="q in p.voice_fingerprint.raw_quotes" :key="q" style="font-size: 12px; color: #475569; padding: 4px 8px; background: white; border-radius: 4px; margin-bottom: 3px; font-style: italic;">
              "{{ q }}"
            </div>
          </div>
        </div>
        <!-- Opinion bank -->
        <div v-if="(p.opinion_bank || []).length" class="ip-info-block opinion-block">
          <div class="block-title">💡 观点素材库（{{ p.opinion_bank.length }}条）</div>
          <div v-for="op in p.opinion_bank.slice(0, 5)" :key="op.opinion_id" style="font-size: 12px; padding: 8px; background: white; border-radius: 6px; margin-bottom: 6px; border-left: 3px solid #eab308;">
            <div style="font-weight: bold; color: #78350f;">{{ op.topic }} · {{ op.stance }}</div>
            <div style="color: #475569; font-style: italic; margin-top: 2px;">"{{ op.raw_expression }}"</div>
          </div>
        </div>
        <!-- Expression patterns -->
        <div v-if="p.expression_patterns && (p.expression_patterns.preferred_openings || []).length" class="ip-info-block expression-block">
          <div class="block-title">🗣️ 表达模式</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
            <div><span style="color: #15803d; font-weight: bold;">开场：</span><span style="color: #475569;">{{ (p.expression_patterns.preferred_openings || []).join('、') }}</span></div>
            <div><span style="color: #15803d; font-weight: bold;">过渡：</span><span style="color: #475569;">{{ (p.expression_patterns.preferred_transitions || []).join('、') }}</span></div>
            <div><span style="color: #15803d; font-weight: bold;">收尾：</span><span style="color: #475569;">{{ (p.expression_patterns.preferred_closings || []).join('、') }}</span></div>
          </div>
        </div>
        <!-- Business intent -->
        <div v-if="p.business_intent" style="margin-bottom: 16px;">
          <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 8px;">🎯 商业意图</div>
          <div style="font-size: 12px; color: #606266; line-height: 1.8;">
            <div><strong>核心目的：</strong>{{ p.business_intent.primary_goal }}</div>
            <div><strong>目标印象：</strong>{{ p.business_intent.target_perception }}</div>
            <div><strong>竞争差异：</strong>{{ p.business_intent.competitive_context }}</div>
          </div>
        </div>
        <!-- Identity attitude -->
        <div v-if="p.identity_attitude">
          <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 8px;">🎭 身份态度</div>
          <div style="font-size: 12px; color: #606266; line-height: 1.8;">
            <div><strong>身份定位：</strong>{{ p.identity_attitude.status_level }}</div>
            <div><strong>沟通基调：</strong>{{ p.identity_attitude.communication_tone }}</div>
            <div><strong>开场偏好：</strong>{{ p.identity_attitude.hook_preference }}</div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Quick action bar -->
    <div style="display: flex; gap: 10px; margin-bottom: 20px;">
      <el-button type="warning" size="large" @click="autoFlow" :loading="generatingTopics || generatingScript"
        style="font-size: 15px; padding: 12px 28px; font-weight: bold;">
        🚀 一键生成脚本
      </el-button>
      <el-button type="info" plain @click="startSupplementInterview">🎙️ 继续访谈（完善形象）</el-button>
    </div>

    <!-- Topic library header -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3 style="margin: 0;">📋 选题库 <span style="font-size: 13px; font-weight: normal; color: #909399;">（{{ store.topics.length }} 个选题）</span></h3>
      <el-button type="warning" @click="generateTopics" :loading="generatingTopics">
        {{ store.topics.length > 0 ? '🔄 重新生成选题' : '✨ 生成选题库（15个）' }}
      </el-button>
    </div>

    <!-- Generating spinner -->
    <div v-if="generatingTopics" style="text-align: center; padding: 40px;">
      <el-icon class="is-loading" :size="40" style="color: #f59e0b;"><Loading /></el-icon>
      <p style="color: #909399; margin-top: 12px;">AI正在基于你的真实故事、观点和商业目标生成选题...</p>
    </div>

    <el-empty v-else-if="store.topics.length === 0" description="点击上方按钮，AI将基于你的IP档案生成15个专属选题" />

    <!-- Topic cards grid -->
    <el-row :gutter="16" v-if="!generatingTopics">
      <el-col :span="12" v-for="topic in store.topics" :key="topic.topic_id" style="margin-bottom: 16px;">
        <el-card shadow="hover" style="height: 100%;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
              <div style="flex: 1;">
                <el-tag :type="topicTypeTag(topic.type)" size="small" style="margin-bottom: 6px;">{{ topic.type }}</el-tag>
                <div style="font-weight: bold; font-size: 15px; line-height: 1.4;">{{ topic.title }}</div>
              </div>
              <el-button type="warning" size="small" @click="openScriptGenerator(topic)" style="flex-shrink: 0;">写脚本</el-button>
            </div>
          </template>
          <div style="font-size: 13px; padding: 8px 12px; background: #fffbeb; border-radius: 6px; border-left: 3px solid #f59e0b; margin-bottom: 10px; color: #78350f; font-style: italic; line-height: 1.5;">
            "{{ topic.hook_opening }}"
          </div>
          <div style="font-size: 12px; color: #606266; margin-bottom: 8px;">{{ topic.core_angle }}</div>
          <div v-if="topic.strategic_angle" style="font-size: 11px; color: #0369a1; padding: 4px 8px; background: #f0f9ff; border-radius: 4px; margin-bottom: 6px;">
            🎯 {{ topic.strategic_angle }}
          </div>
          <div v-if="topic.why_viral" style="font-size: 11px; color: #909399;">💡 {{ topic.why_viral }}</div>
          <div style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 11px; color: #bbb;">建议时长：{{ topic.estimated_duration }}秒</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
