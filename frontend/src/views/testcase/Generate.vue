<template>
  <div class="generate-page">
    <el-card>
      <template #header>
        <span>AI生成测试用例</span>
      </template>
      
      <el-steps :active="currentStep" finish-status="success" simple style="margin-bottom: 30px;">
        <el-step title="选择项目" />
        <el-step title="上传文档" />
        <el-step title="生成功能点" />
        <el-step title="审核确认" />
        <el-step title="生成用例" />
      </el-steps>
      
      <div class="step-content">
        <div v-show="currentStep === 0" class="step-panel">
          <el-form :model="formData" label-width="100px">
            <el-form-item label="选择项目">
              <el-select v-model="formData.projectId" placeholder="请选择项目" style="width: 100%;">
                <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="测试类型">
              <el-checkbox-group v-model="formData.testTypes">
                <el-checkbox label="functional">功能测试</el-checkbox>
                <el-checkbox label="performance">性能测试</el-checkbox>
                <el-checkbox label="security">安全测试</el-checkbox>
                <el-checkbox label="reliability">可靠性测试</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </div>
        
        <div v-show="currentStep === 1" class="step-panel">
          <el-upload
            class="upload-area"
            drag
            multiple
            :file-list="fileList"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、Word、Markdown、TXT 等格式文档
              </div>
            </template>
          </el-upload>
        </div>
        
        <div v-show="currentStep === 2" class="step-panel">
          <div class="generating" v-if="isGenerating">
            <el-icon class="is-loading" :size="40"><Loading /></el-icon>
            <p>AI正在分析文档并生成功能点...</p>
          </div>
          <div v-else>
            <el-table :data="generatedFunctionPoints" stripe max-height="400">
              <el-table-column prop="name" label="功能点名称" min-width="200" />
              <el-table-column prop="test_type" label="测试类型" width="120">
                <template #default="{ row }">
                  <el-tag>{{ getTestTypeLabel(row.test_type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="priority" label="优先级" width="80">
                <template #default="{ row }">
                  <el-tag :type="getPriorityColor(row.priority)">{{ row.priority.toUpperCase() }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ $index }">
                  <el-button type="danger" link @click="removeFunctionPoint($index)">移除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        
        <div v-show="currentStep === 3" class="step-panel">
          <el-result
            icon="success"
            title="功能点审核完成"
            sub-title="请确认功能点无误后继续生成测试用例"
          >
            <template #extra>
              <p>共 {{ generatedFunctionPoints.length }} 个功能点待生成测试用例</p>
            </template>
          </el-result>
        </div>
        
        <div v-show="currentStep === 4" class="step-panel">
          <div class="generating" v-if="isGenerating">
            <el-icon class="is-loading" :size="40"><Loading /></el-icon>
            <p>AI正在生成测试用例...</p>
          </div>
          <el-result
            v-else
            icon="success"
            title="测试用例生成完成"
            :sub-title="`成功生成 ${generatedTestCases.length} 个测试用例`"
          >
            <template #extra>
              <el-button type="primary" @click="viewTestCases">查看用例</el-button>
              <el-button @click="resetGenerate">继续生成</el-button>
            </template>
          </el-result>
        </div>
      </div>
      
      <div class="step-actions">
        <el-button v-if="currentStep > 0" @click="prevStep">上一步</el-button>
        <el-button v-if="currentStep < 4" type="primary" @click="nextStep" :disabled="!canNextStep">
          {{ currentStep === 2 || currentStep === 4 ? '生成' : '下一步' }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, Loading } from '@element-plus/icons-vue'
import { projectApi, generatorApi, type Project } from '@/api'

const router = useRouter()
const currentStep = ref(0)
const isGenerating = ref(false)
const projects = ref<Project[]>([])
const fileList = ref<any[]>([])
const generatedFunctionPoints = ref<any[]>([])
const generatedTestCases = ref<any[]>([])

const formData = reactive({
  projectId: '',
  testTypes: ['functional'] as string[]
})

const canNextStep = computed(() => {
  switch (currentStep.value) {
    case 0:
      return formData.projectId !== ''
    case 1:
      return fileList.value.length > 0
    case 2:
      return generatedFunctionPoints.value.length > 0
    case 3:
      return true
    default:
      return false
  }
})

const testTypeLabels: Record<string, string> = {
  functional: '功能测试',
  performance: '性能测试',
  security: '安全测试',
  reliability: '可靠性测试'
}

const priorityColors: Record<string, string> = {
  p0: 'danger',
  p1: 'warning',
  p2: 'primary',
  p3: 'info',
  p4: 'info'
}

const getTestTypeLabel = (type: string) => testTypeLabels[type] || type
const getPriorityColor = (priority: string) => priorityColors[priority] || 'info'

const loadProjects = async () => {
  try {
    projects.value = await projectApi.list()
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

const handleFileChange = (file: any, files: any[]) => {
  fileList.value = files
}

const handleFileRemove = (file: any, files: any[]) => {
  fileList.value = files
}

const removeFunctionPoint = (index: number) => {
  generatedFunctionPoints.value.splice(index, 1)
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const nextStep = async () => {
  if (currentStep.value === 2) {
    await generateFunctionPoints()
  } else if (currentStep.value === 4) {
    await generateTestCases()
  } else {
    currentStep.value++
  }
}

const generateFunctionPoints = async () => {
  isGenerating.value = true
  try {
    const result = await generatorApi.generateFunctionPoints({
      project_id: formData.projectId,
      document_ids: [],
      test_types: formData.testTypes
    })
    
    generatedFunctionPoints.value = result.function_points || []
    currentStep.value++
    ElMessage.success('功能点生成完成')
  } catch (error) {
    console.error('Failed to generate function points:', error)
    ElMessage.error('生成失败')
  } finally {
    isGenerating.value = false
  }
}

const generateTestCases = async () => {
  isGenerating.value = true
  try {
    const fpIds = generatedFunctionPoints.value.map(fp => fp.id).filter(Boolean)
    
    const result = await generatorApi.generateTestCases({
      project_id: formData.projectId,
      function_point_ids: fpIds.length > 0 ? fpIds : ['mock-id']
    })
    
    generatedTestCases.value = result.test_cases || []
    currentStep.value++
    ElMessage.success('测试用例生成完成')
  } catch (error) {
    console.error('Failed to generate test cases:', error)
    ElMessage.error('生成失败')
  } finally {
    isGenerating.value = false
  }
}

const viewTestCases = () => {
  router.push('/test-cases')
}

const resetGenerate = () => {
  currentStep.value = 0
  formData.projectId = ''
  formData.testTypes = ['functional']
  fileList.value = []
  generatedFunctionPoints.value = []
  generatedTestCases.value = []
}

onMounted(() => {
  loadProjects()
})
</script>

<style lang="scss" scoped>
.generate-page {
  .step-content {
    min-height: 400px;
    
    .step-panel {
      padding: 20px;
    }
    
    .upload-area {
      width: 100%;
      
      :deep(.el-upload-dragger) {
        width: 100%;
      }
    }
    
    .generating {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 300px;
      
      p {
        margin-top: 20px;
        color: #909399;
      }
    }
  }
  
  .step-actions {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-top: 30px;
  }
}
</style>
