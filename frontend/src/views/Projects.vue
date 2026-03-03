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
            <el-button v-if="false" type="success" text size="small" @click="goToGenerate(project)">
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

    <el-dialog v-model="detailDialogVisible" title="项目详情" width="700px" class="dark-dialog detail-dialog">
      <div v-if="detailLoading" class="loading-container">
        <el-skeleton :rows="6" animated />
        <div class="loading-text">加载中...</div>
      </div>
      
      <div v-else-if="detailError" class="error-container">
        <el-result
          icon="error"
          title="加载失败"
          :sub-title="detailError"
        >
          <template #extra>
            <el-button type="primary" @click="loadProjectDetail">重试</el-button>
          </template>
        </el-result>
      </div>
      
      <div v-else-if="projectDetail" class="detail-content">
        <div class="detail-header">
          <div class="detail-icon">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="detail-title">
            <h2>{{ projectDetail.name }}</h2>
            <div class="detail-meta">
              <span class="meta-tag" :class="projectDetail.status">
                {{ projectDetail.status === 'active' ? '活跃' : '归档' }}
              </span>
              <span class="meta-date">
                <el-icon><Calendar /></el-icon>
                创建于 {{ formatDate(projectDetail.created_at) }}
              </span>
            </div>
          </div>
        </div>

        <div class="detail-section" v-if="projectDetail.description">
          <h3 class="section-title">项目描述</h3>
          <div class="description-content" v-html="formatDescription(projectDetail.description)"></div>
        </div>

        <div class="detail-section">
          <h3 class="section-title">资源统计</h3>
          <div class="stats-grid">
            <div class="stat-card documents">
              <div class="stat-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ projectDetail.document_stats.total }}</div>
                <div class="stat-label">文档总数</div>
              </div>
              <div class="stat-breakdown">
                <span class="breakdown-item success">
                  <span class="dot"></span>
                  已解析: {{ projectDetail.document_stats.parsed }}
                </span>
                <span class="breakdown-item warning">
                  <span class="dot"></span>
                  待处理: {{ projectDetail.document_stats.pending }}
                </span>
                <span class="breakdown-item danger" v-if="projectDetail.document_stats.failed > 0">
                  <span class="dot"></span>
                  失败: {{ projectDetail.document_stats.failed }}
                </span>
              </div>
            </div>

            <div class="stat-card function-points">
              <div class="stat-icon">
                <el-icon><Aim /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ projectDetail.function_point_count }}</div>
                <div class="stat-label">功能点数量</div>
              </div>
            </div>

            <div class="stat-card test-cases">
              <div class="stat-icon">
                <el-icon><List /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ projectDetail.test_case_stats.total }}</div>
                <div class="stat-label">测试用例</div>
              </div>
              <div class="stat-breakdown">
                <span class="breakdown-item primary">
                  <span class="dot"></span>
                  手动: {{ projectDetail.test_case_stats.manual }}
                </span>
                <span class="breakdown-item info">
                  <span class="dot"></span>
                  自动化: {{ projectDetail.test_case_stats.auto }}
                </span>
              </div>
              <div class="stat-breakdown" v-if="projectDetail.test_case_stats.frontend > 0 || projectDetail.test_case_stats.backend > 0">
                <span class="breakdown-item">
                  <span class="dot"></span>
                  前端: {{ projectDetail.test_case_stats.frontend }}
                </span>
                <span class="breakdown-item">
                  <span class="dot"></span>
                  后端: {{ projectDetail.test_case_stats.backend }}
                </span>
              </div>
            </div>

            <div class="stat-card test-scripts">
              <div class="stat-icon">
                <el-icon><Tickets /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ projectDetail.test_script_count }}</div>
                <div class="stat-label">测试脚本</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="goToDocuments">
          <el-icon><FolderOpened /></el-icon>
          进入文档管理
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Folder, FolderAdd, Calendar, View, MagicStick, Edit, Delete, Document, Aim, List, Tickets, FolderOpened } from '@element-plus/icons-vue'
import { projectApi, type Project, type ProjectDetail } from '@/api'
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

