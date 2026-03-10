<script setup lang="ts">
import { useStoryboardStore } from '../../../stores/storyboard'

const store = useStoryboardStore()

const hookOptions = [
  { value: '', label: 'AI自动选择' },
  { value: 'pain_point', label: '痛点型 - 直击用户焦虑，引发共鸣' },
  { value: 'data_shock', label: '数据型 - 用数字制造冲击' },
  { value: 'contrast', label: '对比型 - Before/After强烈反差' },
  { value: 'reverse', label: '反转型 - 开头反常识吸引停留' },
  { value: 'scene_immersion', label: '场景型 - 代入使用场景' },
]

const styleOptions = [
  { value: 'cinematic', label: '质感大片', icon: '🎬' },
  { value: 'lifestyle', label: '生活种草', icon: '🏠' },
  { value: 'demo', label: '产品测评', icon: '🔬' },
  { value: 'vlog', label: '真人口播', icon: '🎤' },
]

const examples = [
  { text: '戴森Airwrap美发器', detail: '一机六合一，康达效应气流造型不伤发，30秒沙龙级造型' },
  { text: '添可洗地机', detail: '吸拖洗一体，热风速干不发臭，懒人家务神器' },
  { text: '瑞幸生椰拿铁', detail: '椰奶+浓缩咖啡，低糖0反式脂肪，打工人续命神器' },
  { text: '花西子空气蜜粉', detail: '轻薄控油不卡粉，养肤成分，一整天不脱妆' },
]

const fillExample = (ex: typeof examples[0]) => {
  store.userInput = ex.text
  store.productDetail = ex.detail
}
</script>

<template>
  <div class="input-section">
    <!-- 产品信息 -->
    <div class="input-card">
      <h3>产品名称</h3>
      <el-input
        v-model="store.userInput"
        placeholder="输入要推广的产品名称，如：戴森Airwrap美发器"
        maxlength="100"
        show-word-limit
      />
      <div class="examples">
        <span class="examples-label">热门:</span>
        <el-tag
          v-for="(ex, i) in examples"
          :key="i"
          class="example-tag"
          effect="plain"
          @click="fillExample(ex)"
        >{{ ex.text }}</el-tag>
      </div>
    </div>

    <div class="input-card">
      <h3>产品卖点/详情</h3>
      <el-input
        v-model="store.productDetail"
        type="textarea"
        :rows="3"
        placeholder="核心卖点、功能特点、目标用户、与竞品区别...填得越详细，脚本越精准"
        maxlength="500"
        show-word-limit
      />
    </div>

    <!-- 配置行 -->
    <div class="config-row">
      <div class="input-card config-item">
        <h3>视频风格</h3>
        <div class="style-grid">
          <div
            v-for="s in styleOptions"
            :key="s.value"
            class="style-option"
            :class="{ active: store.style === s.value }"
            @click="store.style = s.value"
          >
            <span class="style-icon">{{ s.icon }}</span>
            <span class="style-label">{{ s.label }}</span>
          </div>
        </div>
      </div>

      <div class="input-card config-item">
        <h3>Hook类型</h3>
        <el-select v-model="store.hookType" placeholder="AI自动选择" clearable style="width:100%">
          <el-option
            v-for="h in hookOptions"
            :key="h.value"
            :value="h.value || null"
            :label="h.label"
          />
        </el-select>

        <h3 style="margin-top:16px">目标时长</h3>
        <el-slider
          v-model="store.totalDuration"
          :min="15"
          :max="120"
          :step="5"
          :marks="{ 15: '15s', 30: '30s', 45: '45s', 60: '60s' }"
          show-input
          :show-input-controls="false"
          input-size="small"
        />
      </div>
    </div>

    <!-- 行业（可选） -->
    <div class="input-card">
      <h3>行业 <el-tag size="small" type="info">可选</el-tag></h3>
      <el-input
        v-model="store.characterDescription"
        placeholder="如：个护美容、食品饮料、3C数码、家居清洁...不填则AI自动判断"
        maxlength="50"
      />
    </div>

    <!-- 生成按钮 -->
    <div class="generate-btn-wrap">
      <el-button
        type="primary"
        size="large"
        :loading="store.generating"
        :disabled="!store.userInput.trim()"
        @click="store.startGenerate()"
        class="generate-btn"
      >
        {{ store.generating ? 'AI多Agent协作中...' : '生成卖货分镜脚本' }}
      </el-button>
      <p class="generate-hint" v-if="!store.generating">Director策略 → Screenwriter分镜 → Producer质审</p>
    </div>
  </div>
</template>

<style scoped>
.input-section { display: flex; flex-direction: column; gap: 16px; }
.input-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.input-card h3 { margin: 0 0 12px; font-size: 15px; color: #303133; }

.examples { display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.examples-label { font-size: 13px; color: #909399; }
.example-tag { cursor: pointer; }
.example-tag:hover { color: #409eff; border-color: #409eff; }

.config-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 768px) { .config-row { grid-template-columns: 1fr; } }

.style-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.style-option {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 10px 4px; border-radius: 8px; border: 2px solid #ebeef5;
  cursor: pointer; transition: all 0.2s;
}
.style-option:hover { border-color: #c0c4cc; }
.style-option.active { border-color: #409eff; background: #ecf5ff; }
.style-icon { font-size: 24px; }
.style-label { font-size: 12px; color: #606266; }

.generate-btn-wrap { text-align: center; padding: 8px 0; }
.generate-btn { min-width: 260px; height: 48px; font-size: 16px; border-radius: 24px; }
.generate-hint { margin: 8px 0 0; font-size: 12px; color: #909399; }
</style>
