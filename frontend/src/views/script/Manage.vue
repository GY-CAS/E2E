<template>
  <div class="scripts-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>测试脚本列表</span>
            <el-select v-model="selectedProject" placeholder="选择项目" style="margin-left: 16px; width: 200px;" clearable @change="loadScripts">
              <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </div>
        </div>
      </template>
      
      <el-table :data="scripts" v-loading="loading" stripe>
        <el-table-column prop="name" label="脚本名称" min-width="200" />
        <el-table-column prop="language" label="语言" width="100">
          <template #default="{ row }">
            <el-tag :type="row.language === 'python' ? 'success' : 'warning'">
              {{ row.language === 'python' ? 'Python' : 'Java' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="framework" label="框架" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewScript(row)">查看</el-button>
            <el-button type="primary" link @click="downloadScript(row)">下载</el-button>
            <el-button type="danger" link @click="deleteScript(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="editorVisible" title="脚本详情" width="900px" top="5vh">
      <div class="script-info" v-if="currentScript">
        <el-descriptions :column="3" border size="small" style="margin-bottom: 16px;">
          <el-descriptions-item label="脚本名称">{{ currentScript.name }}</el-descriptions-item>
          <el-descriptions-item label="语言">{{ currentScript.language }}</el-descriptions-item>
          <el-descriptions-item label="框架">{{ currentScript.framework }}</el-descriptions-item>
        </el-descriptions>
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

const statusTypes: Record<string, string> = {
  draft: 'info',
  reviewed: 'warning',
  approved: 'success'
}

const getStatusLabel = (status: string) => statusLabels[status] || status
const getStatusType = (status: string) => statusTypes[status] || 'info'
const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss')

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
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-left {
      display: flex;
      align-items: center;
    }
  }
  
  .script-info {
    .code-editor {
      background-color: #1e1e1e;
      border-radius: 8px;
      padding: 16px;
      max-height: 500px;
      overflow: auto;
      
      pre {
        margin: 0;
        
        code {
          color: #d4d4d4;
          font-family: 'Consolas', 'Monaco', monospace;
          font-size: 13px;
          line-height: 1.5;
        }
      }
    }
  }
}
</style>
