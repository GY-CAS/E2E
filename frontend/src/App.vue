<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
}

body {
  margin: 0;
  padding: 0;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
}

/* 全局覆盖 Element Plus textarea 样式 */
.el-textarea__inner {
  min-height: 60px !important;
  height: auto !important;
  padding: 8px 12px !important;
  resize: none !important;
}
</style>
