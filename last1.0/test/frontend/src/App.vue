<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './components/AppSidebar.vue'

const route = useRoute()

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    '/dashboard':      '工作台',
    '/script-creator': 'AI 创作',
    '/ip-studio':      'IP工作室',
    '/templates':      '模板库',
    '/project-list':   '项目列表',
    '/comic-drama':    '漫剧生成',
    '/avatar':         '数字人生成',
    '/imgtext':        '图文AI制作',
    '/schedule':       '排期发布',
    '/adkol':          '投流达人',
    '/analytics':      '数据复盘',
    '/history':        '内容库',
    '/hotbreak':       '爆款深度解析',
    '/pos360':         '360° 行业定位分析',
    '/settings':       '设置',
  }
  return map[route.path] ?? 'Wing AI'
})
</script>

<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <AppSidebar />

    <!-- Main area -->
    <div class="mn">
      <!-- Topbar (JSX .tb style) -->
      <div class="tb">
        <div class="tb-t">{{ pageTitle }}</div>
        <div class="tb-r">
          <div class="sr">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input placeholder="搜索..." />
          </div>
          <button class="bt bt-p" @click="$router.push('/script-creator')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            新建脚本
          </button>
        </div>
      </div>

      <!-- Page content -->
      <div class="app-scroll">
        <router-view />
      </div>
    </div>
  </div>
</template>
