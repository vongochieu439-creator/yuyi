<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listTemplates } from '../../api/templates'
import type { Template } from '../../types'
import { useRouter } from 'vue-router'

const router = useRouter()
const templates = ref<Template[]>([])
const loading = ref(false)
const tTab = ref('KOL风格')
const fp = ref('全部')
const tabs = ['KOL风格', '营销方法论', '行业专属']
const platFilters = ['全部', '抖音', '小红书', '视频号']

const staticTemplates = [
  { id: 1, name: '李佳琦种草公式', plat: '抖音', desc: 'OMG 买它逻辑，强调痛点+即时效果+价格锚点', tags: ['美妆头部', '高转化'], stat: '+25%', uses: '新上线' },
  { id: 2, name: '张同学乡村叙事', plat: '抖音', desc: '快节奏剪辑+沉浸式生活场景，软植入自然不突兀', tags: ['三农/食品', '生活化'], stat: '+30%', uses: '1.2w+次' },
  { id: 3, name: '罗永浩理性测评', plat: '视频号', desc: '参数罗列+幽默吐槽+硬核对比，建立信任感', tags: ['数码3C', '专业测评'], stat: '+22%', uses: '8.5k+次' },
  { id: 4, name: 'PAS痛点放大法', plat: '通用', desc: 'Problem - Agitation - Solution，经典营销理论', tags: ['知识付费', '理论模型'], stat: '+18%', uses: '15.3k+次' },
  { id: 5, name: '小红书种草笔记', plat: '小红书', desc: '真实体验+使用心得+购买链接，图文并茂', tags: ['美妆护肤', '种草'], stat: '+20%', uses: '3.2k+次' },
  { id: 6, name: '薇娅直播切片', plat: '抖音', desc: '限时抢购+库存紧张+价格优势，直播电商核心', tags: ['电商直播', '紧迫感'], stat: '+28%', uses: '5.7k+次' },
]

const filteredTemplates = computed(() => {
  return staticTemplates.filter(t => fp.value === '全部' || t.plat === fp.value)
})

const loadTemplates = async () => {
  loading.value = true
  try {
    const res: any = await listTemplates({})
    if (res?.templates?.length) templates.value = res.templates
  } catch {}
  finally { loading.value = false }
}

function useTemplate(_t: any) {
  router.push('/script-creator')
}

onMounted(loadTemplates)
</script>

<template>
  <div class="sc">
    <!-- Tabs -->
    <div class="tt">
      <button v-for="t in tabs" :key="t" class="tti" :class="{ on: tTab === t }" @click="tTab = t">{{ t }}</button>
    </div>

    <!-- Platform filter -->
    <div class="fr">
      <div class="fg">
        <span class="fl">平台</span>
        <div class="fcs">
          <button v-for="f in platFilters" :key="f" class="fc2" :class="{ on: fp === f }" @click="fp = f">{{ f }}</button>
        </div>
      </div>
    </div>

    <!-- Grid -->
    <div class="tg2">
      <div v-for="t in filteredTemplates" :key="t.id" class="tc">
        <div class="tc-tp">
          <span>{{ t.plat }}</span>
          <span>{{ t.uses }}</span>
        </div>
        <div class="tc-n">{{ t.name }}</div>
        <div class="tc-d">{{ t.desc }}</div>
        <div class="tc-tgs">
          <span v-for="tg in t.tags" :key="tg" class="tc-tg">{{ tg }}</span>
        </div>
        <div class="tc-bot">
          <span class="tc-st">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 23c-3.6 0-8-2.4-8-7.7 0-3.5 2.1-6.4 4-8.8.6-.8 1.8-.3 1.7.7-.2 1.6.3 3.3 1.5 4.5.2.2.5.1.6-.2.4-1.6 1.5-3.5 3.2-5.2.5-.5 1.4-.2 1.4.5 0 2.2.8 4.1 2.1 5.5.9 1 1.5 2.3 1.5 3.8 0 4-3 6.9-8 6.9z"/></svg>
            完播率 {{ t.stat }}
          </span>
          <button class="tc-bt" @click="useTemplate(t)">用此模板创建 →</button>
        </div>
      </div>
    </div>
  </div>
</template>
