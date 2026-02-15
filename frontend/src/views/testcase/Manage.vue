<template>
  <div class="test-cases-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>测试用例列表</span>
            <el-select v-model="selectedProject" placeholder="选择项目" style="margin-left: 16px; width: 200px;" clearable @change="loadTestCases">
              <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </div>
          <div class="header-right">
            <el-button @click="exportTestCases" :disabled="selectedCases.length === 0">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table 
        :data="testCases" 
        v-loading="loading" 
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="title" label="用例标题" min-width="250" show-overflow-tooltip />
        <el-table-column prop="test_type" label="测试类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTestTypeColor(row.test_type)">{{ getTestTypeLabel(row.test_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="test_category" label="分类" width="100" />
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="getPriorityColor(row.priority)">{{ row.priority.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewTestCase(row)">查看</el-button>
            <el-button type="success" link @click="approveTestCase(row)" :disabled="row.status !== 'draft'">通过</el-button>
            <el-button type="primary" link @click="generateScript(row)" :disabled="row.status !== 'approved'">生成脚本</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="detailVisible" title="测试用例详情" width="800px">
      <el-descriptions :column="2" border v-if="currentCase">
        <el-descriptions-item label="用例标题" :span="2">{{ currentCase.title }}</el-descriptions-item>
        <el-descriptions-item label="测试类型">{{ getTestTypeLabel(currentCase.test_type) }}</el-descriptions-item>
        <el-descriptions-item label="测试分类">{{ currentCase.test_category }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ currentCase.priority.toUpperCase() }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ getStatusLabel(currentCase.status) }}</el-descriptions-item>
        <el-descriptions-item label="前置条件" :span="2">{{ currentCase.preconditions || '无' }}</el-descriptions-item>
        <el-descriptions-item label="测试步骤" :span="2">
          <el-steps direction="vertical" :active="currentCase.test_steps.length">
            <el-step v-for="step in currentCase.test_steps" :key="step.step_num" :title="`步骤${step.step_num}`">
              <template #description>
                <div class="step-detail">
                  <p><strong>操作：</strong>{{ step.action }}</p>
                  <p><strong>预期结果：</strong>{{ step.expected_result }}</p>
                </div>
              </template>
            </el-step>
          </el-steps>
        </el-descriptions-item>
        <el-descriptions-item label="预期结果" :span="2">{{ currentCase.expected_results || '无' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { testCaseApi, projectApi, type TestCase, type Project } from '@/api'

const loading = ref(false)
const testCases = ref<TestCase[]>([])
const projects = ref<Project[]>([])
const selectedProject = ref<string>('')
const selectedCases = ref<TestCase[]>([])
const detailVisible = ref(false)
const currentCase = ref<TestCase | null>(null)

const testTypeLabels: Record<string, string> = {
  functional: '功能测试',
  performance: '性能测试',
  security: '安全测试',
  reliability: '可靠性测试'
}

const testTypeColors: Record<string, string> = {
  functional: 'primary',
  performance: 'warning',
  security: 'danger',
  reliability: 'info'
}

const priorityColors: Record<string, string> = {
  p0: 'danger',
  p1: 'warning',
  p2: 'primary',
  p3: 'info',
  p4: 'info'
}

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

const getTestTypeLabel = (type: string) => testTypeLabels[type] || type
const getTestTypeColor = (type: string) => testTypeColors[type] || 'info'
const getPriorityColor = (priority: string) => priorityColors[priority] || 'info'
const getStatusLabel = (status: string) => statusLabels[status] || status
const getStatusType = (status: string) => statusTypes[status] || 'info'

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

const handleSelectionChange = (selection: TestCase[]) => {
  selectedCases.value = selection
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

const generateScript = (tc: TestCase) => {
  ElMessage.info('脚本生成功能开发中')
}

const exportTestCases = () => {
  ElMessage.info('导出功能开发中')
}

onMounted(async () => {
  await loadProjects()
})
</script>

<style lang="scss" scoped>
.test-cases-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-left {
      display: flex;
      align-items: center;
    }
  }
  
  .step-detail {
    p {
      margin: 4px 0;
      font-size: 13px;
    }
  }
}
</style>
