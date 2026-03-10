<script setup lang="ts">
import { ref, computed } from 'vue'

const schMonth = ref(new Date().getMonth())
const schYear = ref(new Date().getFullYear())
const schModal = ref(false)
const schTab = ref(0)
const schColor = ref(0)

const monthNames = ['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月']

const calDays = computed(() => {
  const first = new Date(schYear.value, schMonth.value, 1)
  const last  = new Date(schYear.value, schMonth.value + 1, 0)
  const startDay = (first.getDay() + 6) % 7
  const days: Array<{d:number,cur:boolean,today?:boolean}> = []
  const prev = new Date(schYear.value, schMonth.value, 0).getDate()
  for (let i = startDay - 1; i >= 0; i--) days.push({ d: prev - i, cur: false })
  const now = new Date()
  for (let i = 1; i <= last.getDate(); i++) {
    days.push({ d: i, cur: true, today: i === now.getDate() && schMonth.value === now.getMonth() && schYear.value === now.getFullYear() })
  }
  while (days.length < 42) days.push({ d: days.length - last.getDate() - startDay + 1, cur: false })
  return days
})

function prevMonth() {
  if (schMonth.value === 0) { schMonth.value = 11; schYear.value-- } else schMonth.value--
}
function nextMonth() {
  if (schMonth.value === 11) { schMonth.value = 0; schYear.value++ } else schMonth.value++
}
function goToday() {
  schMonth.value = new Date().getMonth()
  schYear.value = new Date().getFullYear()
}
</script>

