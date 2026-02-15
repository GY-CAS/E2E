<template>
  <div class="documents-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>文档列表</span>
            <el-select v-model="selectedProject" placeholder="选择项目" style="margin-left: 16px; width: 200px;" clearable @change="loadDocuments">
              <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </div>
          <el-upload
            :show-file-list="false"
            :before-upload="handleUpload"
            :disabled="!selectedProject"
          >
            <el-button type="primary" :disabled="!selectedProject">
              <el-icon><Upload /></el-icon>
              上传文档
            </el-button>
          </el-upload>
        </div>
      </template>
      
      <el-table :data="documents" v-loading="loading" stripe>
        <el-table-column prop="name" label="文档名称" min-width="200" />
        <el-table-column prop="doc_type" label="文档类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ getDocTypeLabel(row.doc_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="文件大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="parseDocument(row)" :disabled="row.status !== 'pending'">解析</el-button>
            <el-button type="danger" link @click="deleteDocument(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { documentApi, projectApi, type Document, type Project } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const loading = ref(false)
const documents = ref<Document[]>([])
const projects = ref<Project[]>([])
const selectedProject = ref<string>('')

const docTypeLabels: Record<string, string> = {
  requirement: '需求文档',
  spec: '规格说明书',
  design: '设计文档',
  api: '接口说明',
  manual: '用户手册',
  image: '图片'
}

const statusLabels: Record<string, string> = {
  pending: '待解析',
  processing: '解析中',
  parsed: '已解析',
  failed: '解析失败'
}

const statusTypes: Record<string, string> = {
  pending: 'info',
  processing: 'warning',
  parsed: 'success',
  failed: 'danger'
}

const getDocTypeLabel = (type: string) => docTypeLabels[type] || type
const getStatusLabel = (status: string) => statusLabels[status] || status
const getStatusType = (status: string) => statusTypes[status] || 'info'
const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss')
const formatFileSize = (size: number) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  return `${(size / 1024 / 1024).toFixed(2)} MB`
}

const loadProjects = async () => {
  try {
    projects.value = await projectApi.list()
    const projectId = route.query.project_id as string
    if (projectId) {
      selectedProject.value = projectId
    }
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

const loadDocuments = async () => {
  if (!selectedProject.value) {
    documents.value = []
    return
  }
  
  loading.value = true
  try {
    documents.value = await documentApi.list({ project_id: selectedProject.value })
  } catch (error) {
    console.error('Failed to load documents:', error)
  } finally {
    loading.value = false
  }
}

const handleUpload = async (file: File) => {
  if (!selectedProject.value) {
    ElMessage.warning('请先选择项目')
    return false
  }
  
  try {
    await documentApi.upload(selectedProject.value, file)
    ElMessage.success('上传成功')
    loadDocuments()
  } catch (error) {
    console.error('Failed to upload:', error)
  }
  return false
}

const parseDocument = async (doc: Document) => {
  try {
    await documentApi.parse(doc.id)
    ElMessage.success('开始解析文档')
    loadDocuments()
  } catch (error) {
    console.error('Failed to parse:', error)
  }
}

const deleteDocument = async (doc: Document) => {
  try {
    await ElMessageBox.confirm('确定要删除该文档吗？', '提示', { type: 'warning' })
    await documentApi.delete(doc.id)
    ElMessage.success('删除成功')
    loadDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete:', error)
    }
  }
}

onMounted(async () => {
  await loadProjects()
  await loadDocuments()
})
</script>

<style lang="scss" scoped>
.documents-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-left {
      display: flex;
      align-items: center;
    }
  }
}
</style>
