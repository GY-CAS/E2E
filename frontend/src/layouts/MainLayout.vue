<template>
  <el-container class="main-layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon class="logo-icon"><MagicStick /></el-icon>
        <h1>E2E Test</h1>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="side-menu"
        router
        background-color="transparent"
        text-color="rgba(255, 255, 255, 0.7)"
        active-text-color="#fff"
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
          <el-button type="primary" class="generate-btn" @click="$router.push('/test-cases/generate')">
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
  Plus,
  MagicStick
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
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    .logo-icon {
      font-size: 24px;
      color: #667eea;
    }
    
    h1 {
      color: #fff;
      font-size: 16px;
      font-weight: 600;
      margin: 0;
      white-space: nowrap;
      background: linear-gradient(90deg, #667eea, #764ba2);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }
  
  .side-menu {
    border-right: none;
    
    :deep(.el-menu-item) {
      margin: 4px 8px;
      border-radius: 8px;
      transition: all 0.3s ease;
      
      &:hover {
        background: rgba(255, 255, 255, 0.05);
      }
      
      &.is-active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        
        .el-icon {
          color: #fff;
        }
      }
      
      .el-icon {
        color: rgba(255, 255, 255, 0.7);
      }
    }
  }
}

.header {
  background: rgba(26, 26, 46, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  
  .header-left {
    display: flex;
    align-items: center;
    
    :deep(.el-breadcrumb) {
      .el-breadcrumb__inner,
      .el-breadcrumb__separator {
        color: rgba(255, 255, 255, 0.6);
      }
      
      .el-breadcrumb__inner a,
      .el-breadcrumb__inner.is-link {
        color: rgba(255, 255, 255, 0.8);
        
        &:hover {
          color: #667eea;
        }
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .generate-btn {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border: none;
      
      &:hover {
        opacity: 0.9;
        transform: translateY(-1px);
      }
    }
  }
}

.main {
  background: transparent;
  padding: 0;
}
</style>
