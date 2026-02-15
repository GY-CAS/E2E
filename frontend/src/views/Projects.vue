<template>
  <div class="projects-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>项目列表</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新建项目
          </el-button>
        </div>
      </template>
      
      <el-table :data="projects" v-loading="loading" stripe>
        <el-table-column prop="name" label="项目名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '活跃' : '归档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewProject(row)">查看</el-button>
            <el-button type="primary" link @click="editProject(row)">编辑</el-button>
            <el-button type="danger" link @click="deleteProject(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadProjects"
        @current-change="loadProjects"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="editingProject ? '编辑项目' : '新建项目'" width="500px">
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { projectApi, type Project } from '@/api'
import dayjs from 'dayjs'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const projects = ref<Project[]>([])
const dialogVisible = ref(false)
const editingProject = ref<Project | null>(null)
const formRef = ref<FormInstance>()

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  name: '',
  description: ''
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss')

const loadProjects = async () => {
  loading.value = true
  try {
    const data = await projectApi.list({
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    })
    projects.value = data
    pagination.total = data.length
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

const deleteProject = async (project: Project) => {
  try {
    await ElMessageBox.confirm('确定要删除该项目吗？', '提示', {
      type: 'warning'
    })
    await projectApi.delete(project.id)
    ElMessage.success('删除成功')
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
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
