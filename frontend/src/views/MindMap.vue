<template>
  <div class="mind-map-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">思维导图</h1>
        <p class="page-subtitle">可视化测试用例结构</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedProject" placeholder="选择项目" class="project-select" clearable @change="loadMindMap">
          <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button-group class="zoom-controls">
          <el-button @click="zoomIn">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
          <el-button @click="zoomOut">
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <el-button @click="resetZoom">
            <el-icon><RefreshRight /></el-icon>
          </el-button>
        </el-button-group>
      </div>
    </div>
    
    <div class="content-card">
      <div class="mind-map-container" ref="containerRef">
        <div v-if="!selectedProject" class="empty-state">
          <el-icon><Share /></el-icon>
          <p>请选择项目查看思维导图</p>
        </div>
        <div v-else-if="mindMapData.length === 0" class="empty-state">
          <el-icon><Share /></el-icon>
          <p>暂无思维导图数据，请先生成测试用例</p>
        </div>
        <div v-else id="mind-map-canvas" ref="canvasRef" style="width: 100%; height: 600px;"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { ZoomIn, ZoomOut, RefreshRight, Share } from '@element-plus/icons-vue'
import { projectApi, type Project } from '@/api'
import G6 from '@antv/g6'

const containerRef = ref<HTMLElement>()
const canvasRef = ref<HTMLElement>()
const projects = ref<Project[]>([])
const selectedProject = ref<string>('')
const mindMapData = ref<any[]>([])
const graph = ref<any>(null)

const loadProjects = async () => {
  try {
    projects.value = await projectApi.list()
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

const loadMindMap = async () => {
  if (!selectedProject.value) {
    mindMapData.value = []
    return
  }
  
  mindMapData.value = [
    {
      id: 'root',
      text: '测试用例',
      children: [
        {
          id: 'tc1',
          text: '用户登录测试',
          children: [
            { id: 's1', text: '输入用户名' },
            { id: 's2', text: '输入密码' },
            { id: 's3', text: '点击登录' }
          ]
        },
        {
          id: 'tc2',
          text: 'API性能测试',
          children: [
            { id: 's4', text: '发送请求' },
            { id: 's5', text: '验证响应时间' }
          ]
        }
      ]
    }
  ]
  
  await nextTick()
  renderMindMap()
}

const convertToG6Data = (data: any): any => {
  return {
    id: data.id,
    label: data.text,
    children: data.children?.map((child: any) => convertToG6Data(child)) || []
  }
}

const renderMindMap = () => {
  if (!canvasRef.value || mindMapData.value.length === 0) return
  
  if (graph.value) {
    graph.value.destroy()
  }
  
  const g6Data = convertToG6Data(mindMapData.value[0])
  
  graph.value = new G6.TreeGraph({
    container: 'mind-map-canvas',
    width: canvasRef.value.clientWidth,
    height: 600,
    modes: {
      default: [
        'collapse-expand',
        'drag-canvas',
        'zoom-canvas'
      ]
    },
    defaultNode: {
      size: [120, 30],
      type: 'rect',
      style: {
        fill: '#667eea',
        stroke: '#667eea',
        radius: 4
      },
      labelCfg: {
        style: {
          fill: '#fff',
          fontSize: 12
        }
      }
    },
    defaultEdge: {
      type: 'cubic-horizontal',
      style: {
        stroke: 'rgba(255, 255, 255, 0.3)'
      }
    },
    layout: {
      type: 'compactBox',
      direction: 'LR',
      getId: (d: any) => d.id,
      getHeight: () => 30,
      getWidth: () => 120,
      getVGap: () => 10,
      getHGap: () => 50
    }
  })
  
  graph.value.data(g6Data)
  graph.value.render()
  graph.value.fitView()
}

const zoomIn = () => {
  if (graph.value) {
    const zoom = graph.value.getZoom()
    graph.value.zoomTo(zoom * 1.2)
  }
}

const zoomOut = () => {
  if (graph.value) {
    const zoom = graph.value.getZoom()
    graph.value.zoomTo(zoom / 1.2)
  }
}

const resetZoom = () => {
  if (graph.value) {
    graph.value.fitView()
  }
}

watch(selectedProject, () => {
  loadMindMap()
})

onMounted(() => {
  loadProjects()
})
</script>

<style lang="scss" scoped>
.mind-map-page {
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
      align-items: center;
      
      .project-select {
        width: 200px;
      }
      
      .zoom-controls {
        .el-button {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: rgba(255, 255, 255, 0.8);
          
          &:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
          }
        }
      }
    }
  }
  
  .content-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 20px;
    
    .mind-map-container {
      min-height: 600px;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 8px;
      
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 600px;
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
