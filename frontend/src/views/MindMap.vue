<template>
  <div class="mind-map-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>思维导图</span>
            <el-select v-model="selectedProject" placeholder="选择项目" style="margin-left: 16px; width: 200px;" clearable @change="loadMindMap">
              <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </div>
          <div class="header-right">
            <el-button-group>
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
      </template>
      
      <div class="mind-map-container" ref="containerRef">
        <div v-if="!selectedProject" class="empty-state">
          <el-empty description="请选择项目查看思维导图" />
        </div>
        <div v-else-if="mindMapData.length === 0" class="empty-state">
          <el-empty description="暂无思维导图数据，请先生成测试用例" />
        </div>
        <div v-else id="mind-map-canvas" ref="canvasRef" style="width: 100%; height: 600px;"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { ZoomIn, ZoomOut, RefreshRight } from '@element-plus/icons-vue'
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
        fill: '#409EFF',
        stroke: '#409EFF',
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
        stroke: '#A3B1BF'
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
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-left {
      display: flex;
      align-items: center;
    }
  }
  
  .mind-map-container {
    min-height: 600px;
    
    .empty-state {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 600px;
    }
  }
}
</style>
