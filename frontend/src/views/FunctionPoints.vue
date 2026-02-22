<template>
  <div class="function-points-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">功能点管理</h1>
        <p class="page-subtitle">管理项目功能点</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedProject" placeholder="选择项目" class="project-select" clearable @change="loadFunctionPoints">
          <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button type="primary" class="create-btn" @click="showAddDialog" :disabled="!selectedProject">
          <el-icon><Plus /></el-icon>
          新增功能点
        </el-button>
      </div>
    </div>
    
    <div class="content-card">
      <div class="fp-list">
        <div v-for="fp in functionPoints" :key="fp.id" class="fp-item">
          <div class="fp-icon">
            <el-icon><List /></el-icon>
          </div>
          <div class="fp-info">
            <div class="fp-name">{{ fp.name }}</div>
            <div class="fp-meta">
              <span class="meta-tag type-tag">{{ getTestTypeLabel(fp.test_type) }}</span>
              <span class="meta-tag priority-tag" :class="fp.priority">{{ fp.priority?.toUpperCase() }}</span>
              <span class="meta-module" v-if="fp.module">{{ fp.module }}</span>
            </div>
          </div>
          <div class="fp-status" :class="fp.status">
            {{ getStatusLabel(fp.status) }}
          </div>
          <div class="fp-actions">
            <el-button type="primary" text size="small" @click="showEditDialog(fp)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="success" text size="small" @click="approveFP(fp)" :disabled="fp.status !== 'pending'">
              <el-icon><Check /></el-icon>
              通过
            </el-button>
            <el-button type="warning" text size="small" @click="rejectFP(fp)" :disabled="fp.status !== 'pending'">
              <el-icon><Close /></el-icon>
              拒绝
            </el-button>
            <el-button type="danger" text size="small" @click="deleteFP(fp)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
        
        <div v-if="!loading && functionPoints.length === 0" class="empty-state">
          <el-icon><List /></el-icon>
          <p>{{ selectedProject ? '暂无功能点' : '请先选择项目' }}</p>
        </div>
      </div>
    </div>
    
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑功能点' : '新增功能点'" width="600px">
      <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="功能点名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入功能点名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入功能点描述" />
        </el-form-item>
        <el-form-item label="测试类型" prop="test_type">
          <el-select v-model="formData.test_type" placeholder="请选择测试类型" style="width: 100%;">
            <el-option label="功能测试" value="functional" />
            <el-option label="性能测试" value="performance" />
            <el-option label="安全测试" value="security" />
            <el-option label="可靠性测试" value="reliability" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="formData.priority" placeholder="请选择优先级" style="width: 100%;">
            <el-option label="P0 - 最高" value="p0" />
            <el-option label="P1 - 高" value="p1" />
            <el-option label="P2 - 中" value="p2" />
            <el-option label="P3 - 低" value="p3" />
            <el-option label="P4 - 最低" value="p4" />
          </el-select>
        </el-form-item>
        <el-form-item label="模块" prop="module">
          <el-input v-model="formData.module" placeholder="请输入所属模块" />
        </el-form-item>
        <el-form-item label="验收标准" prop="acceptance_criteria">
          <el-input v-model="formData.acceptance_criteria" type="textarea" :rows="3" placeholder="请输入验收标准" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, List, Edit, Check, Close, Delete } from '@element-plus/icons-vue'
