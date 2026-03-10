<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useScriptCreatorStore } from '../../../stores/scriptCreator'
import { extractProductInfo } from '../../../api/scriptCreator'
import TemplateSelector from './TemplateSelector.vue'

const store = useScriptCreatorStore()
const showTemplateDialog = ref(false)
const extracting = ref(false)
const urlInput = ref('')
const inputMode = ref<'manual' | 'url' | 'image'>('manual')

const industryOptions = [
  { label: '美妆护肤', value: '美妆护肤' },
  { label: '食品保健', value: '食品保健' },
  { label: '数码3C', value: '数码3C' },
  { label: '服装鞋包', value: '服装鞋包' },
  { label: '家居生活', value: '家居生活' },
  { label: '教育培训', value: '教育培训' },
  { label: '母婴', value: '母婴' },
  { label: '其他', value: '其他' },
]

const ensureProductInfo = () => {
  if (!store.productInfo) {
    store.productInfo = {
      product_name: '',
      category: '',
      price_range: '',
      core_features: [],
      target_audience: '',
      use_cases: [],
      differentiators: [],
      brand_tone: '',
      raw_content: '',
    }
  }
}

const handleExtractUrl = async () => {
  if (!urlInput.value.trim()) return
  extracting.value = true
  try {
    const res: any = await extractProductInfo('url', urlInput.value)
    const info = res.product_info
    if (info) {
      store.productInfo = info
      inputMode.value = 'manual'
      ElMessage.success(`已提取产品信息: ${info.product_name}`)
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '链接提取失败')
  } finally {
    extracting.value = false
  }
}

const handleImageUpload = async (file: { raw: File }) => {
  extracting.value = true
  try {
    const reader = new FileReader()
    const base64 = await new Promise<string>((resolve) => {
      reader.onload = () => resolve((reader.result as string).split(',')[1] || '')
      reader.readAsDataURL(file.raw)
    })
    const res: any = await extractProductInfo('image', base64)
    if (res.product_info) {
      store.productInfo = res.product_info
      inputMode.value = 'manual'
      ElMessage.success(`已识别产品: ${res.product_info.product_name}`)
    }
  } catch (e: any) {
    ElMessage.error('图片识别失败')
  } finally {
    extracting.value = false
  }
}

// Deep mode
const deepInput = ref('')
const deepChatBox = ref<HTMLElement>()
const userScriptInput = ref('')
const showUserScript = ref(false)
const deepStarted = ref(false)

const handleDeepSend = async () => {
  if (!deepInput.value.trim() || store.deepLoading) return
  const msg = deepInput.value
  deepInput.value = ''
  const res = await store.sendDeepChat(msg)
  await nextTick()
  if (deepChatBox.value) deepChatBox.value.scrollTop = deepChatBox.value.scrollHeight
  if (res?.script_ready) {
    ElMessage.success('已检测到生成意图，点击下方按钮生成脚本')
  }
}

const startDeepChat = async () => {
  store.mode = 'deep'
  deepStarted.value = true
  // 初始欢迎消息
  store.deepMessages.push({
    role: 'ai',
    content: '你好！我是你的短视频创意顾问。告诉我你想推广什么产品，或者试试下面的快捷操作：\n\n- 帮我找灵感：从抖音热搜、小红书等实时数据中挖掘创意角度\n- 搜一下XX：搜索相关爆款视频\n- 分析链接：拆解竞品视频结构\n\n准备好了就开始吧！',
  })
  await nextTick()
  if (deepChatBox.value) deepChatBox.value.scrollTop = deepChatBox.value.scrollHeight
}

const handleDeepQuickAction = async (action: string) => {
  if (action === 'inspire') {
    if (!store.productInfo?.product_name) {
      ElMessage.warning('请先在消息中告诉我你的产品名称')
      return
    }
    await store.getInspirations()
  } else if (action === 'idea') {
    deepInput.value = '我有个想法，我想做一个关于'
  } else if (action === 'link') {
    deepInput.value = '帮我分析这个视频 '
  }
  await nextTick()
  if (deepChatBox.value) deepChatBox.value.scrollTop = deepChatBox.value.scrollHeight
}