const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const detailError = ref('')
const projectDetail = ref<ProjectDetail | null>(null)
const currentProjectId = ref('')

const formData = reactive({
  name: '',
  description: ''
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD')

const formatDescription = (description: string | null): string => {
  if (!description) return ''
  return description
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
}

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

const viewProject = async (project: Project) => {
  currentProjectId.value = project.id
  detailDialogVisible.value = true
  await loadProjectDetail()
}

const loadProjectDetail = async () => {
  if (!currentProjectId.value) return
  
  detailLoading.value = true
  detailError.value = ''
  
  try {
    const data = await projectApi.getDetail(currentProjectId.value)
    projectDetail.value = data
  } catch (error: any) {
    console.error('Failed to load project detail:', error)
    detailError.value = error.message || '无法加载项目详情，请稍后重试'
  } finally {
    detailLoading.value = false
  }
}

const goToDocuments = () => {
  if (projectDetail.value) {
    router.push(`/documents?project_id=${projectDetail.value.id}`)
  }
  detailDialogVisible.value = false
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
  background: var(--background-color);
  padding: 24px;
  color: var(--text-primary);
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding: 20px 24px;
    background: var(--surface-color);
    border-radius: 12px;
    border: 1px solid var(--border-color);
    
    .header-content {
      .page-title {
        font-size: 22px;
        font-weight: 600;
        margin: 0 0 6px 0;
        color: var(--text-primary);
      }
      
      .page-subtitle {
        font-size: 13px;
        color: var(--text-tertiary);
        margin: 0;
      }
    }
    
    .create-btn {
      background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
      border: none;
      
      &:hover {
        opacity: 0.9;
      }
    }
  }
  
  .content-card {
    background: var(--surface-color);
    border-radius: 12px;
    border: 1px solid var(--border-color);
    padding: 20px;
    
    .projects-list {
      .project-item {
        display: flex;
        align-items: center;
        padding: 16px 20px;
        background: var(--border-light);
        border-radius: 10px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        
        &:hover {
          background: var(--border-color);
          
          .project-actions {
            opacity: 1;
          }
        }
        
        .project-icon {
          width: 44px;
          height: 44px;
          border-radius: 10px;
          background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
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
            color: var(--text-primary);
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
                color: var(--success-color);
              }
              
              &.archived {
                background: var(--border-light);
                color: var(--text-tertiary);
              }
            }
            
            .meta-date {
              display: flex;
              align-items: center;
              gap: 4px;
              color: var(--text-tertiary);
            }
          }
        }
        
        .project-desc {
          flex: 1;
          font-size: 13px;
          color: var(--text-tertiary);
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
        color: var(--text-tertiary);
        
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
      border-top: 1px solid var(--border-color);
      
      :deep(.el-pagination) {
        .el-pagination__total {
          color: var(--text-secondary);
        }
        
        .btn-prev, .btn-next, .el-pager li {
          background: var(--surface-color);
          color: var(--text-secondary);
          border: 1px solid var(--border-color);
          
          &:hover {
            background: var(--border-light);
          }
          
          &.is-active {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
            color: #fff;
            border-color: var(--primary-color);
          }
          
          &.is-disabled {
            color: var(--text-tertiary);
          }
        }
      }
    }
  }
}

:deep(.el-dialog) {
  .el-dialog__header {
    .el-dialog__title {
      color: var(--text-primary);
    }
  }
  
  .el-dialog__body {
    color: var(--text-primary);
  }
  
  .el-form-item__label {
    color: var(--text-secondary);
  }
  
  .el-input__wrapper {
    background: var(--surface-color);
    border: 1px solid var(--border-color);
    box-shadow: none;
    
    &:hover, &:focus {
      border-color: var(--primary-color);
    }
    
    input {
      color: var(--text-primary);
      
      &::placeholder {
        color: var(--text-tertiary);
      }
    }
  }
  
  .el-textarea__inner {
    background: var(--surface-color);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    
    &::placeholder {
      color: var(--text-tertiary);
    }
  }
}

