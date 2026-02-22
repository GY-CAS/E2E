<template>
  <div class="documents-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">文档管理</h1>
        <p class="page-subtitle">上传和管理项目文档</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedProject" placeholder="选择项目" class="project-select" clearable @change="loadDocuments">
          <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-upload
          :show-file-list="false"
          :before-upload="handleUpload"
          :disabled="!selectedProject"
        >
          <el-button type="primary" class="upload-btn" :disabled="!selectedProject">
            <el-icon><Upload /></el-icon>
            上传文档
          </el-button>
        </el-upload>
      </div>
    </div>
    
    <div class="content-card">
      <div class="documents-list">
        <div v-for="doc in documents" :key="doc.id" class="document-item">
          <div class="doc-icon">
            <el-icon><DocumentIcon /></el-icon>
          </div>
          <div class="doc-info">
            <div class="doc-name">{{ doc.name }}</div>
            <div class="doc-meta">
              <span class="meta-tag">{{ getDocTypeLabel(doc.doc_type) }}</span>
              <span class="meta-size">{{ formatFileSize(doc.file_size) }}</span>
              <span class="meta-date">{{ formatDate(doc.created_at) }}</span>
            </div>
          </div>
          <div class="doc-status" :class="doc.status">
            {{ getStatusLabel(doc.status) }}
          </div>
          <div class="doc-actions">
            <el-button type="primary" text size="small" @click="parseDocument(doc)" :disabled="doc.status !== 'pending'">
              <el-icon><Refresh /></el-icon>
              解析
            </el-button>
            <el-button type="danger" text size="small" @click="deleteDocument(doc)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
        
        <div v-if="!loading && documents.length === 0" class="empty-state">
          <el-icon><DocumentAdd /></el-icon>
          <p>{{ selectedProject ? '暂无文档' : '请先选择项目' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Document as DocumentIcon, DocumentAdd, Refresh, Delete } from '@element-plus/icons-vue'
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

const getDocTypeLabel = (type: string) => docTypeLabels[type] || type || '文档'
const getStatusLabel = (status: string) => statusLabels[status] || status
const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm')
const formatFileSize = (size: number) => {
  if (!size) return '-'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
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
      
      .upload-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        
        &:hover:not(:disabled) {
          opacity: 0.9;
        }
        
        &:disabled {
          opacity: 0.5;
        }
      }
    }
  }
  
  .content-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 20px;
    
    .documents-list {
      .document-item {
        display: flex;
        align-items: center;
        padding: 16px 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(255, 255, 255, 0.06);
          
          .doc-actions {
            opacity: 1;
          }
        }
        
        .doc-icon {
          width: 44px;
          height: 44px;
          border-radius: 10px;
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          
          .el-icon {
            font-size: 22px;
            color: #fff;
          }
        }
        
        .doc-info {
          flex: 1;
          
          .doc-name {
            font-size: 15px;
            font-weight: 500;
            margin-bottom: 6px;
          }
          
          .doc-meta {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
            
            .meta-tag {
              padding: 2px 8px;
              background: rgba(102, 126, 234, 0.2);
              color: #667eea;
              border-radius: 4px;
            }
          }
        }
        
        .doc-status {
          font-size: 12px;
          padding: 4px 12px;
          border-radius: 4px;
          margin-right: 16px;
          
          &.pending {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.6);
          }
          
          &.processing {
            background: rgba(230, 162, 60, 0.2);
            color: #e6a23c;
          }
          
          &.parsed {
            background: rgba(103, 194, 58, 0.2);
            color: #67c23a;
          }
          
          &.failed {
            background: rgba(245, 108, 108, 0.2);
            color: #f56c6c;
          }
        }
        
        .doc-actions {
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
}
</style>