<template>
  <div class="sch-wrap">
    <div class="sch-main">
      <!-- Top legend -->
      <div class="sch-top">
        <div class="sch-legend">
          <span class="lg-sell">带货类</span>
          <span class="lg-edu">科普类</span>
          <span class="lg-story">剧情类</span>
          <span class="lg-daily">日常/预热</span>
        </div>
      </div>

      <!-- Calendar -->
      <div class="sch-cal">
        <table>
          <thead>
            <tr>
              <th>每周目标</th>
              <th v-for="d in ['周一','周二','周三','周四','周五','周六','周日']" :key="d">{{ d }}</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(_, wi) in Array(6)" :key="wi">
              <tr v-if="wi === 0 || calDays.slice(wi*7, wi*7+7).some(d => d.cur)">
                <td>
                  <div class="sch-wk-n">WEEK {{ String(wi + 1).padStart(2, '0') }}</div>
                  <div class="sch-wk-d">点击设置周目标</div>
                </td>
                <td v-for="(d, di) in calDays.slice(wi*7, wi*7+7)" :key="di"
                  :class="{ dim: !d.cur, today: d.today }"
                  @click="schModal = true">
                  <div class="day-n">
                    {{ d.d }}
                    <span v-if="d.today" class="sch-today-badge">今天</span>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- Nav -->
      <div class="sch-nav">
        <button class="sch-nav-btn" @click="prevMonth">&lt; 上一个月</button>
        <span style="font-size:14px;font-weight:700;">{{ schYear }}年 {{ monthNames[schMonth] }}</span>
        <button class="sch-nav-btn today" @click="goToday">今天</button>
        <button class="sch-nav-btn" @click="nextMonth">下一个月 &gt;</button>
        <div class="sch-pub">
          <button class="sch-pub-btn pri" @click="schModal = true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            一键发布
          </button>
          <button class="sch-pub-btn sec" @click="schModal = true">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            定时发布
          </button>
        </div>
      </div>
    </div>

    <!-- Right sidebar -->
    <div class="sch-side">
      <div class="sch-side-t">本月执行看板</div>
      <div class="sch-board">
        <div class="sch-board-row">
          <div>
            <div class="sch-board-lbl">已发布内容</div>
            <div class="sch-board-v">0<span style="font-size:12px;color:var(--t3);font-weight:400;">/0 条</span></div>
          </div>
          <div>
            <div class="sch-board-lbl" style="text-align:right;">月达成率</div>
            <div class="sch-board-pct">0%</div>
          </div>
        </div>
        <div class="sch-board-sub">
          <span>待发布 0</span>
          <span style="color:var(--r);">异常数 0</span>
        </div>
      </div>

      <div class="sch-focus">
        <div class="sch-focus-tag">FOCUS OF TODAY / 今日重点</div>
        <div class="sch-focus-t">今日目标: 暂无发布任务</div>
        <div class="sch-focus-d">休息一下，或者开始规划明天的精彩内容吧！</div>
      </div>

      <div class="sch-add">
        <div class="sch-add-t">添加发布计划</div>
        <div class="sch-add-btn" @click="schModal = true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          新建计划
        </div>
        <div class="sch-add-link">查看历史计划</div>
      </div>

      <div>
        <div class="sch-detail-t">
          今日详细计划
          <span class="sch-detail-ct">0个任务</span>
        </div>
        <div style="font-size:11px;color:var(--t3);text-align:center;padding:20px;">暂无计划</div>
      </div>
    </div>
  </div>

  <!-- Modal -->
  <div v-if="schModal" class="sch-ov" @click="schModal = false">
    <div class="sch-mdl" @click.stop>
      <div class="sch-mdl-main">
        <div class="sch-mdl-hd">
          <div class="sch-mdl-t">新建发布计划</div>
          <button style="width:34px;height:34px;border-radius:10px;border:none;background:none;cursor:pointer;color:var(--t3);display:flex;align-items:center;justify-content:center;" @click="schModal = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div class="sch-mdl-tabs">
          <button v-for="(t, i) in ['内容库上传','本地上传','标签提醒']" :key="i"
            class="sch-mdl-tab" :class="{ on: schTab === i }" @click="schTab = i">{{ t }}</button>
        </div>
        <div class="sch-mdl-body">
          <div class="tool-fg">
            <div class="tool-fg-l">发布平台</div>
            <div class="sch-plats">
              <div v-for="(p, i) in [{ t:'抖', c:'#000' },{ t:'快', c:'#FF6600' },{ t:'红', c:'#FF2442' },{ t:'微', c:'#D4A017' }]"
                :key="i" class="sch-plat-btn" :class="{ on: i === 0 }" :style="{ color: p.c, fontWeight: 700, fontSize: '12px' }">
                {{ p.t }}
              </div>
            </div>
          </div>
          <div v-if="schTab !== 2" class="sch-content-row">
            <div class="sch-cover">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              封面(选填)
            </div>
            <div class="sch-content-fields">
              <input class="tool-inp" placeholder="输入您视频的标题......" />
              <textarea class="tool-inp" rows="3" placeholder="输入您视频的描述或正文......" style="resize:vertical;" />
            </div>
          </div>
          <div v-else>
            <div class="tool-fg"><input class="tool-inp" placeholder="输入提醒标题......" /></div>
            <div class="tool-fg"><textarea class="tool-inp" rows="3" placeholder="输入提醒详细内容（可选）......" style="resize:vertical;" /></div>
          </div>
          <div class="sch-plan-bar">
            <div class="sch-plan-bar-t">计划与分类</div>
            <div class="sch-plan-bar-row">
              <span style="display:flex;align-items:center;gap:4px;">📅 {{ new Date().toLocaleDateString('zh-CN') }}</span>
              <span>—</span>
              <span style="display:flex;align-items:center;gap:4px;">🕒 18:00</span>
              <div class="sch-colors">
                <div style="font-size:10px;color:var(--t3);margin-right:4px;align-self:center;">选择颜色</div>
                <div v-for="(c, i) in ['#3B82F6','#10B981','#7C3AED','#F97316','#F43F5E']" :key="i"
                  class="sch-color" :class="{ on: schColor === i }" :style="{ background: c }"
                  @click="schColor = i" />
              </div>
            </div>
          </div>
        </div>
        <div class="sch-mdl-foot">
          <button class="sch-f-btn sch-f-cancel" @click="schModal = false">取消</button>
          <button class="sch-f-btn sch-f-confirm">{{ schTab === 2 ? '确认提醒' : '确认发布' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