.detail-dialog {
  .loading-container {
    padding: 40px 0;
    text-align: center;
    
    .loading-text {
      margin-top: 16px;
      color: var(--text-tertiary);
    }
  }
  
  .error-container {
    padding: 40px 0;
  }
  
  .detail-content {
    .detail-header {
      display: flex;
      align-items: center;
      padding: 20px;
      background: var(--border-light);
      border-radius: 12px;
      margin-bottom: 24px;
      
      .detail-icon {
        width: 64px;
        height: 64px;
        border-radius: 16px;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 20px;
        flex-shrink: 0;
        
        .el-icon {
          font-size: 32px;
          color: #fff;
        }
      }
      
      .detail-title {
        flex: 1;
        
        h2 {
          font-size: 20px;
          font-weight: 600;
          margin: 0 0 8px 0;
          color: var(--text-primary);
        }
        
        .detail-meta {
          display: flex;
          align-items: center;
          gap: 16px;
          
          .meta-tag {
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 13px;
            
            &.active {
              background: rgba(103, 194, 58, 0.2);
              color: var(--success-color);
            }
            
            &.archived {
              background: var(--border-light);
              color: var(--text-tertiary);
            }
          }
          
          .meta-date {
            display: flex;
            align-items: center;
            gap: 6px;
            color: var(--text-tertiary);
            font-size: 13px;
          }
        }
      }
    }
    
    .detail-section {
      margin-bottom: 24px;
      
      .section-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 16px 0;
        color: var(--text-primary);
        padding-left: 12px;
        border-left: 3px solid var(--primary-color);
      }
      
      .description-content {
        padding: 16px;
        background: var(--border-light);
        border-radius: 8px;
        font-size: 14px;
        line-height: 1.8;
        color: var(--text-secondary);
        
        :deep(strong) {
          color: var(--text-primary);
          font-weight: 600;
        }
        
        :deep(code) {
          padding: 2px 6px;
          background: var(--background-color);
          border-radius: 4px;
          font-family: monospace;
          font-size: 13px;
        }
      }
    }
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      
      @media (max-width: 640px) {
        grid-template-columns: 1fr;
      }
      
      .stat-card {
        padding: 20px;
        background: var(--border-light);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        
        &:hover {
          border-color: var(--primary-color);
          transform: translateY(-2px);
        }
        
        .stat-icon {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 12px;
          
          .el-icon {
            font-size: 20px;
            color: #fff;
          }
        }
        
        &.documents .stat-icon {
          background: linear-gradient(135deg, #409eff 0%, #3375e6 100%);
        }
        
        &.function-points .stat-icon {
          background: linear-gradient(135deg, #e6a23c 0%, #cf9236 100%);
        }
        
        &.test-cases .stat-icon {
          background: linear-gradient(135deg, #67c23a 0%, #56ab2f 100%);
        }
        
        &.test-scripts .stat-icon {
          background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
        }
        
        .stat-info {
          margin-bottom: 12px;
          
          .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.2;
          }
          
          .stat-label {
            font-size: 13px;
            color: var(--text-tertiary);
            margin-top: 4px;
          }
        }
        
        .stat-breakdown {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          padding-top: 12px;
          border-top: 1px solid var(--border-color);
          
          .breakdown-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--text-secondary);
            
            .dot {
              width: 8px;
              height: 8px;
              border-radius: 50%;
              background: var(--text-tertiary);
            }
            
            &.success .dot { background: #67c23a; }
            &.warning .dot { background: #e6a23c; }
            &.danger .dot { background: #f56c6c; }
            &.primary .dot { background: #409eff; }
            &.info .dot { background: #909399; }
          }
        }
      }
    }
  }
}
</style>
