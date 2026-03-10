<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const currentPath = computed(() => route.path)

const historyCount = ref(28)

function isActive(path: string) {
  return currentPath.value === path || currentPath.value.startsWith(path + '/')
}

function go(path: string) {
  router.push(path)
}
</script>

<template>
  <aside class="sb">
    <!-- Logo -->
    <div class="sb-logo">
      <div class="sb-lic">W</div>
      <span class="sb-ltx">Wing AI</span>
      <span class="sb-lv">Beta</span>
    </div>

    <!-- Nav -->
    <nav style="flex:1;padding-bottom:8px;overflow-y:auto;overflow-x:hidden;">
      <!-- 工作台 -->
      <div class="sb-g">
        <div
          class="sb-i"
          :class="{ on: isActive('/dashboard') || currentPath === '/' }"
          @click="go('/dashboard')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          工作台
        </div>
      </div>

      <!-- AI 创作 -->
      <div class="sb-g">
        <div class="sb-gt">AI 创作</div>
        <!-- AI创作 parent -->
        <div
          class="sb-i accent"
          :class="{ on: isActive('/script-creator') }"
          @click="go('/script-creator')"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z"/></svg>
          AI创作
          <span class="sb-tag" style="background:var(--pbg);color:var(--p);">HOT</span>
        </div>
        <!-- Sub items -->
        <div class="sb-sub">
          <div class="sb-si" :class="{ on: isActive('/ip-studio') }" @click="go('/ip-studio')">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            数字人生成
          </div>
          <div class="sb-si" :class="{ on: isActive('/imgtext') }" @click="go('/imgtext')">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
            图文AI制作
          </div>
        </div>
      </div>

      <!-- 运营管理 -->
      <div class="sb-g">
        <div class="sb-gt">运营管理</div>
        <div class="sb-i" :class="{ on: isActive('/schedule') }" @click="go('/schedule')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          排期发布
        </div>
        <div class="sb-i" :class="{ on: isActive('/adkol') }" @click="go('/adkol')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
          投流达人
        </div>
        <div class="sb-i" :class="{ on: isActive('/analytics') }" @click="go('/analytics')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          数据复盘
        </div>
      </div>

      <!-- 其他 -->
      <div class="sb-g">
        <div class="sb-i" :class="{ on: isActive('/history') }" @click="go('/history')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>
          创作历史
          <span class="sb-tag" style="background:var(--pbg);color:var(--p);">{{ historyCount }}</span>
        </div>
        <div class="sb-i" :class="{ on: isActive('/templates') }" @click="go('/templates')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
          模板库
        </div>
        <div class="sb-i" :class="{ on: isActive('/project-list') }" @click="go('/project-list')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          项目列表
        </div>
        <div class="sb-i" :class="{ on: isActive('/settings') }" @click="go('/settings')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68V3a2 2 0 1 1 4 0v.09c.08.55.44 1.03 1 1.24a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.2.56.69.92 1.24 1H21a2 2 0 1 1 0 4h-.09c-.55.08-1.03.44-1.24 1z"/></svg>
          设置
        </div>
      </div>
    </nav>

    <!-- Bottom - IP Profile card -->
    <div class="sb-bt">
      <div class="ipc" @click="go('/ip-studio')">
        <div class="ipc-h">
          <div class="ipc-a">IP</div>
          <div>
            <div class="ipc-n">我的IP人设</div>
            <div class="ipc-s">● 已配置</div>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
/* Sidebar structural styles (layout only, design tokens come from global.scss) */
.sb {
  width: 240px;
  min-width: 240px;
  background: var(--s);
  border-right: 1px solid var(--bl);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
  height: 100vh;
}
.sb::-webkit-scrollbar { width: 3px; }
.sb::-webkit-scrollbar-thumb { background: var(--b); border-radius: 2px; }

.sb-logo {
  padding: 18px 16px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--bl);
  flex-shrink: 0;
}
.sb-lic {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, var(--p), var(--pl));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 800; font-size: 11px; letter-spacing: -0.5px;
}
.sb-ltx { font-weight: 800; font-size: 17px; letter-spacing: -.5px; }
.sb-lv {
  font-size: 9px; color: var(--p); background: var(--pbg);
  padding: 2px 6px; border-radius: 4px; font-weight: 700; margin-left: auto;
}
.sb-g { padding: 14px 10px 4px; }
.sb-gt {
  font-size: 9px; font-weight: 700; color: var(--t3);
  text-transform: uppercase; letter-spacing: .8px;
  padding: 0 8px 6px;
}
.sb-i {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 10px;
  cursor: pointer; transition: .2s ease;
  font-size: 13px; font-weight: 500; color: var(--t2);
  position: relative; margin-bottom: 1px;
  user-select: none;
}
.sb-i:hover { background: var(--s3); color: var(--t1); }
.sb-i.on {
  background: var(--pbg); color: var(--p); font-weight: 600;
}
.sb-i.on::before {
  content: '';
  position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  width: 3px; height: 18px;
  background: var(--p); border-radius: 0 3px 3px 0;
}
.sb-i.accent { color: var(--p); }
.sb-tag {
  font-size: 9px; font-weight: 700; margin-left: auto;
  padding: 1px 6px; border-radius: 8px;
}
.sb-sub { padding-left: 26px; margin-bottom: 2px; }
.sb-si {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 10px; border-radius: 6px;
  cursor: pointer; font-size: 12px; color: var(--t3);
  transition: .2s ease; margin-bottom: 1px;
}
.sb-si::before {
  content: ''; width: 4px; height: 4px; border-radius: 50%;
  background: currentColor; opacity: .4; flex-shrink: 0;
}
.sb-si:hover { color: var(--t1); background: var(--s3); }
.sb-si.on {
  color: var(--p); font-weight: 600; background: var(--pbg);
}
.sb-si.on::before { opacity: 1; background: var(--p); }
.sb-bt { margin-top: auto; padding: 10px; border-top: 1px solid var(--bl); }
.ipc {
  background: linear-gradient(135deg, #F5F0FF, #EDE9FE);
  border-radius: 14px; padding: 11px; cursor: pointer;
  transition: .2s ease; border: 1px solid transparent;
}
.ipc:hover { border-color: var(--pl); }
.ipc-h { display: flex; align-items: center; gap: 7px; }
.ipc-a {
  width: 24px; height: 24px; border-radius: 50%;
  background: linear-gradient(135deg, var(--p), #A78BFA);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 9px; font-weight: 800;
}
.ipc-n { font-size: 11px; font-weight: 600; }
.ipc-s { font-size: 9px; color: var(--g); }
</style>
