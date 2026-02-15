<template>
  <el-container class="main-layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <h1>E2E Test Generator</h1>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="side-menu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <span>项目管理</span>
        </el-menu-item>
        <el-menu-item index="/documents">
          <el-icon><Document /></el-icon>
          <span>文档管理</span>
        </el-menu-item>
        <el-menu-item index="/function-points">
          <el-icon><List /></el-icon>
          <span>功能点管理</span>
        </el-menu-item>
        <el-menu-item index="/test-cases">
          <el-icon><Tickets /></el-icon>
          <span>测试用例</span>
        </el-menu-item>
        <el-menu-item index="/test-scripts">
          <el-icon><DocumentCopy /></el-icon>
          <span>测试脚本</span>
        </el-menu-item>
        <el-menu-item index="/mind-map">
          <el-icon><Share /></el-icon>
          <span>思维导图</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="$router.push('/test-cases/generate')">
            <el-icon><Plus /></el-icon>
            生成测试用例
          </el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  DataAnalysis,
  Folder,
  Document,
  List,
  Tickets,
  DocumentCopy,
  Share,
  Plus
} from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta.title as string || '')
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
}

.aside {
  background-color: #304156;
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #263445;
    
    h1 {
      color: #fff;
      font-size: 16px;
      margin: 0;
      white-space: nowrap;
    }
  }
  
  .side-menu {
    border-right: none;
  }
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  
  .header-left {
    display: flex;
    align-items: center;
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
}

.main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
