<template>
  <div class="scripts-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">测试脚本管理</h1>
        <p class="page-subtitle">管理自动化测试脚本</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedProject" placeholder="选择项目" class="project-select" clearable @change="loadScripts">
          <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
      </div>
    </div>
    
    <div class="content-card">
      <div class="scripts-list">
        <div v-for="script in scripts" :key="script.id" class="script-item">
          <div class="script-icon">
            <el-icon><DocumentCopy /></el-icon>
          </div>
          <div class="script-info">
            <div class="script-name">{{ script.name }}</div>
            <div class="script-meta">
              <span class="meta-tag lang-tag" :class="script.language">
                {{ script.language === 'python' ? 'Python' : 'Java' }}
              </span>
              <span class="meta-tag framework-tag">{{ script.framework }}</span>
              <span class="meta-date">{{ formatDate(script.created_at) }}</span>
            </div>
          </div>
          <div class="script-status" :class="script.status">
            {{ getStatusLabel(script.status) }}
          </div>
          <div class="script-actions">
            <el-button type="primary" text size="small" @click="viewScript(script)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button type="success" text size="small" @click="downloadScript(script)">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button type="danger" text size="small" @click="deleteScript(script)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
        
        <div v-if="!loading && scripts.length === 0" class="empty-state">
          <el-icon><DocumentCopy /></el-icon>
          <p>{{ selectedProject ? '暂无测试脚本' : '请先选择项目' }}</p>
        </div>
      </div>
    </div>
    
    <el-dialog v-model="editorVisible" title="脚本详情" width="900px" top="5vh" class="dark-dialog">
      <div class="script-info-dialog" v-if="currentScript">
        <div class="info-header">
          <div class="info-item">
            <span class="info-label">脚本名称</span>
            <span class="info-value">{{ currentScript.name }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">语言</span>
            <span class="info-value">{{ currentScript.language }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">框架</span>
            <span class="info-value">{{ currentScript.framework }}</span>
          </div>
        </div>
        <div class="code-editor">
          <pre><code>{{ currentScript.content }}</code></pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentCopy, View, Download, Delete } from '@element-plus/icons-vue'
import { testScriptApi, projectApi, type TestScript, type Project } from '@/api'
import dayjs from 'dayjs'

const loading = ref(false)
const scripts = ref<TestScript[]>([])
const projects = ref<Project[]>([])
const selectedProject = ref<string>('')
const editorVisible = ref(false)
const currentScript = ref<TestScript | null>(null)

const statusLabels: Record<string, string> = {
  draft: '草稿',
  reviewed: '已审核',
  approved: '已通过'
}

const getStatusLabel = (status: string) => statusLabels[status] || status
const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm')

const loadProjects = async () => {
  try {
    projects.value = await projectApi.list()
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

const loadScripts = async () => {
  if (!selectedProject.value) {
    scripts.value = []
    return
  }
  
  loading.value = true
  try {
    scripts.value = await testScriptApi.list({ project_id: selectedProject.value })
  } catch (error) {
    console.error('Failed to load scripts:', error)
  } finally {
    loading.value = false
  }
}

const viewScript = (script: TestScript) => {
  currentScript.value = script
  editorVisible.value = true
}

const downloadScript = async (script: TestScript) => {
  try {
    const blob = await testScriptApi.download(script.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${script.name}.${script.language === 'python' ? 'py' : 'java'}`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download:', error)
  }
}

const deleteScript = async (script: TestScript) => {
  try {
    await ElMessageBox.confirm('确定要删除该脚本吗？', '提示', { type: 'warning' })
    await testScriptApi.delete(script.id)
    ElMessage.success('删除成功')
    loadScripts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete:', error)
    }
  }
}

onMounted(async () => {
  await loadProjects()
})
</script>

<style lang="scss" scoped>
.scripts-page {
  min-height: calc(100vh - 60px);
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 24px;
  color: #fff;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding: 20px 24px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    
    .header-content {
      .page-title {
        font-size: 22px;
        font-weight: 600;
        margin: 0 0 6px 0;
      }
      
      .page-subtitle {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.5);
        margin: 0;
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
      
      .project-select {
        width: 200px;
      }
    }
  }
  
  .content-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 20px;
    
    .scripts-list {
      .script-item {
        display: flex;
        align-items: center;
        padding: 16px 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(255, 255, 255, 0.06);
          
          .script-actions {
            opacity: 1;
          }
        }
        
        .script-icon {
          width: 44px;
          height: 44px;
          border-radius: 10px;
          background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          
          .el-icon {
            font-size: 22px;
            color: #fff;
          }
        }
        
        .script-info {
          flex: 1;
          
          .script-name {
            font-size: 15px;
            font-weight: 500;
            margin-bottom: 6px;
          }
          
          .script-meta {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
            
            .meta-tag {
              padding: 2px 8px;
              border-radius: 4px;
            }
            
            .lang-tag {
              background: rgba(103, 194, 58, 0.2);
              color: #67c23a;
              
              &.java {
                background: rgba(230, 162, 60, 0.2);
                color: #e6a23c;
              }
            }
            
            .framework-tag {
              background: rgba(102, 126, 234, 0.2);
              color: #667eea;
            }
          }
        }
        
        .script-status {
          font-size: 12px;
          padding: 4px 12px;
          border-radius: 4px;
          margin-right: 16px;
          
          &.draft {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.6);
          }
          
          &.reviewed {
            background: rgba(230, 162, 60, 0.2);
            color: #e6a23c;
          }
          
          &.approved {
            background: rgba(103, 194, 58, 0.2);
            color: #67c23a;
          }
        }
        
        .script-actions {
          display: flex;
          gap: 4px;
          opacity: 0.6;
          transition: opacity 0.3s ease;
        }
      }
      
      .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: rgba(255, 255, 255, 0.4);
        
        .el-icon {
          font-size: 64px;
          margin-bottom: 16px;
        }
        
        p {
          font-size: 14px;
        }
      }
    }
  }
  
  .script-info-dialog {
    .info-header {
      display: flex;
      gap: 24px;
      margin-bottom: 16px;
      padding: 16px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      
      .info-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
        
        .info-label {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.5);
        }
        
        .info-value {
          font-size: 14px;
          font-weight: 500;
        }
      }
    }
    
    .code-editor {
      background-color: #0d1117;
      border-radius: 8px;
      padding: 16px;
      max-height: 500px;
      overflow: auto;
      border: 1px solid rgba(255, 255, 255, 0.1);
      
      pre {
        margin: 0;
        
        code {
          color: #c9d1d9;
          font-family: 'Consolas', 'Monaco', monospace;
          font-size: 13px;
          line-height: 1.6;
        }
      }
    }
  }
}

:deep(.dark-dialog) {
  .el-dialog {
    background: #1a1a2e;
    border: 1px solid rgba(255, 255, 255, 0.1);
    
    .el-dialog__header {
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      
      .el-dialog__title {
        color: #fff;
      }
    }
    
    .el-dialog__body {
      color: rgba(255, 255, 255, 0.8);
    }
  }
}
</style>
