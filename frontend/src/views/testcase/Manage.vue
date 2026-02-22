<template>
  <div class="test-cases-page">
    <div class="page-header">
      <div class="header-content">
        <div class="title-row">
          <div class="title-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
            </svg>
          </div>
          <div>
            <h1 class="page-title">测试用例管理</h1>
            <p class="page-subtitle">高效管理项目测试用例，保障产品质量</p>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <div class="project-selector">
          <label>当前项目</label>
          <el-select v-model="selectedProject" placeholder="选择项目" class="project-select" clearable @change="loadTestCases">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </div>
        <el-button type="primary" class="create-btn" @click="showAddDialog" :disabled="!selectedProject">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          新增用例
        </el-button>
      </div>
    </div>
    
    <div class="stats-bar" v-if="selectedProject">
      <div class="stat-item">
        <div class="stat-icon total">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ testCases.length }}</span>
          <span class="stat-label">总用例</span>
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-icon approved">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ testCases.filter(t => t.status === 'approved').length }}</span>
          <span class="stat-label">已通过</span>
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-icon pending">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ testCases.filter(t => t.status === 'draft').length }}</span>
          <span class="stat-label">待审核</span>
        </div>
      </div>
    </div>
    
    <div class="content-card">
      <div class="tc-list" v-if="testCases.length > 0">
        <div v-for="tc in testCases" :key="tc.id" class="tc-item" :class="`priority-${tc.priority}`">
          <div class="tc-priority-indicator"></div>
          <div class="tc-icon" :class="tc.test_type">
            <svg v-if="tc.test_type === 'functional'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <path d="M9 9h6M9 13h6M9 17h4"/>
            </svg>
            <svg v-else-if="tc.test_type === 'performance'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
            <svg v-else-if="tc.test_type === 'security'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 16v-4M12 8h.01"/>
            </svg>
          </div>
          <div class="tc-info">
            <div class="tc-name">{{ tc.title }}</div>
            <div class="tc-meta">
              <span class="meta-tag type-tag" :class="tc.test_type">{{ getTestTypeLabel(tc.test_type) }}</span>
              <span class="meta-tag priority-tag" :class="tc.priority">{{ tc.priority?.toUpperCase() }}</span>
              <span class="meta-category" v-if="tc.test_category">{{ tc.test_category }}</span>
            </div>
          </div>
          <div class="tc-status" :class="tc.status">
            <span class="status-dot"></span>
            {{ getStatusLabel(tc.status) }}
          </div>
          <div class="tc-actions">
            <el-tooltip content="查看详情" placement="top">
              <button class="action-btn view" @click="viewTestCase(tc)">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              </button>
            </el-tooltip>
            <el-tooltip content="编辑" placement="top">
              <button class="action-btn edit" @click="showEditDialog(tc)">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
            </el-tooltip>
            <el-tooltip content="通过审核" placement="top">
              <button class="action-btn approve" @click="approveTestCase(tc)" :disabled="tc.status === 'approved'">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </button>
            </el-tooltip>
            <el-tooltip content="拒绝" placement="top">
              <button class="action-btn reject" @click="rejectTestCase(tc)" :disabled="tc.status === 'approved' || tc.status === 'rejected'">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <button class="action-btn delete" @click="deleteTestCase(tc)">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                </svg>
              </button>
            </el-tooltip>
          </div>
        </div>
      </div>
      
      <div v-else class="empty-state">
        <div class="empty-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
        </div>
        <h3>{{ selectedProject ? '暂无测试用例' : '请先选择项目' }}</h3>
        <p>{{ selectedProject ? '点击右上角「新增用例」按钮创建第一个测试用例' : '从下拉菜单中选择一个项目开始管理测试用例' }}</p>
        <el-button v-if="selectedProject" type="primary" class="empty-btn" @click="showAddDialog">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          创建测试用例
        </el-button>
      </div>
    </div>
    
    <el-dialog v-model="detailVisible" title="测试用例详情" width="700px">
      <div class="detail-content" v-if="currentCase">
        <div class="detail-header">
          <h3 class="detail-title">{{ currentCase.title }}</h3>
          <div class="detail-tags">
            <el-tag :type="getTestTypeTag(currentCase.test_type)">{{ getTestTypeLabel(currentCase.test_type) }}</el-tag>
            <el-tag :type="getPriorityTag(currentCase.priority)">{{ currentCase.priority?.toUpperCase() }}</el-tag>
            <el-tag :type="getStatusTag(currentCase.status)">{{ getStatusLabel(currentCase.status) }}</el-tag>
          </div>
        </div>
        
        <el-descriptions :column="1" border class="detail-desc">
          <el-descriptions-item label="描述" v-if="currentCase.description">{{ currentCase.description }}</el-descriptions-item>
          <el-descriptions-item label="分类" v-if="currentCase.test_category">{{ currentCase.test_category }}</el-descriptions-item>
          <el-descriptions-item label="前置条件" v-if="currentCase.preconditions">{{ currentCase.preconditions }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="detail-section" v-if="currentCase.test_steps && currentCase.test_steps.length > 0">
          <h4>测试步骤</h4>
          <div class="steps-container">
            <div v-for="(step, index) in currentCase.test_steps" :key="index" class="step-row">
              <div class="step-number">{{ index + 1 }}</div>
              <div class="step-info">
                <div class="step-action"><strong>操作：</strong>{{ step.action }}</div>
                <div class="step-expected"><strong>预期：</strong>{{ step.expected_result }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="detail-section" v-if="currentCase.expected_results">
          <h4>预期结果</h4>
          <p class="result-content">{{ currentCase.expected_results }}</p>
        </div>
      </div>
    </el-dialog>
    
    <el-dialog v-model="formVisible" :title="isEdit ? '编辑测试用例' : '新增测试用例'" width="650px">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用例标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入测试用例标题" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="测试类型" prop="test_type">
              <el-select v-model="formData.test_type" placeholder="请选择类型" style="width: 100%;">
                <el-option label="功能测试" value="functional" />
                <el-option label="性能测试" value="performance" />
                <el-option label="安全测试" value="security" />
                <el-option label="可靠性测试" value="reliability" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="formData.priority" placeholder="请选择优先级" style="width: 100%;">
                <el-option label="P0 - 最高" value="p0" />
                <el-option label="P1 - 高" value="p1" />
                <el-option label="P2 - 中" value="p2" />
                <el-option label="P3 - 低" value="p3" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="用例描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="请输入用例描述" />
        </el-form-item>
        <el-form-item label="测试分类" prop="test_category">
          <el-input v-model="formData.test_category" placeholder="如：前端UI、后端API、业务流程等" />
        </el-form-item>
        <el-form-item label="前置条件" prop="preconditions">
          <el-input v-model="formData.preconditions" type="textarea" :rows="2" placeholder="请输入前置条件" />
        </el-form-item>
        
        <el-divider content-position="left">测试步骤</el-divider>
        
        <div class="steps-form">
          <div v-for="(step, index) in formData.test_steps" :key="index" class="step-form-item">
            <div class="step-form-header">
              <span>步骤 {{ index + 1 }}</span>
              <el-button type="danger" text size="small" @click="removeStep(index)" v-if="formData.test_steps.length > 1">
                删除
              </el-button>
            </div>
            <el-form-item :label="`操作`">
              <el-input v-model="step.action" type="textarea" :rows="2" placeholder="请输入操作步骤" />
            </el-form-item>
            <el-form-item :label="`预期结果`">
              <el-input v-model="step.expected_result" type="textarea" :rows="2" placeholder="请输入预期结果" />
            </el-form-item>
          </div>
          <el-button type="primary" plain @click="addStep" class="add-step-btn">
            + 添加步骤
          </el-button>
        </div>
        
        <el-form-item label="预期结果" prop="expected_results">
          <el-input v-model="formData.expected_results" type="textarea" :rows="3" placeholder="请输入整体预期结果" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { testCaseApi, projectApi, type TestCase, type Project } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const testCases = ref<TestCase[]>([])
const projects = ref<Project[]>([])
const selectedProject = ref<string>('')
const detailVisible = ref(false)
const currentCase = ref<TestCase | null>(null)
const formVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<string>('')

interface TestStepForm {
  step_num: number
  action: string
  expected_result: string
}

const formData = reactive({
  title: '',
  description: '',
  test_type: 'functional',
  test_category: 'functional',
  priority: 'p2',
  preconditions: '',
  test_steps: [] as TestStepForm[],
  expected_results: ''
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入用例标题', trigger: 'blur' }],
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
  draft: '草稿',
  reviewed: '已审核',
  approved: '已通过',
  rejected: '已拒绝'
}

const getTestTypeLabel = (type: string) => testTypeLabels[type] || type
const getStatusLabel = (status: string) => statusLabels[status] || status

const getTestTypeTag = (type: string): '' | 'success' | 'warning' | 'info' | 'danger' => {
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    functional: '',
    performance: 'warning',
    security: 'danger',
    reliability: 'success'
  }
  return map[type] || 'info'
}

const getPriorityTag = (priority: string): '' | 'success' | 'warning' | 'info' | 'danger' => {
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    p0: 'danger',
    p1: 'danger',
    p2: 'warning',
    p3: 'info',
    p4: 'info'
  }
  return map[priority] || 'info'
}

const getStatusTag = (status: string): '' | 'success' | 'warning' | 'info' | 'danger' => {
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    draft: 'info',
    reviewed: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

const loadProjects = async () => {
  try {
    projects.value = await projectApi.list()
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

const loadTestCases = async () => {
  if (!selectedProject.value) {
    testCases.value = []
    return
  }
  
  loading.value = true
  try {
    testCases.value = await testCaseApi.list({ project_id: selectedProject.value })
  } catch (error) {
    console.error('Failed to load test cases:', error)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  formData.title = ''
  formData.description = ''
  formData.test_type = 'functional'
  formData.test_category = 'functional'
  formData.priority = 'p2'
  formData.preconditions = ''
  formData.test_steps = [{ step_num: 1, action: '', expected_result: '' }]
  formData.expected_results = ''
  editingId.value = ''
  isEdit.value = false
}

const showAddDialog = () => {
  resetForm()
  formVisible.value = true
}

const showEditDialog = (tc: TestCase) => {
  isEdit.value = true
  editingId.value = tc.id
  formData.title = tc.title
  formData.description = tc.description || ''
  formData.test_type = tc.test_type || 'functional'
  formData.test_category = tc.test_category || 'functional'
  formData.priority = tc.priority || 'p2'
  formData.preconditions = tc.preconditions || ''
  formData.test_steps = tc.test_steps && tc.test_steps.length > 0 
    ? tc.test_steps.map((s, i) => ({ step_num: i + 1, action: s.action, expected_result: s.expected_result }))
    : [{ step_num: 1, action: '', expected_result: '' }]
  formData.expected_results = tc.expected_results || ''
  formVisible.value = true
}

const addStep = () => {
  formData.test_steps.push({
    step_num: formData.test_steps.length + 1,
    action: '',
    expected_result: ''
  })
}

const removeStep = (index: number) => {
  formData.test_steps.splice(index, 1)
  formData.test_steps.forEach((step, i) => {
    step.step_num = i + 1
  })
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const testSteps = formData.test_steps
        .filter(s => s.action.trim())
        .map((s, i) => ({
          step_num: i + 1,
          action: s.action,
          expected_result: s.expected_result
        }))
      
      const data = {
        title: formData.title,
        description: formData.description,
        test_type: formData.test_type,
        test_category: formData.test_category,
        priority: formData.priority,
        preconditions: formData.preconditions,
        test_steps: testSteps,
        expected_results: formData.expected_results,
        project_id: selectedProject.value,
        status: isEdit.value ? 'draft' : undefined
      }
      
      if (isEdit.value) {
        await testCaseApi.update(editingId.value, data)
        ElMessage.success('更新成功，状态已重置为待审核')
      } else {
        await testCaseApi.create(data)
        ElMessage.success('创建成功')
      }
      
      formVisible.value = false
      loadTestCases()
    } catch (error: any) {
      console.error('Failed to save:', error)
      ElMessage.error(error?.response?.data?.detail || '保存失败')
    } finally {
      submitting.value = false
    }
  })
}

const viewTestCase = (tc: TestCase) => {
  currentCase.value = tc
  detailVisible.value = true
}

const approveTestCase = async (tc: TestCase) => {
  try {
    await testCaseApi.approve(tc.id)
    ElMessage.success('审核通过')
    loadTestCases()
  } catch (error) {
    console.error('Failed to approve:', error)
  }
}

const rejectTestCase = async (tc: TestCase) => {
  try {
    await testCaseApi.reject(tc.id)
    ElMessage.success('已拒绝')
    loadTestCases()
  } catch (error) {
    console.error('Failed to reject:', error)
  }
}

const deleteTestCase = async (tc: TestCase) => {
  try {
    await ElMessageBox.confirm(`确定要删除测试用例「${tc.title}」吗？`, '删除确认', {
      type: 'warning'
    })
    await testCaseApi.delete(tc.id)
    ElMessage.success('删除成功')
    loadTestCases()
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
.test-cases-page {
  min-height: calc(100vh - 60px);
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
  padding: 24px;
  color: #fff;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 20px 24px;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border-radius: 16px;
    border: 1px solid rgba(102, 126, 234, 0.2);
    backdrop-filter: blur(10px);
    
    .header-content {
      .title-row {
        display: flex;
        align-items: center;
        gap: 16px;
      }
      
      .title-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        
        svg {
          width: 24px;
          height: 24px;
          color: #fff;
        }
      }
      
      .page-title {
        font-size: 24px;
        font-weight: 700;
        margin: 0 0 4px 0;
        background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.8) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      
      .page-subtitle {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.5);
        margin: 0;
      }
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .project-selector {
        display: flex;
        flex-direction: column;
        gap: 4px;
        
        label {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.5);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
      }
      
      .project-select {
        width: 220px;
      }
      
      .create-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        height: 40px;
        padding: 0 20px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        
        .btn-icon {
          width: 16px;
          height: 16px;
        }
        
        &:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        }
        
        &:disabled {
          opacity: 0.5;
        }
      }
    }
  }
  
  .stats-bar {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px 20px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      flex: 1;
      
      .stat-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        
        svg {
          width: 20px;
          height: 20px;
        }
        
        &.total {
          background: rgba(102, 126, 234, 0.2);
          color: #667eea;
        }
        
        &.approved {
          background: rgba(103, 194, 58, 0.2);
          color: #67c23a;
        }
        
        &.pending {
          background: rgba(230, 162, 60, 0.2);
          color: #e6a23c;
        }
      }
      
      .stat-info {
        display: flex;
        flex-direction: column;
        
        .stat-value {
          font-size: 24px;
          font-weight: 700;
          line-height: 1;
        }
        
        .stat-label {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.5);
          margin-top: 4px;
        }
      }
    }
  }
  
  .content-card {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 20px;
    
    .tc-list {
      .tc-item {
        display: flex;
        align-items: center;
        padding: 16px 20px;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        
        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 3px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          opacity: 0;
          transition: opacity 0.3s ease;
        }
        
        &:hover {
          background: rgba(255, 255, 255, 0.04);
          border-color: rgba(102, 126, 234, 0.3);
          
          &::before {
            opacity: 1;
          }
          
          .tc-actions {
            opacity: 1;
          }
        }
        
        &.priority-p0, &.priority-p1 {
          .tc-priority-indicator {
            position: absolute;
            right: 0;
            top: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(135deg, #f56c6c 0%, #e6a23c 100%);
          }
        }
        
        .tc-icon {
          width: 44px;
          height: 44px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          flex-shrink: 0;
          
          svg {
            width: 22px;
            height: 22px;
            color: #fff;
          }
          
          &.functional {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          
          &.performance {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          }
          
          &.security {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          }
          
          &.reliability {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
          }
        }
        
        .tc-info {
          flex: 1;
          min-width: 0;
          
          .tc-name {
            font-size: 15px;
            font-weight: 500;
            margin-bottom: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          
          .tc-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            
            .meta-tag {
              padding: 2px 8px;
              border-radius: 4px;
              font-weight: 500;
            }
            
            .type-tag {
              &.functional {
                background: rgba(102, 126, 234, 0.2);
                color: #667eea;
              }
              
              &.performance {
                background: rgba(245, 87, 108, 0.2);
                color: #f5576c;
              }
              
              &.security {
                background: rgba(79, 172, 254, 0.2);
                color: #4facfe;
              }
              
              &.reliability {
                background: rgba(67, 233, 123, 0.2);
                color: #43e97b;
              }
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
            
            .meta-category {
              color: rgba(255, 255, 255, 0.4);
            }
          }
        }
        
        .tc-status {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          padding: 4px 12px;
          border-radius: 20px;
          margin-right: 16px;
          font-weight: 500;
          
          .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
          }
          
          &.draft {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.6);
            
            .status-dot {
              background: rgba(255, 255, 255, 0.4);
            }
          }
          
          &.reviewed {
            background: rgba(230, 162, 60, 0.2);
            color: #e6a23c;
            
            .status-dot {
              background: #e6a23c;
            }
          }
          
          &.approved {
            background: rgba(103, 194, 58, 0.2);
            color: #67c23a;
            
            .status-dot {
              background: #67c23a;
            }
          }
          
          &.rejected {
            background: rgba(245, 108, 108, 0.2);
            color: #f56c6c;
            
            .status-dot {
              background: #f56c6c;
            }
          }
        }
        
        .tc-actions {
          display: flex;
          gap: 4px;
          opacity: 0.5;
          transition: opacity 0.3s ease;
          
          .action-btn {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            border: none;
            background: rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.6);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            
            svg {
              width: 16px;
              height: 16px;
            }
            
            &:hover:not(:disabled) {
              background: rgba(255, 255, 255, 0.1);
              color: #fff;
            }
            
            &.view:hover {
              background: rgba(102, 126, 234, 0.2);
              color: #667eea;
            }
            
            &.edit:hover {
              background: rgba(240, 147, 251, 0.2);
              color: #f093fb;
            }
            
            &.approve:hover:not(:disabled) {
              background: rgba(103, 194, 58, 0.2);
              color: #67c23a;
            }
            
            &.reject:hover:not(:disabled) {
              background: rgba(245, 108, 108, 0.2);
              color: #f56c6c;
            }
            
            &.delete:hover {
              background: rgba(245, 108, 108, 0.2);
              color: #f56c6c;
            }
            
            &:disabled {
              opacity: 0.3;
              cursor: not-allowed;
            }
          }
        }
      }
    }
    
    .empty-state {
      text-align: center;
      padding: 80px 20px;
      
      .empty-icon {
        width: 80px;
        height: 80px;
        margin: 0 auto 24px;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        
        svg {
          width: 40px;
          height: 40px;
          color: rgba(102, 126, 234, 0.5);
        }
      }
      
      h3 {
        font-size: 18px;
        font-weight: 600;
        margin: 0 0 8px 0;
        color: rgba(255, 255, 255, 0.8);
      }
      
      p {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.4);
        margin: 0 0 24px 0;
      }
      
      .empty-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        height: 44px;
        padding: 0 24px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        
        .btn-icon {
          width: 16px;
          height: 16px;
        }
      }
    }
  }
}