const handleInspirationClick = async (ins: any) => {
  deepInput.value = `就用"${ins.angle}"这个角度，Hook用：${ins.suggested_hook}`
  await handleDeepSend()
}

const handleDeepGenerate = async () => {
  await store.generateFromDeepConversation()
  ElMessage.success('脚本生成完成')
}

const handleTemplateSelected = (t: any) => {
  store.selectedTemplate = t
  showTemplateDialog.value = false
}

const handleSkipToPreview = async () => {
  if (!userScriptInput.value.trim()) return
  await store.skipToPreview(userScriptInput.value.trim())
  ElMessage.success('脚本解析完成，进入分镜预览')
}
</script>

<template>
  <div style="max-width: 660px; margin: 30px auto;">
    <!-- Mode toggle -->
    <div style="text-align: center; margin-bottom: 24px;">
      <el-radio-group v-model="store.mode" size="large">
        <el-radio-button value="quick">⚡ 快速模式</el-radio-button>
        <el-radio-button value="data_driven">📊 数据驱动</el-radio-button>
        <el-radio-button value="deep">🤖 深度定制</el-radio-button>
      </el-radio-group>
      <div style="font-size: 13px; color: #909399; margin-top: 8px;">
        {{ store.mode === 'quick' ? '填写产品信息，秒出3个创意方向'
           : store.mode === 'data_driven' ? '分析真实爆款视频+评论，数据驱动生成脚本（约3-5分钟）'
           : 'AI创意工作室：对话+实时数据搜索+灵感推荐，量身定制脚本' }}
      </div>
    </div>

    <!-- Quick mode & Data-driven mode (share same input form) -->
    <el-card v-if="store.mode === 'quick' || store.mode === 'data_driven'" shadow="always">
      <template #header>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 18px;">{{ store.mode === 'data_driven' ? '📊' : '⚡' }}</span>
          <span style="font-weight: bold; font-size: 16px;">{{ store.mode === 'data_driven' ? '数据驱动创作' : '快速创作' }}</span>
          <el-tag :type="store.mode === 'data_driven' ? 'warning' : 'success'" size="small">{{ store.mode === 'data_driven' ? '深度调研' : '推荐' }}</el-tag>
          <div style="margin-left: auto;">
            <el-button text size="small" @click="showTemplateDialog = true">📋 选择模板</el-button>
          </div>
        </div>
      </template>

      <!-- Input mode tabs -->
      <div style="display: flex; gap: 6px; margin-bottom: 16px;">
        <el-button :type="inputMode === 'manual' ? 'primary' : 'default'" size="small" plain @click="inputMode = 'manual'">✏️ 手动输入</el-button>
        <el-button :type="inputMode === 'url' ? 'primary' : 'default'" size="small" plain @click="inputMode = 'url'">🔗 粘贴链接</el-button>
        <el-button :type="inputMode === 'image' ? 'primary' : 'default'" size="small" plain @click="inputMode = 'image'">🖼️ 上传图片</el-button>
      </div>

      <!-- URL extraction -->
      <div v-if="inputMode === 'url'" style="margin-bottom: 16px;">
        <el-input v-model="urlInput" placeholder="粘贴产品页面链接（淘宝/京东/小红书等）" size="large" clearable>
          <template #append>
            <el-button :loading="extracting" @click="handleExtractUrl">提取</el-button>
          </template>
        </el-input>
        <div style="font-size: 12px; color: #909399; margin-top: 4px;">AI将自动抓取页面内容，提取产品名称和卖点</div>
      </div>

      <!-- Image upload -->
      <div v-if="inputMode === 'image'" style="margin-bottom: 16px;">
        <el-upload :auto-upload="false" accept="image/*" :show-file-list="false" @change="handleImageUpload" drag>
          <div style="padding: 20px; text-align: center;">
            <el-icon :size="40" style="color: #909399;"><Upload /></el-icon>
            <p style="color: #909399; margin-top: 8px;">{{ extracting ? '正在识别...' : '拖拽或点击上传产品图片' }}</p>
          </div>
        </el-upload>
      </div>

      <!-- Manual form (always shown, auto-filled from extraction) -->
      <el-form label-width="72px" style="margin-top: 4px;">
        <el-form-item label="产品" required>
          <el-input
            :model-value="store.productInfo?.product_name || ''"
            placeholder="如：美白面霜、智能手表、蛋白粉"
            maxlength="50"
            size="large"
            clearable
            @update:model-value="(v: string) => { ensureProductInfo(); store.productInfo!.product_name = v; }"
          />
        </el-form-item>
        <el-form-item label="品类">
          <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            <span
              v-for="ind in industryOptions"
              :key="ind.value"
              @click="ensureProductInfo(); store.productInfo!.category = (store.productInfo!.category === ind.value ? '' : ind.value)"
              :style="{
                display: 'inline-block', padding: '4px 14px', borderRadius: '16px', cursor: 'pointer', fontSize: '13px',
                border: '1px solid', userSelect: 'none', transition: 'all 0.2s',
                borderColor: store.productInfo?.category === ind.value ? '#409eff' : '#dcdfe6',
                background: store.productInfo?.category === ind.value ? '#409eff' : '#fff',
                color: store.productInfo?.category === ind.value ? '#fff' : '#606266',
              }"
            >
              {{ ind.label }}
            </span>
          </div>
        </el-form-item>
        <el-form-item label="时长">
          <el-radio-group v-model="store.targetDuration">
            <el-radio-button :value="30">30秒</el-radio-button>
            <el-radio-button :value="60">60秒</el-radio-button>
            <el-radio-button :value="120">2分钟</el-radio-button>
            <el-radio-button :value="180">3分钟</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button
            v-if="store.mode === 'quick'"
            type="primary"
            size="large"
            @click="store.startResearch"
            :disabled="!store.productInfo?.product_name?.trim()"
            :loading="store.loading"
            style="width: 100%; font-size: 15px;"
          >
            ⚡ 快速生成脚本
          </el-button>
          <el-button
            v-else-if="store.mode === 'data_driven'"
            type="primary"
            size="large"
            @click="store.startDataDrivenResearch"
            :disabled="!store.productInfo?.product_name?.trim()"
            :loading="store.loading"
            style="width: 100%; font-size: 15px;"
          >
            📊 数据驱动生成（分析爆款+评论+创意）
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Deep mode: Creative Studio -->
    <el-card v-else shadow="always" class="deep-studio">
      <template #header>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 18px;">🤖</span>
          <span style="font-weight: bold; font-size: 16px;">AI创意工作室</span>
          <el-tag type="warning" size="small">数据+对话</el-tag>
        </div>
      </template>

      <!-- 产品名称快速输入（首次使用） -->
      <div v-if="!deepStarted" style="margin-bottom: 12px;">
        <el-input
          :model-value="store.productInfo?.product_name || ''"
          placeholder="先告诉我你的产品名称（如：美白面霜）"
          size="large"
          @update:model-value="(v: string) => { ensureProductInfo(); store.productInfo!.product_name = v; }"
        >
          <template #prepend>产品</template>
        </el-input>
        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;">
          <span
            v-for="ind in industryOptions" :key="ind.value"
            @click="ensureProductInfo(); store.productInfo!.category = ind.value"
            :style="{
              padding: '3px 10px', borderRadius: '12px', cursor: 'pointer', fontSize: '12px',
              border: '1px solid', userSelect: 'none',
              borderColor: store.productInfo?.category === ind.value ? '#409eff' : '#dcdfe6',
              background: store.productInfo?.category === ind.value ? '#ecf5ff' : '#fff',
              color: store.productInfo?.category === ind.value ? '#409eff' : '#909399',
            }"
          >{{ ind.label }}</span>
        </div>
      </div>

      <!-- Chat area -->
      <div ref="deepChatBox" style="min-height: 240px; max-height: 420px; overflow-y: auto; padding: 14px; background: #f8f9fa; border-radius: 8px; margin-bottom: 12px;">
        <template v-if="store.deepMessages.length > 0">
          <div v-for="(msg, i) in store.deepMessages" :key="i" style="margin-bottom: 14px;">
            <!-- AI message -->
            <div v-if="msg.role === 'ai'" style="display: flex; align-items: flex-start; gap: 10px;">
              <div style="width: 30px; height: 30px; border-radius: 50%; background: linear-gradient(135deg, #409eff, #67c23a); display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; font-weight: bold; flex-shrink: 0;">AI</div>
              <div style="flex: 1; max-width: 84%;">
                <div style="background: white; border: 1px solid #e4e7ed; border-radius: 2px 12px 12px 12px; padding: 10px 14px; font-size: 14px; color: #303133; line-height: 1.7; white-space: pre-line; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">{{ msg.content }}</div>

                <!-- Tool data cards -->
                <div v-if="msg.tool_used === 'search_douyin' && msg.tool_data?.videos" class="tool-card">
                  <div class="tool-card-header">抖音视频搜索结果</div>
                  <div v-for="(v, vi) in msg.tool_data.videos.slice(0, 3)" :key="vi" class="tool-card-item">
                    <span>{{ v.description?.slice(0, 35) }}...</span>
                    <el-tag size="small" type="danger">{{ v.play_count >= 10000 ? (v.play_count/10000).toFixed(1) + '万' : v.play_count }}播放</el-tag>
                  </div>
                </div>

                <div v-if="msg.tool_used === 'search_xiaohongshu' && msg.tool_data?.notes" class="tool-card">
                  <div class="tool-card-header">小红书笔记</div>
                  <div v-for="(n, ni) in msg.tool_data.notes.slice(0, 3)" :key="ni" class="tool-card-item">
                    <span>{{ n.title?.slice(0, 30) }}</span>
                    <el-tag size="small">{{ n.liked_count }}赞</el-tag>
                  </div>
                </div>

                <div v-if="msg.tool_used === 'get_hot_topics' && msg.tool_data?.topics" class="tool-card">
                  <div class="tool-card-header">抖音热搜</div>
                  <div v-for="(t, ti) in msg.tool_data.topics.slice(0, 5)" :key="ti" class="tool-card-item">
                    <span>{{ t.position }}. {{ t.title }}</span>
                  </div>
                </div>

                <!-- Inspiration cards -->
                <div v-if="msg.tool_used === 'inspiration' && msg.tool_data?.inspirations" class="inspiration-cards">
                  <div
                    v-for="(ins, ii) in msg.tool_data.inspirations" :key="ii"
                    class="inspiration-card"
                    @click="handleInspirationClick(ins)"
                  >
                    <div class="ins-angle">{{ ins.angle }}</div>
                    <div class="ins-source"><el-tag size="small" type="info">{{ ins.source }}</el-tag></div>
                    <div class="ins-backing">{{ ins.data_backing }}</div>
                    <div class="ins-hook">{{ ins.suggested_hook }}</div>
                  </div>
                </div>
              </div>
            </div>
            <!-- User message -->
            <div v-else style="display: flex; justify-content: flex-end;">
              <div style="background: #409eff; border-radius: 12px 2px 12px 12px; padding: 10px 14px; max-width: 84%; font-size: 14px; color: white; line-height: 1.7;">{{ msg.content }}</div>
            </div>
          </div>

          <!-- Loading indicator -->
          <div v-if="store.deepLoading" style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 30px; height: 30px; border-radius: 50%; background: linear-gradient(135deg, #409eff, #67c23a); display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; font-weight: bold; flex-shrink: 0;">AI</div>
            <div style="background: white; border: 1px solid #e4e7ed; border-radius: 2px 12px 12px 12px; padding: 10px 14px; color: #909399; font-size: 13px;">思考中...</div>
          </div>
        </template>
        <div v-else style="text-align: center; padding: 60px 20px; color: #909399;">
          <p style="font-size: 15px; margin-bottom: 12px;">AI创意工作室 — 对话式创作 + 实时数据</p>
          <p style="font-size: 13px;">输入产品名称，点击"开始创作"</p>
        </div>
      </div>

      <!-- Quick action buttons -->
      <div v-if="deepStarted" style="display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap;">
        <el-button size="small" round @click="handleDeepQuickAction('idea')">💡 我有个想法</el-button>
        <el-button size="small" round type="warning" @click="handleDeepQuickAction('inspire')" :loading="store.deepLoading">🔥 帮我找灵感</el-button>
        <el-button size="small" round @click="handleDeepQuickAction('link')">📎 分析链接</el-button>
      </div>

      <!-- Chat input -->
      <div v-if="!deepStarted">
        <el-button type="primary" size="large" @click="startDeepChat" :disabled="!store.productInfo?.product_name?.trim()" style="width: 100%;">开始创作</el-button>
      </div>
      <div v-if="deepStarted" style="display: flex; gap: 8px;">
        <el-input v-model="deepInput" placeholder="聊聊你的创意想法，或试试'帮我搜XX视频'..." @keyup.enter="handleDeepSend" size="large" :disabled="store.deepLoading" clearable />
        <el-button type="primary" @click="handleDeepSend" :disabled="!deepInput.trim() || store.deepLoading" size="large">发送</el-button>
      </div>

      <!-- Generate button -->
      <div v-if="store.deepMessages.length >= 4" style="text-align: center; margin-top: 14px;">
        <el-button type="success" size="large" @click="handleDeepGenerate" :loading="store.loading" style="padding: 12px 36px; font-size: 15px;">
          就这个方向，出脚本 →
        </el-button>
        <div style="font-size: 12px; color: #909399; margin-top: 4px;">保留完整对话上下文生成3个脚本</div>
      </div>

      <!-- 用户自带脚本 -->
      <el-divider />
      <div style="margin-top: 8px;">
        <el-button text type="primary" @click="showUserScript = !showUserScript">
          {{ showUserScript ? '收起' : '我有自己的脚本，直接预览' }}
        </el-button>
        <div v-if="showUserScript" style="margin-top: 12px;">
          <el-input
            v-model="userScriptInput"
            type="textarea"
            :rows="6"
            placeholder="粘贴你的脚本文案，AI会自动解析为分镜格式..."
          />
          <div style="display: flex; gap: 8px; margin-top: 8px; align-items: center;">
            <span style="font-size: 13px; color: #909399;">目标时长:</span>
            <el-radio-group v-model="store.targetDuration" size="small">
              <el-radio-button :value="30">30s</el-radio-button>
              <el-radio-button :value="60">60s</el-radio-button>
              <el-radio-button :value="120">2min</el-radio-button>
            </el-radio-group>
            <el-button
              type="success"
              :disabled="!userScriptInput.trim()"
              :loading="store.loading"
              @click="handleSkipToPreview"
              style="margin-left: auto;"
            >
              解析并预览分镜
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <TemplateSelector v-model="showTemplateDialog" @select="handleTemplateSelected" />
  </div>
</template>

<style scoped>
/* Deep Studio: Tool data cards */
.tool-card {
  margin-top: 8px;
  background: #f0f7ff;
  border: 1px solid #d9ecff;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
}
.tool-card-header {
  font-weight: bold;
  color: #409eff;
  margin-bottom: 6px;
  font-size: 12px;
}
.tool-card-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  color: #606266;
  gap: 8px;
}
.tool-card-item span:first-child {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Inspiration cards */
.inspiration-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.inspiration-card {
  flex: 1;
  min-width: 180px;
  background: linear-gradient(135deg, #fff7e6, #fff1cc);
  border: 1px solid #ffd666;
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.inspiration-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 214, 102, 0.3);
}
.ins-angle {
  font-weight: bold;
  font-size: 14px;
  color: #d48806;
  margin-bottom: 4px;
}
.ins-source {
  margin-bottom: 4px;
}
.ins-backing {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 4px;
  line-height: 1.4;
}
.ins-hook {
  font-size: 13px;
  color: #fa8c16;
  font-style: italic;
}
</style>
