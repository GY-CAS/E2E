<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div class="header-content">
        <h1 class="title">测试用例生成平台</h1>
        <p class="subtitle">AI驱动的智能化测试用例管理系统</p>
      </div>
      <div class="header-time">
        <div class="time">{{ currentTime }}</div>
        <div class="date">{{ currentDate }}</div>
      </div>
    </div>
    
    <div class="stats-grid">
      <div class="stat-card projects">
        <div class="stat-bg"></div>
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ animatedStats.projects }}</div>
            <div class="stat-label">项目总数</div>
          </div>
        </div>
        <div class="stat-trend">
          <el-icon><TrendCharts /></el-icon>
          <span>活跃项目</span>
        </div>
      </div>
      
      <div class="stat-card documents">
        <div class="stat-bg"></div>
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ animatedStats.documents }}</div>
            <div class="stat-label">文档总数</div>
          </div>
        </div>
        <div class="stat-trend">
          <el-icon><Files /></el-icon>
          <span>已解析</span>
        </div>
      </div>
      
      <div class="stat-card testcases">
        <div class="stat-bg"></div>
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Tickets /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ animatedStats.testCases }}</div>
            <div class="stat-label">测试用例</div>
          </div>
        </div>
        <div class="stat-trend">
          <el-icon><CircleCheck /></el-icon>
          <span>已审核</span>
        </div>
      </div>
      
      <div class="stat-card scripts">
        <div class="stat-bg"></div>
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><DocumentCopy /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ animatedStats.scripts }}</div>
            <div class="stat-label">测试脚本</div>
          </div>
        </div>
        <div class="stat-trend">
          <el-icon><VideoPlay /></el-icon>
          <span>可执行</span>
        </div>
      </div>
    </div>
    
    <div class="main-content">
      <div class="quick-actions-panel">
        <div class="panel-header">
          <h2>快速操作</h2>
          <div class="panel-line"></div>
        </div>
        <div class="actions-grid">
          <div class="action-card" @click="$router.push('/projects')">
            <div class="action-icon-wrapper">
              <el-icon><FolderAdd /></el-icon>
            </div>
            <div class="action-info">
              <h3>创建项目</h3>
              <p>新建测试项目</p>
            </div>
            <div class="action-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
          
          <div class="action-card" @click="$router.push('/documents')">
            <div class="action-icon-wrapper">
              <el-icon><Upload /></el-icon>
            </div>
            <div class="action-info">
              <h3>上传文档</h3>
              <p>导入需求文档</p>
            </div>
            <div class="action-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
          
          <div class="action-card" @click="$router.push('/test-cases/generate')">
            <div class="action-icon-wrapper ai">
              <el-icon><MagicStick /></el-icon>
            </div>
            <div class="action-info">
              <h3>AI生成用例</h3>
              <p>智能生成测试用例</p>
            </div>
            <div class="action-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
          
          <div class="action-card" @click="$router.push('/function-points')">
            <div class="action-icon-wrapper">
              <el-icon><List /></el-icon>
            </div>
            <div class="action-info">
              <h3>功能点管理</h3>
              <p>查看功能点列表</p>
            </div>
            <div class="action-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>
      
      <div class="side-panel">
        <div class="panel-header">
          <h2>最近项目</h2>
          <div class="panel-line"></div>
        </div>
        <div class="recent-projects">
          <div v-for="project in recentProjects" :key="project.id" class="project-item" @click="$router.push(`/test-cases/generate?project_id=${project.id}&reset=true`)">
            <div class="project-icon">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="project-info">
              <div class="project-name">{{ project.name }}</div>
              <div class="project-meta">
                <span class="project-status" :class="project.status">{{ project.status }}</span>
                <span class="project-date">{{ formatDate(project.created_at) }}</span>
              </div>
            </div>
            <el-icon class="project-arrow"><ArrowRight /></el-icon>
          </div>
          <div v-if="recentProjects.length === 0" class="empty-state">
            <el-icon><FolderAdd /></el-icon>
            <p>暂无项目，点击创建</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { 
  Folder, Document, Tickets, DocumentCopy, 
  FolderAdd, Upload, MagicStick, List,
  TrendCharts, Files, CircleCheck, VideoPlay,
  ArrowRight
} from '@element-plus/icons-vue'
import { projectApi, documentApi, testCaseApi, testScriptApi, type Project } from '@/api'

const stats = ref({
  projects: 0,
  documents: 0,
  testCases: 0,
  scripts: 0
})

const animatedStats = ref({
  projects: 0,
  documents: 0,
  testCases: 0,
  scripts: 0
})

const recentProjects = ref<Project[]>([])
const currentTime = ref('')
const currentDate = ref('')
let timeInterval: number | null = null

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  currentDate.value = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
}

const animateNumber = (target: number, key: keyof typeof animatedStats.value) => {
  const duration = 1000
  const start = animatedStats.value[key]
  const increment = (target - start) / (duration / 16)
  let current = start
  
  const animate = () => {
    current += increment
    if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
      animatedStats.value[key] = target
    } else {
      animatedStats.value[key] = Math.round(current)
      requestAnimationFrame(animate)
    }
  }
  
  requestAnimationFrame(animate)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

