import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json'
  }
})

apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export const api = {
  get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.get(url, config)
  },
  
  post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.post(url, data, config)
  },
  
  put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.put(url, data, config)
  },
  
  patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.patch(url, data, config)
  },
  
  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.delete(url, config)
  }
}

export interface Project {
  id: string
  name: string
  description: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface ProjectStats {
  project_id: string
  project_name: string
  document_count: number
  parsed_document_count: number
  function_point_count: number
  test_case_count: number
}

export interface Document {
  id: string
  project_id: string
  name: string
  doc_type: string
  file_path: string
  file_size: number
  status: string
  created_at: string
  updated_at: string
}

export interface FunctionPoint {
  id: string
  project_id: string
  document_id: string | null
  name: string
  description: string | null
  test_type: string
  priority: string
  module: string | null
  acceptance_criteria: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface TestStep {
  step_num: number
  action: string
  expected_result: string
  test_data?: Record<string, unknown>
}

export interface TestCase {
  id: string
  project_id: string
  function_point_id: string | null
  title: string
  description: string | null
  test_type: string
  test_category: string
  priority: string
  preconditions: string | null
  test_steps: TestStep[]
  expected_results: string | null
  test_data: Record<string, unknown> | null
  tags: string[]
  status: string
  version: number
  created_at: string
  updated_at: string
}

export interface TestScript {
  id: string
  project_id: string
  test_case_id: string | null
  name: string
  language: string
  framework: string
  content: string
  file_path: string | null
  dependencies: string[]
  status: string
  version: number
  created_at: string
  updated_at: string
}

export const projectApi = {
  list: (params?: { skip?: number; limit?: number }) => 
    api.get<Project[]>('/projects', { params }),
  get: (id: string) => api.get<Project>(`/projects/${id}`),
  stats: (id: string) => api.get<ProjectStats>(`/projects/${id}/stats`),
  create: (data: Partial<Project>) => api.post<Project>('/projects', data),
  update: (id: string, data: Partial<Project>) => api.patch<Project>(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`)
}

export const documentApi = {
  list: (params?: { project_id?: string; skip?: number; limit?: number }) => 
    api.get<Document[]>('/documents', { params }),
  get: (id: string) => api.get<Document>(`/documents/${id}`),
  upload: (projectId: string, file: File, docType?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (docType) {
      formData.append('doc_type', docType)
    }
    return api.post<Document>(`/documents/upload/${projectId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  delete: (id: string) => api.delete(`/documents/${id}`),
  parse: (id: string) => api.post(`/documents/${id}/parse`),
  parseStatus: (id: string) => api.get(`/documents/${id}/parse-status`)
}

export const functionPointApi = {
  list: (params?: { project_id?: string; skip?: number; limit?: number }) => 
    api.get<FunctionPoint[]>('/function-points', { params }),
  get: (id: string) => api.get<FunctionPoint>(`/function-points/${id}`),
  create: (data: Partial<FunctionPoint>) => api.post<FunctionPoint>('/function-points', data),
  createBatch: (data: Partial<FunctionPoint>[]) => api.post<FunctionPoint[]>('/function-points/batch', data),
  update: (id: string, data: Partial<FunctionPoint>) => api.patch<FunctionPoint>(`/function-points/${id}`, data),
  approve: (id: string) => api.post<FunctionPoint>(`/function-points/${id}/approve`),
  reject: (id: string) => api.post<FunctionPoint>(`/function-points/${id}/reject`),
  delete: (id: string) => api.delete(`/function-points/${id}`)
}

export const testCaseApi = {
  list: (params?: { project_id?: string; skip?: number; limit?: number }) => 
    api.get<TestCase[]>('/test-cases', { params }),
  get: (id: string) => api.get<TestCase>(`/test-cases/${id}`),
  create: (data: Partial<TestCase>) => api.post<TestCase>('/test-cases', data),
  createBatch: (data: Partial<TestCase>[]) => api.post<TestCase[]>('/test-cases/batch', data),
  update: (id: string, data: Partial<TestCase>) => api.patch<TestCase>(`/test-cases/${id}`, data),
  approve: (id: string) => api.post<TestCase>(`/test-cases/${id}/approve`),
  reject: (id: string) => api.post<TestCase>(`/test-cases/${id}/reject`),
  delete: (id: string) => api.delete(`/test-cases/${id}`)
}

export const testScriptApi = {
  list: (params?: { project_id?: string; skip?: number; limit?: number }) => 
    api.get<TestScript[]>('/test-scripts', { params }),
  get: (id: string) => api.get<TestScript>(`/test-scripts/${id}`),
  create: (data: Partial<TestScript>) => api.post<TestScript>('/test-scripts', data),
  createBatch: (data: Partial<TestScript>[]) => api.post<TestScript[]>('/test-scripts/batch', data),
  update: (id: string, data: Partial<TestScript>) => api.patch<TestScript>(`/test-scripts/${id}`, data),
  delete: (id: string) => api.delete(`/test-scripts/${id}`),
  download: (id: string) => api.get(`/test-scripts/${id}/download`, { responseType: 'blob' })
}

export const generatorApi = {
  understandRequirements: (userInput: string) => 
    api.post<{ success: boolean; analysis: any }>('/generator/understand-requirements', { user_input: userInput }),
  
  generateFunctionPoints: (data: {
    project_id: string
    document_ids?: string[]
    test_types: string[]
    user_requirements?: string
  }) => api.post<{ success: boolean; message: string; function_points: any[]; requirements_analysis?: any }>('/generator/function-points', data),
  
  saveFunctionPoints: (data: Partial<FunctionPoint>[]) => 
    api.post<{ success: boolean; message: string; function_points: FunctionPoint[] }>('/generator/function-points/save', data),
  
  refineFunctionPoint: (data: {
    function_point: any
    user_feedback: string
    project_id?: string
  }) => api.post<{ success: boolean; message: string; function_point: any }>('/generator/function-points/refine', data),
  
  generateTestCases: (data: {
    project_id: string
    function_point_ids: string[]
  }) => api.post<{ success: boolean; message: string; test_cases: any[] }>('/generator/test-cases', data),
  
  saveTestCases: (data: any[]) => 
    api.post<{ success: boolean; message: string; test_cases: TestCase[] }>('/generator/test-cases/save', data),
  
  generateScripts: (data: {
    project_id: string
    test_case_ids: string[]
    language: string
    framework: string
  }) => api.post<{ success: boolean; message: string; scripts: any[] }>('/generator/scripts', data),
  
  saveScripts: (data: any[]) => 
    api.post<{ success: boolean; message: string; scripts: TestScript[] }>('/generator/scripts/save', data),
  
  getVectorStats: (projectId: string) => 
    api.get<{ exists: boolean; count: number }>(`/generator/vector-stats/${projectId}`)
}
