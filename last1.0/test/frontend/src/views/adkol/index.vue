<script setup lang="ts">
import { ref } from 'vue'

const searchQuery = ref('')
const platform = ref('')
const tagFilter = ref('')
const priceRange = ref('')
const sortBy = ref('')

const kols = [
  { nm: '山白', id: 10283, cat: '抖音 · 才艺技能', desc: '叔侄两人，拍一些乡里间的手艺活儿，视频质感高，传统文化创作者', fans: '1618.5万', price: '¥200,000', tags: ['才艺技能', '非遗'], loc: '湖南省', bg: '#3B82F6' },
  { nm: '王小怪', id: 66716, cat: '抖音 · 萌宠', desc: '一个家里养了几百只宠物的宠物达人，幕后故事，宠物日常', fans: '1159.7万', price: '¥140,000', tags: ['萌宠', '日常'], loc: '辽宁省', bg: '#F59E0B' },
  { nm: '艾维奇Vic', id: 83562, cat: '抖音 · 生活', desc: '偶遇+猎奇各种职业，通过访问访谈切入主题，了解大咖观点', fans: '754.5万', price: '¥300,000', tags: ['生活', '汽车'], loc: '上海', bg: '#7C3AED' },
  { nm: '卢克文工作室', id: 20018, cat: '抖音 · 知识科普', desc: '畅销书作者，知识科普人文类创作者，热点分析', fans: '933万', price: '¥160,000', tags: ['知识科普', '人文'], loc: '成都市', bg: '#10B981' },
  { nm: '方也', id: 10830, cat: '抖音 · 旅行', desc: '与传统非遗文化结合产出创意短片，摇臂汽车短片，文化类创意', fans: '800.5万', price: '¥210,000', tags: ['旅行', '艺术文化'], loc: '南京市', bg: '#6366F1' },
  { nm: '焦绿儿', id: 33847, cat: '抖音 · 旅行', desc: '高颜值旅行类达人，文案优美，风格清新自然，打卡全国标志性地域', fans: '754.1万', price: '¥218,000', tags: ['旅行', '时尚'], loc: '南京市', bg: '#EC4899' },
  { nm: '草莓朵朵', id: 66888, cat: '抖音 · 生活', desc: '记录日常生活中的点滴，内容涵盖美妆美食，传递甜蜜温馨的氛围', fans: '1063.5万', price: '¥50,000', tags: ['生活', '剧情'], loc: '重庆市', bg: '#F59E0B' },
  { nm: '长沙一家人', id: 20021, cat: '抖音 · 母婴亲子', desc: '记录一家人进行各种游戏挑战的搞笑日常，聚会游戏大挑战', fans: '1008.6万', price: '¥50,000', tags: ['母婴亲子', '搞笑'], loc: '长沙市', bg: '#EF4444' },
]
</script>

<template>
  <div class="kol-wrap">
    <div class="kol-search">
      <input v-model="searchQuery" placeholder="搜索达人昵称或ID..." />
      <button class="kol-search-btn">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        搜索
      </button>
    </div>

    <div class="kol-filters">
      <div class="kol-fg">
        <div class="kol-fg-l">平台类型</div>
        <select v-model="platform"><option>全部平台</option><option>抖音</option><option>快手</option><option>小红书</option><option>TikTok</option></select>
      </div>
      <div class="kol-fg">
        <div class="kol-fg-l">标签</div>
        <select v-model="tagFilter"><option>全部标签</option><option>美妆</option><option>科技</option><option>美食</option><option>旅行</option></select>
      </div>
      <div class="kol-fg">
        <div class="kol-fg-l">价格区间</div>
        <select v-model="priceRange"><option>不限价格</option><option>5万以下</option><option>5-20万</option><option>20万以上</option></select>
      </div>
      <div class="kol-fg">
        <div class="kol-fg-l">排序方式</div>
        <select v-model="sortBy"><option>综合排序</option><option>粉丝数</option><option>报价</option></select>
      </div>
    </div>

    <div class="kol-grid">
      <div v-for="k in kols" :key="k.id" class="kol-card">
        <div class="kol-card-top">
          <div class="kol-card-av" :style="{ background: k.bg }">{{ k.nm[0] }}</div>
          <div style="flex:1;min-width:0;">
            <div style="display:flex;align-items:center;gap:8px;">
              <div class="kol-card-nm">{{ k.nm }}</div>
              <div class="kol-card-id">ID: {{ k.id }}</div>
            </div>
            <div class="kol-card-cat">{{ k.cat }}</div>
            <div class="kol-card-desc">{{ k.desc }}</div>
          </div>
        </div>
        <div class="kol-card-stats">
          <div class="kol-stat"><div class="kol-stat-l">粉丝数</div><div class="kol-stat-v">{{ k.fans }}</div></div>
          <div class="kol-stat"><div class="kol-stat-l">互动率</div><div class="kol-stat-v">-</div></div>
          <div class="kol-stat"><div class="kol-stat-l">预估报价</div><div class="kol-stat-v" style="color:var(--t1);">{{ k.price }}</div></div>
        </div>
        <div class="kol-card-foot">
          <div class="kol-card-tags">
            <span v-for="tag in k.tags" :key="tag">{{ tag }}</span>
          </div>
          <div class="kol-card-loc">📍 {{ k.loc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