import { functionPointApi, projectApi, type FunctionPoint, type Project } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const functionPoints = ref<FunctionPoint[]>([])
const projects = ref<Project[]>([])
const selectedProject = ref<string>('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<string>('')

const formData = reactive({
  name: '',
  description: '',
  test_type: 'functional',
  priority: 'p2',
  module: '',
  acceptance_criteria: ''
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入功能点名称', trigger: 'blur' }],
  test_type: [{ required: true, message: '请选择测试类型', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }]
}

const testTypeLabels: Record<string, string> = {
  functional: '功能测试',
  performance: '性能测试',
  security: '安全测试',
  reliability: '可靠性测试'
}

const statusLabels: Record<string, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝'
}

const getTestTypeLabel = (type: string) => testTypeLabels[type] || type
const getStatusLabel = (status: string) => statusLabels[status] || status

const loadProjects = async () => {
  try {
    projects.value = await projectApi.list()
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

const loadFunctionPoints = async () => {
  if (!selectedProject.value) {
    functionPoints.value = []
    return
  }
  
  loading.value = true
  try {
    functionPoints.value = await functionPointApi.list({ project_id: selectedProject.value })
  } catch (error) {
    console.error('Failed to load function points:', error)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  formData.name = ''
  formData.description = ''
  formData.test_type = 'functional'
  formData.priority = 'p2'
  formData.module = ''
  formData.acceptance_criteria = ''
  editingId.value = ''
  isEdit.value = false
}

const showAddDialog = () => {
  resetForm()
  dialogVisible.value = true
}

const showEditDialog = (fp: FunctionPoint) => {
  isEdit.value = true
  editingId.value = fp.id
  formData.name = fp.name
  formData.description = fp.description || ''
  formData.test_type = fp.test_type || 'functional'
  formData.priority = fp.priority || 'p2'
  formData.module = fp.module || ''
  formData.acceptance_criteria = fp.acceptance_criteria || ''
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const data = {
        ...formData,
        project_id: selectedProject.value,
        status: isEdit.value ? 'pending' : undefined
      }
      
      if (isEdit.value) {
        await functionPointApi.update(editingId.value, data)
        ElMessage.success('更新成功，状态已重置为待审核')
      } else {
        await functionPointApi.create(data)
        ElMessage.success('创建成功')
      }
      
      dialogVisible.value = false
      loadFunctionPoints()
    } catch (error: any) {
      console.error('Failed to save:', error)
      ElMessage.error(error?.response?.data?.detail || '保存失败')
    } finally {
      submitting.value = false
    }
  })
}

const approveFP = async (fp: FunctionPoint) => {
  try {
    await functionPointApi.approve(fp.id)
    ElMessage.success('审核通过')
    loadFunctionPoints()
  } catch (error) {
    console.error('Failed to approve:', error)
  }
}

const rejectFP = async (fp: FunctionPoint) => {
  try {
    await functionPointApi.reject(fp.id)
    ElMessage.success('已拒绝')
    loadFunctionPoints()
  } catch (error) {
    console.error('Failed to reject:', error)
  }
}

const deleteFP = async (fp: FunctionPoint) => {
  try {
    await ElMessageBox.confirm(`确定要删除功能点「${fp.name}」吗？`, '删除确认', {
      type: 'warning'
    })
    await functionPointApi.delete(fp.id)
    ElMessage.success('删除成功')
    loadFunctionPoints()
  } catch (error: any) {
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
.function-points-page {
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
      
      .create-btn {
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
    
    .fp-list {
      .fp-item {
        display: flex;
        align-items: center;
        padding: 16px 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(255, 255, 255, 0.06);
          
          .fp-actions {
            opacity: 1;
          }
        }
        
        .fp-icon {
          width: 44px;
          height: 44px;
          border-radius: 10px;
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          
          .el-icon {
            font-size: 22px;
            color: #fff;
          }
        }
        
        .fp-info {
          flex: 1;
          
          .fp-name {
            font-size: 15px;
            font-weight: 500;
            margin-bottom: 6px;
          }
          
          .fp-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            
            .meta-tag {
              padding: 2px 8px;
              border-radius: 4px;
            }
            
            .type-tag {
              background: rgba(102, 126, 234, 0.2);
              color: #667eea;
            }
            
            .priority-tag {
              &.p0, &.p1 {
                background: rgba(245, 108, 108, 0.2);
                color: #f56c6c;
              }
              
              &.p2 {
                background: rgba(230, 162, 60, 0.2);
                color: #e6a23c;
              }
              
              &.p3, &.p4 {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.6);
              }
            }
            
            .meta-module {
              color: rgba(255, 255, 255, 0.5);
            }
          }
        }
        
        .fp-status {
          font-size: 12px;
          padding: 4px 12px;
          border-radius: 4px;
          margin-right: 16px;
          
          &.pending {
            background: rgba(230, 162, 60, 0.2);
            color: #e6a23c;
          }
          
          &.approved {
            background: rgba(103, 194, 58, 0.2);
            color: #67c23a;
          }
          
          &.rejected {
            background: rgba(245, 108, 108, 0.2);
            color: #f56c6c;
          }
        }
        
        .fp-actions {
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
