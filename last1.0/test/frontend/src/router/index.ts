import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/dashboard/index.vue'),
    },
    {
      path: '/script-creator',
      name: 'ScriptCreator',
      component: () => import('../views/script-creator/index.vue'),
    },
    {
      path: '/ip-studio',
      name: 'IPStudio',
      component: () => import('../views/ip-studio/index.vue'),
    },
    {
      path: '/templates',
      name: 'Templates',
      component: () => import('../views/templates/index.vue'),
    },
    {
      path: '/project-list',
      name: 'ProjectList',
      component: () => import('../views/project-list/index.vue'),
    },
    {
      path: '/comic-drama',
      name: 'ComicDrama',
      component: () => import('../views/comic-drama/index.vue'),
    },
    // New pages matching JSX design
    {
      path: '/avatar',
      name: 'Avatar',
      component: () => import('../views/avatar/index.vue'),
    },
    {
      path: '/imgtext',
      name: 'ImgText',
      component: () => import('../views/imgtext/index.vue'),
    },
    {
      path: '/schedule',
      name: 'Schedule',
      component: () => import('../views/schedule/index.vue'),
    },
    {
      path: '/adkol',
      name: 'AdKol',
      component: () => import('../views/adkol/index.vue'),
    },
    {
      path: '/analytics',
      name: 'Analytics',
      component: () => import('../views/analytics/index.vue'),
    },
    {
      path: '/history',
      name: 'History',
      component: () => import('../views/history/index.vue'),
    },
    {
      path: '/hotbreak',
      name: 'HotBreak',
      component: () => import('../views/hotbreak/index.vue'),
    },
    {
      path: '/pos360',
      name: 'Pos360',
      component: () => import('../views/pos360/index.vue'),
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/settings/index.vue'),
    },
  ],
})

export default router