onMounted(async () => {
  updateTime()
  timeInterval = window.setInterval(updateTime, 1000)
  
  try {
    const [projects, documents, testCases, scripts] = await Promise.all([
      projectApi.list({ limit: 5 }),
      documentApi.list({ limit: 100 }),
      testCaseApi.list({ limit: 100 }),
      testScriptApi.list({ limit: 100 })
    ])
    
    recentProjects.value = projects
    stats.value.projects = projects.length
    stats.value.documents = documents.length
    stats.value.testCases = testCases.length
    stats.value.scripts = scripts.length
    
    animateNumber(stats.value.projects, 'projects')
    animateNumber(stats.value.documents, 'documents')
    animateNumber(stats.value.testCases, 'testCases')
    animateNumber(stats.value.scripts, 'scripts')
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style lang="scss" scoped>
.dashboard {
  min-height: calc(100vh - 60px);
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 24px;
  color: #fff;
  
  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    padding: 24px 32px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    
    .header-content {
      .title {
        font-size: 28px;
        font-weight: 600;
        margin: 0 0 8px 0;
        background: linear-gradient(90deg, #fff, #a8b2d1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }
      
      .subtitle {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.6);
        margin: 0;
      }
    }
    
    .header-time {
      text-align: right;
      
      .time {
        font-size: 32px;
        font-weight: 300;
        font-family: 'Courier New', monospace;
        letter-spacing: 2px;
      }
      
      .date {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.5);
        margin-top: 4px;
      }
    }
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 24px;
    
    .stat-card {
      position: relative;
      padding: 24px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      overflow: hidden;
      transition: all 0.3s ease;
      
      &:hover {
        transform: translateY(-4px);
        border-color: rgba(255, 255, 255, 0.2);
        
        .stat-bg {
          opacity: 0.15;
        }
      }
      
      .stat-bg {
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        opacity: 0.08;
        transition: opacity 0.3s ease;
      }
      
      &.projects .stat-bg {
        background: radial-gradient(circle, #667eea 0%, transparent 70%);
      }
      
      &.documents .stat-bg {
        background: radial-gradient(circle, #f093fb 0%, transparent 70%);
      }
      
      &.testcases .stat-bg {
        background: radial-gradient(circle, #4facfe 0%, transparent 70%);
      }
      
      &.scripts .stat-bg {
        background: radial-gradient(circle, #43e97b 0%, transparent 70%);
      }
      
      .stat-content {
        display: flex;
        align-items: center;
        position: relative;
        z-index: 1;
        
        .stat-icon {
          width: 56px;
          height: 56px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          
          .el-icon {
            font-size: 28px;
            color: #fff;
          }
        }
      }
      
      &.projects .stat-icon {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }
      
      &.documents .stat-icon {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      }
      
      &.testcases .stat-icon {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      }
      
      &.scripts .stat-icon {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
      }
      
      .stat-info {
        .stat-value {
          font-size: 36px;
          font-weight: 600;
          line-height: 1;
        }
        
        .stat-label {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.6);
          margin-top: 8px;
        }
      }
      
      .stat-trend {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        
        .el-icon {
          font-size: 14px;
        }
      }
    }
  }
  
  .main-content {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
    
    .quick-actions-panel,
    .side-panel {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 16px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 24px;
      
      .panel-header {
        margin-bottom: 20px;
        
        h2 {
          font-size: 16px;
          font-weight: 500;
          margin: 0 0 12px 0;
        }
        
        .panel-line {
          height: 2px;
          background: linear-gradient(90deg, #667eea, transparent);
          border-radius: 1px;
        }
      }
    }
    
    .actions-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      
      .action-card {
        display: flex;
        align-items: center;
        padding: 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(255, 255, 255, 0.08);
          border-color: rgba(255, 255, 255, 0.15);
          transform: translateX(4px);
          
          .action-arrow {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        .action-icon-wrapper {
          width: 48px;
          height: 48px;
          border-radius: 10px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          
          .el-icon {
            font-size: 24px;
            color: #fff;
          }
          
          &.ai {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          }
        }
        
        .action-info {
          flex: 1;
          
          h3 {
            font-size: 15px;
            font-weight: 500;
            margin: 0 0 4px 0;
          }
          
          p {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
            margin: 0;
          }
        }
        
        .action-arrow {
          opacity: 0;
          transform: translateX(-8px);
          transition: all 0.3s ease;
          color: rgba(255, 255, 255, 0.4);
        }
      }
    }
    
    .recent-projects {
      .project-item {
        display: flex;
        align-items: center;
        padding: 14px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(255, 255, 255, 0.08);
          
          .project-arrow {
            opacity: 1;
          }
        }
        
        .project-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: rgba(102, 126, 234, 0.2);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 12px;
          color: #667eea;
        }
        
        .project-info {
          flex: 1;
          
          .project-name {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
          }
          
          .project-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            
            .project-status {
              font-size: 11px;
              padding: 2px 8px;
              border-radius: 4px;
              background: rgba(103, 194, 58, 0.2);
              color: #67c23a;
              
              &.inactive {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.5);
              }
            }
            
            .project-date {
              font-size: 11px;
              color: rgba(255, 255, 255, 0.4);
            }
          }
        }
        
        .project-arrow {
          opacity: 0;
          color: rgba(255, 255, 255, 0.3);
          transition: opacity 0.3s ease;
        }
      }
      
      .empty-state {
        text-align: center;
        padding: 40px 20px;
        color: rgba(255, 255, 255, 0.4);
        
        .el-icon {
          font-size: 48px;
          margin-bottom: 12px;
        }
        
        p {
          font-size: 13px;
        }
      }
    }
  }
}

@media (max-width: 1200px) {
  .dashboard {
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .main-content {
      grid-template-columns: 1fr;
    }
  }
}
</style>
