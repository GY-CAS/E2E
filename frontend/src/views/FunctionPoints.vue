<template>
  <div class="function-points-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>功能点列表</span>
            <el-select v-model="selectedProject" placeholder="选择项目" style="margin-left: 16px; width: 200px;" clearable @change="loadFunctionPoints">
              <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </div>
        </div>
      </template>
      
      <el-table :data="functionPoints" v-loading="loading" stripe>
        <el-table-column prop="name" label="功能点名称" min-width="200" />
        <el-table-column prop="test_type" label="测试类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTestTypeColor(row.test_type)">{{ getTestTypeLabel(row.test_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="getPriorityColor(row.priority)">{{ row.priority.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="success" link @click="approveFP(row)" :disabled="row.status !== 'pending'">通过</el-button>
            <el-button type="danger" link @click="rejectFP(row)" :disabled="row.status !== 'pending'">拒绝</el-button>
            <el-button type="primary" link @click="generateTestCases(row)" :disabled="row.status !== 'approved'">生成用例</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { functionPointApi, projectApi, type FunctionPoint, type Project } from '@/api'

const router = useRouter()
const loading = ref(false)
const functionPoints = ref<FunctionPoint[]>([])
const projects = ref<Project[]>([])
const selectedProject = ref<string>('')

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
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝'
}

const statusTypes: Record<string, string> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger'
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

const generateTestCases = (fp: FunctionPoint) => {
  router.push(`/test-cases/generate?function_point_id=${fp.id}`)
}

onMounted(async () => {
  await loadProjects()
})
</script>

<style lang="scss" scoped>
.function-points-page {
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