.detail-content {
  .detail-header {
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ebeef5;
    
    .detail-title {
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 12px 0;
      color: #303133;
    }
    
    .detail-tags {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
  }
  
  .detail-desc {
    margin-bottom: 24px;
  }
  
  .detail-section {
    margin-bottom: 24px;
    
    h4 {
      font-size: 15px;
      font-weight: 600;
      margin: 0 0 16px 0;
      padding-bottom: 8px;
      border-bottom: 2px solid #409eff;
      color: #303133;
      display: inline-block;
    }
    
    .steps-container {
      .step-row {
        display: flex;
        gap: 16px;
        padding: 16px;
        background: #f5f7fa;
        border-radius: 8px;
        margin-bottom: 12px;
        border-left: 3px solid #409eff;
        
        .step-number {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 13px;
          font-weight: 600;
          color: #fff;
          flex-shrink: 0;
        }
        
        .step-info {
          flex: 1;
          
          .step-action, .step-expected {
            font-size: 14px;
            line-height: 1.8;
            margin-bottom: 8px;
            color: #606266;
            
            strong {
              color: #303133;
              font-weight: 600;
            }
          }
          
          .step-expected {
            color: #67c23a;
            margin-bottom: 0;
            
            strong {
              color: #67c23a;
            }
          }
        }
      }
    }
    
    .result-content {
      padding: 16px;
      background: linear-gradient(135deg, rgba(103, 194, 58, 0.1) 0%, rgba(103, 194, 58, 0.05) 100%);
      border-radius: 8px;
      margin: 0;
      font-size: 14px;
      line-height: 1.8;
      color: #606266;
      border-left: 3px solid #67c23a;
    }
  }
}

.steps-form {
  .step-form-item {
    padding: 16px;
    background: #f5f7fa;
    border-radius: 8px;
    margin-bottom: 12px;
    border-left: 3px solid #409eff;
    
    .step-form-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      font-weight: 600;
      color: #303133;
      font-size: 14px;
    }
  }
  
  .add-step-btn {
    width: 100%;
  }
}
</style>
