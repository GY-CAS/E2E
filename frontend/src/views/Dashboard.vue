<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon projects">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.projects }}</div>
              <div class="stat-label">项目总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon documents">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.documents }}</div>
              <div class="stat-label">文档总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon testcases">
              <el-icon><Tickets /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.testCases }}</div>
              <div class="stat-label">测试用例</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon scripts">
              <el-icon><DocumentCopy /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.scripts }}</div>
              <div class="stat-label">测试脚本</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>快速操作</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="quick-action" @click="$router.push('/projects')">
                <el-icon class="action-icon"><FolderAdd /></el-icon>
                <span>创建项目</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="quick-action" @click="$router.push('/documents')">
                <el-icon class="action-icon"><Upload /></el-icon>
                <span>上传文档</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="quick-action" @click="$router.push('/test-cases/generate')">
                <el-icon class="action-icon"><MagicStick /></el-icon>
                <span>AI生成用例</span>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>最近项目</span>
          </template>
          <div class="recent-projects">
            <div v-for="project in recentProjects" :key="project.id" class="project-item">
              <span class="project-name">{{ project.name }}</span>
              <el-tag size="small">{{ project.status }}</el-tag>
            </div>
            <el-empty v-if="recentProjects.length === 0" description="暂无项目" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Folder, Document, Tickets, DocumentCopy, FolderAdd, Upload, MagicStick } from '@element-plus/icons-vue'
import { projectApi, documentApi, testCaseApi, testScriptApi, type Project } from '@/api'

const stats = ref({
  projects: 0,
  documents: 0,
  testCases: 0,
  scripts: 0
})

const recentProjects = ref<Project[]>([])

onMounted(async () => {
  try {
    const [projects, documents, testCases, scripts] = await Promise.all([
      projectApi.list({ limit: 5 }),
      documentApi.list({ limit: 1 }),
      testCaseApi.list({ limit: 1 }),
      testScriptApi.list({ limit: 1 })
    ])
    
    recentProjects.value = projects
    stats.value.projects = projects.length
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
})
</script>

<style lang="scss" scoped>
.dashboard {
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      
      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
        
        .el-icon {
          font-size: 28px;
          color: #fff;
        }
        
        &.projects {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.documents {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        &.testcases {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.scripts {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }
      
      .stat-info {
        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: #303133;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }
  }
  
  .quick-action {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 30px 20px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
    background-color: #f5f7fa;
    
    &:hover {
      background-color: #e6f0ff;
      transform: translateY(-2px);
    }
    
    .action-icon {
      font-size: 36px;
      color: #409EFF;
      margin-bottom: 12px;
    }
    
    span {
      font-size: 14px;
      color: #606266;
    }
  }
  
  .recent-projects {
    .project-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid #EBEEF5;
      
      &:last-child {
        border-bottom: none;
      }
      
      .project-name {
        font-size: 14px;
        color: #303133;
      }
    }
  }
}
</style>
