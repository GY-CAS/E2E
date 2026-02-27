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
          <el-button type="text" class="theme-toggle" @click="toggleTheme">
            <el-icon v-if="isDarkMode"><Sunny /></el-icon>
            <el-icon v-else><Moon /></el-icon>
          </el-button>
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
import { computed, ref, onMounted } from 'vue'
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
  MagicStick,
  Sunny,
  Moon
} from '@element-plus/icons-vue'

const route = useRoute()
const isDarkMode = ref(true)

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta.title as string || '')

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  document.documentElement.classList.toggle('light-theme', !isDarkMode.value)
  document.documentElement.classList.toggle('dark-theme', isDarkMode.value)
  localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light')
}

const updateThemeFromStorage = (theme: string) => {
  if (theme === 'light') {
    isDarkMode.value = false
    document.documentElement.classList.add('light-theme')
    document.documentElement.classList.remove('dark-theme')
  } else {
    isDarkMode.value = true
    document.documentElement.classList.add('dark-theme')
    document.documentElement.classList.remove('light-theme')
  }
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'light') {
    isDarkMode.value = false
    document.documentElement.classList.add('light-theme')
  } else {
    isDarkMode.value = true
    document.documentElement.classList.add('dark-theme')
  }

  // 监听storage事件，实现跨标签页通信
  window.addEventListener('storage', (event) => {
    if (event.key === 'theme' && event.newValue) {
      updateThemeFromStorage(event.newValue)
    }
  })
})
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
}

.aside {
  background: linear-gradient(180deg, var(--background-color) 0%, var(--surface-color) 50%, var(--border-light) 100%);
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: var(--surface-color);
    border-bottom: 1px solid var(--border-color);
    
    .logo-icon {
      font-size: 24px;
      color: var(--primary-color);
    }
    
    h1 {
      color: var(--text-primary);
      font-size: 16px;
      font-weight: 600;
      margin: 0;
      white-space: nowrap;
      background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
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
      color: var(--text-secondary);
      
      &:hover {
        background: var(--border-light);
        color: var(--text-primary);
      }
      
      &.is-active {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
        
        .el-icon {
          color: #fff;
        }
        
        span {
          color: #fff;
        }
      }
      
      .el-icon {
        color: var(--text-secondary);
      }
    }
  }
}

.header {
  background: var(--surface-color);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
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
        color: var(--text-tertiary);
      }
      
      .el-breadcrumb__inner a,
      .el-breadcrumb__inner.is-link {
        color: var(--text-secondary);
        
        &:hover {
          color: var(--primary-color);
        }
      }
    }
  }
  
  .header-right {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .theme-toggle {
        color: var(--text-secondary);
        font-size: 18px;
        
        &:hover {
          color: var(--text-primary);
          background: var(--border-light);
        }
      }
      
      .generate-btn {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
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
