import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface GenerateTask {
  id: string
  type: 'function_points' | 'test_cases'
  status: 'running' | 'completed' | 'failed'
  progress: number
  message: string
  projectId: string
  startTime: number
  result?: any
  error?: string
}

export const useGenerateStore = defineStore('generate', () => {
  const currentTask = ref<GenerateTask | null>(null)
  const taskHistory = ref<GenerateTask[]>([])

  const savedState = ref({
    projectId: '',
    currentStep: 0,
    testTypes: ['functional'] as string[],
    userRequirements: '',
    existingDocuments: [] as any[],
    existingFunctionPoints: [] as any[],
    generatedFunctionPoints: [] as any[],
    generatedTestCases: [] as any[],
    savedFpIds: [] as string[],
    uploadedDocs: [] as any[],
    fileList: [] as any[]
  })

  const startTask = (type: 'function_points' | 'test_cases', projectId: string) => {
    const task: GenerateTask = {
      id: `${type}_${Date.now()}`,
      type,
      status: 'running',
      progress: 0,
      message: '正在初始化...',
      projectId,
      startTime: Date.now()
    }
    currentTask.value = task
    saveToLocalStorage()
    return task
  }

  const updateTask = (progress: number, message: string) => {
    if (currentTask.value) {
      currentTask.value.progress = progress
      currentTask.value.message = message
      saveToLocalStorage()
    }
  }

  const completeTask = (result?: any) => {
    if (currentTask.value) {
      currentTask.value.status = 'completed'
      currentTask.value.progress = 100
      currentTask.value.result = result
      taskHistory.value.unshift(currentTask.value)
      saveToLocalStorage()
    }
  }

  const failTask = (error: string) => {
    if (currentTask.value) {
      currentTask.value.status = 'failed'
      currentTask.value.error = error
      taskHistory.value.unshift(currentTask.value)
      saveToLocalStorage()
    }
  }

  const clearTask = () => {
    if (currentTask.value && currentTask.value.status === 'running') {
      return false
    }
    currentTask.value = null
    saveToLocalStorage()
    return true
  }

  const saveState = (state: Partial<typeof savedState.value>) => {
    savedState.value = { ...savedState.value, ...state }
    saveToLocalStorage()
  }

  const loadState = () => {
    try {
      const stored = localStorage.getItem('generate_state')
      if (stored) {
        const parsed = JSON.parse(stored)
        savedState.value = { ...savedState.value, ...parsed.savedState }
        if (parsed.currentTask && parsed.currentTask.status === 'running') {
          currentTask.value = parsed.currentTask
        }
      }
    } catch (e) {
      console.error('Failed to load state:', e)
    }
    return savedState.value
  }

  const saveToLocalStorage = () => {
    try {
      localStorage.setItem('generate_state', JSON.stringify({
        currentTask: currentTask.value,
        savedState: savedState.value,
        taskHistory: taskHistory.value.slice(0, 10)
      }))
    } catch (e) {
      console.error('Failed to save state:', e)
    }
  }

  const clearState = () => {
    savedState.value = {
      projectId: '',
      currentStep: 0,
      testTypes: ['functional'],
      userRequirements: '',
      existingDocuments: [],
      existingFunctionPoints: [],
      generatedFunctionPoints: [],
      generatedTestCases: [],
      savedFpIds: [],
      uploadedDocs: [],
      fileList: []
    }
    currentTask.value = null
    localStorage.removeItem('generate_state')
  }

  return {
    currentTask,
    taskHistory,
    savedState,
    startTask,
    updateTask,
    completeTask,
    failTask,
    clearTask,
    saveState,
    loadState,
    clearState
  }
})
