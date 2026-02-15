import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/Projects.vue'),
        meta: { title: '项目管理' }
      },
      {
        path: 'documents',
        name: 'Documents',
        component: () => import('@/views/Documents.vue'),
        meta: { title: '文档管理' }
      },
      {
        path: 'function-points',
        name: 'FunctionPoints',
        component: () => import('@/views/FunctionPoints.vue'),
        meta: { title: '功能点管理' }
      },
      {
        path: 'test-cases',
        name: 'TestCases',
        component: () => import('@/views/testcase/Manage.vue'),
        meta: { title: '测试用例' }
      },
      {
        path: 'test-cases/generate',
        name: 'TestCaseGenerate',
        component: () => import('@/views/testcase/Generate.vue'),
        meta: { title: '生成测试用例' }
      },
      {
        path: 'test-scripts',
        name: 'TestScripts',
        component: () => import('@/views/script/Manage.vue'),
        meta: { title: '测试脚本' }
      },
      {
        path: 'mind-map',
        name: 'MindMap',
        component: () => import('@/views/MindMap.vue'),
        meta: { title: '思维导图' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || 'E2E Test Generator'} - E2E Test Generator`
  next()
})

export default router
