<template>
  <div class="projects-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">项目管理</h1>
        <p class="page-subtitle">管理所有测试项目</p>
      </div>
      <el-button type="primary" class="create-btn" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建项目
      </el-button>
    </div>
    
    <div class="content-card">
      <div class="projects-list">
        <div v-for="project in paginatedProjects" :key="project.id" class="project-item">
          <div class="project-icon">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="project-info">
            <div class="project-name">{{ project.name }}</div>
            <div class="project-meta">
              <span class="meta-tag status-tag" :class="project.status">
                {{ project.status === 'active' ? '活跃' : '归档' }}
              </span>
              <span class="meta-date">
                <el-icon><Calendar /></el-icon>
                {{ formatDate(project.created_at) }}
              </span>
            </div>
          </div>
          <div class="project-desc">{{ project.description || '暂无描述' }}</div>
          <div class="project-actions">
            <el-button type="primary" text size="small" @click="viewProject(project)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button type="success" text size="small" @click="goToGenerate(project)">
              <el-icon><MagicStick /></el-icon>
              生成用例
            </el-button>
            <el-button type="warning" text size="small" @click="editProject(project)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" text size="small" @click="deleteProject(project)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
        
        <div v-if="!loading && projects.length === 0" class="empty-state">
          <el-icon><FolderAdd /></el-icon>
          <p>暂无项目</p>
          <el-button type="primary" @click="showCreateDialog">创建第一个项目</el-button>
        </div>
      </div>
      
      <div class="pagination-wrapper" v-if="projects.length > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="projects.length"
          layout="total, prev, pager, next"
          background
        />
      </div>
    </div>
    
    <el-dialog v-model="dialogVisible" :title="editingProject ? '编辑项目' : '新建项目'" width="500px" class="dark-dialog">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入项目描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Folder, FolderAdd, Calendar, View, MagicStick, Edit, Delete } from '@element-plus/icons-vue'
import { projectApi, type Project } from '@/api'
import dayjs from 'dayjs'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const projects = ref<Project[]>([])
const dialogVisible = ref(false)
const editingProject = ref<Project | null>(null)
const formRef = ref<FormInstance>()
const currentPage = ref(1)
const pageSize = 10

const formData = reactive({
  name: '',
  description: ''
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD')

const paginatedProjects = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return projects.value.slice(start, end)
})

const loadProjects = async () => {
  loading.value = true
  try {
    const data = await projectApi.list({ limit: 100 })
    projects.value = data
  } catch (error) {
    console.error('Failed to load projects:', error)
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  editingProject.value = null
  formData.name = ''
  formData.description = ''
  dialogVisible.value = true
}

const editProject = (project: Project) => {
  editingProject.value = project
  formData.name = project.name
  formData.description = project.description || ''
  dialogVisible.value = true
}

const viewProject = (project: Project) => {
  router.push(`/documents?project_id=${project.id}`)
}

const goToGenerate = (project: Project) => {
  router.push(`/testcase/generate?project_id=${project.id}&reset=true`)
}

const deleteProject = async (project: Project) => {
  try {
    const stats = await projectApi.stats(project.id)
    
    const relatedInfo = []
    if (stats.document_count > 0) relatedInfo.push(`${stats.document_count} 个文档`)
    if (stats.function_point_count > 0) relatedInfo.push(`${stats.function_point_count} 个功能点`)
    if (stats.test_case_count > 0) relatedInfo.push(`${stats.test_case_count} 个测试用例`)
    
    let confirmMessage = '确定要删除该项目吗？'
    if (relatedInfo.length > 0) {
      confirmMessage = `该项目下有 ${relatedInfo.join('、')}，删除后将无法恢复，确定要删除吗？`
    }
    
    await ElMessageBox.confirm(confirmMessage, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    
    await projectApi.delete(project.id)
    ElMessage.success('项目删除成功')
    loadProjects()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete project:', error)
    }
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (editingProject.value) {
        await projectApi.update(editingProject.value.id, formData)
        ElMessage.success('更新成功')
      } else {
        await projectApi.create(formData)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadProjects()
    } catch (error) {
      console.error('Failed to submit:', error)
    } finally {
      submitting.value = false
    }
  })
}

onMounted(() => {
  loadProjects()
})
</script>

<style lang="scss" scoped>
.projects-page {
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
    
    .create-btn {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border: none;
      
      &:hover {
        opacity: 0.9;
      }
    }
  }
  
  .content-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 20px;
    
    .projects-list {
      .project-item {
        display: flex;
        align-items: center;
        padding: 16px 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(255, 255, 255, 0.06);
          
          .project-actions {
            opacity: 1;
          }
        }
        
        .project-icon {
          width: 44px;
          height: 44px;
          border-radius: 10px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          flex-shrink: 0;
          
          .el-icon {
            font-size: 22px;
            color: #fff;
          }
        }
        
        .project-info {
          min-width: 200px;
          margin-right: 20px;
          
          .project-name {
            font-size: 15px;
            font-weight: 500;
            margin-bottom: 6px;
          }
          
          .project-meta {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 12px;
            
            .meta-tag {
              padding: 2px 8px;
              border-radius: 4px;
            }
            
            .status-tag {
              &.active {
                background: rgba(103, 194, 58, 0.2);
                color: #67c23a;
              }
              
              &.archived {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.5);
              }
            }
            
            .meta-date {
              display: flex;
              align-items: center;
              gap: 4px;
              color: rgba(255, 255, 255, 0.5);
            }
          }
        }
        
        .project-desc {
          flex: 1;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.5);
          line-height: 1.5;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          margin-right: 20px;
        }
        
        .project-actions {
          display: flex;
          gap: 4px;
          opacity: 0.6;
          transition: opacity 0.3s ease;
          flex-shrink: 0;
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
          margin-bottom: 20px;
        }
      }
    }
    
    .pagination-wrapper {
      display: flex;
      justify-content: center;
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      
      :deep(.el-pagination) {
        .el-pagination__total {
          color: rgba(255, 255, 255, 0.6);
        }
        
        .btn-prev, .btn-next, .el-pager li {
          background: rgba(255, 255, 255, 0.05);
          color: rgba(255, 255, 255, 0.8);
          
          &:hover {
            background: rgba(255, 255, 255, 0.1);
          }
          
          &.is-active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
          }
          
          &.is-disabled {
            color: rgba(255, 255, 255, 0.3);
          }
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
    
    .el-form-item__label {
      color: rgba(255, 255, 255, 0.8);
    }
    
    .el-input__wrapper {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: none;
      
      &:hover, &:focus {
        border-color: rgba(102, 126, 234, 0.5);
      }
      
      input {
        color: #fff;
        
        &::placeholder {
          color: rgba(255, 255, 255, 0.3);
        }
      }
    }
    
    .el-textarea__inner {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: none;
      color: #fff;
      
      &:hover, &:focus {
        border-color: rgba(102, 126, 234, 0.5);
      }
      
      &::placeholder {
        color: rgba(255, 255, 255, 0.3);
      }
    }
  }
}
</style>
