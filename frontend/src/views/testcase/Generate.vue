<template>
  <div class="generate-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">AI生成测试用例</h1>
        <p class="page-subtitle">智能化测试用例生成流程</p>
      </div>
    </div>
    
    <div class="steps-container">
      <div 
        v-for="(step, index) in stepLabels" 
        :key="index"
        class="step-item"
        :class="{ 
          'is-active': currentStep === index, 
          'is-finished': currentStep > index,
          'is-clickable': formData.projectId || index === 0
        }"
        @click="goToStep(index)"
      >
        <div class="step-icon">
          <el-icon v-if="currentStep > index"><Check /></el-icon>
          <span v-else>{{ index + 1 }}</span>
        </div>
        <div class="step-title">{{ step }}</div>
        <div class="step-line" v-if="index < stepLabels.length - 1"></div>
      </div>
    </div>
    
    <div class="content-card">
      <div class="step-content">
        <div v-show="currentStep === 0" class="step-panel">
          <el-form :model="formData" label-width="100px">
            <el-form-item label="选择项目">
              <el-select 
                v-model="formData.projectId" 
                placeholder="请选择项目" 
                style="width: 100%;"
                @change="onProjectChange"
              >
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
          
          <div v-if="projectStats && formData.projectId" class="project-stats">
            <el-divider>项目统计信息</el-divider>
            <el-row :gutter="20">
              <el-col :span="6">
                <el-statistic title="已上传文档" :value="projectStats.document_count">
                  <template #suffix>
                    <span style="font-size: 14px;">个</span>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="已解析文档" :value="projectStats.parsed_document_count">
                  <template #suffix>
                    <span style="font-size: 14px;">个</span>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="测试功能点" :value="projectStats.function_point_count">
                  <template #suffix>
                    <span style="font-size: 14px;">个</span>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="测试用例" :value="projectStats.test_case_count">
                  <template #suffix>
                    <span style="font-size: 14px;">个</span>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>
            
            <div v-if="existingFunctionPoints.length > 0" class="existing-fps">
              <el-divider>已有功能点</el-divider>
              <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px;">
                <template #title>
                  <span>该项目已有 <strong>{{ existingFunctionPoints.length }}</strong> 个已保存的功能点</span>
                </template>
              </el-alert>
              <el-table :data="existingFunctionPoints" stripe size="small" max-height="200">
                <el-table-column prop="name" label="功能点名称" min-width="180" />
                <el-table-column prop="test_type" label="测试类型" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getTestTypeColor(row.test_type)" size="small">{{ getTestTypeLabel(row.test_type) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="priority" label="优先级" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getPriorityColor(row.priority)" size="small">{{ row.priority?.toUpperCase() }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'approved' ? 'success' : 'warning'" size="small">
                      {{ row.status === 'approved' ? '已审核' : '待审核' }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
        
        <div v-show="currentStep === 1" class="step-panel">
          <div v-if="existingDocuments.length > 0" class="existing-docs">
            <el-alert type="success" :closable="false" show-icon style="margin-bottom: 16px;">
              <template #title>
                <span>该项目已有 <strong>{{ existingDocuments.length }}</strong> 个文档</span>
              </template>
            </el-alert>
            <el-table :data="existingDocuments" stripe size="small" style="margin-bottom: 20px;">
              <el-table-column prop="name" label="文档名称" min-width="200" show-overflow-tooltip />
              <el-table-column prop="doc_type" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.doc_type || '文档' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'parsed' ? 'success' : (row.status === 'pending' ? 'warning' : 'info')" size="small">
                    {{ row.status === 'parsed' ? '已解析' : (row.status === 'pending' ? '待解析' : '解析失败') }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="file_size" label="大小" width="100">
                <template #default="{ row }">
                  {{ formatFileSize(row.file_size) }}
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="上传时间" width="160">
                <template #default="{ row }">
                  {{ formatDate(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="viewDocument(row)">查看</el-button>
                  <el-button type="warning" link size="small" @click="reparseDocument(row)" :disabled="row.status === 'parsed'">重解析</el-button>
                  <el-button type="danger" link size="small" @click="deleteDocument(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-divider>继续上传新文档</el-divider>
          </div>
          
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
          
          <el-divider>或者</el-divider>
          
          <el-form label-width="100px">
            <el-form-item label="需求描述">
              <el-input
                v-model="formData.userRequirements"
                type="textarea"
                :rows="5"
                placeholder="请输入您的测试需求描述，例如：&#10;- 测试用户登录功能&#10;- 测试API接口响应时间&#10;- 测试数据安全性"
              />
            </el-form-item>
          </el-form>
        </div>
        
        <div v-show="currentStep === 2" class="step-panel">
          <div class="generating" v-if="isGenerating">
            <el-icon class="is-loading" :size="40"><Loading /></el-icon>
            <p>{{ generateStatus }}</p>
            <el-progress :percentage="generateProgress" :stroke-width="8" style="width: 300px; margin-top: 20px;" />
          </div>
          <div v-else>
            <div class="fp-header">
              <span>功能点列表 ({{ allFunctionPoints.length }} 个)</span>
              <div class="fp-actions">
                <el-button type="primary" @click="aiGenerateFunctionPoints" :loading="isAiGenerating">
                  <el-icon><MagicStick /></el-icon>
                  AI辅助生成
                </el-button>
                <el-button @click="showAddFpDialog">
                  <el-icon><Plus /></el-icon>
                  添加功能点
                </el-button>
              </div>
            </div>
            
            <div v-if="allFunctionPoints.length === 0" class="empty-hint">
              <el-empty description="暂无功能点，请点击「AI辅助生成」或「添加功能点」">
                <el-button type="primary" @click="aiGenerateFunctionPoints" :loading="isAiGenerating">
                  <el-icon><MagicStick /></el-icon>
                  AI辅助生成
                </el-button>
              </el-empty>
            </div>
            
            <el-table v-else :data="allFunctionPoints" stripe max-height="450">
              <el-table-column prop="name" label="功能点名称" min-width="200">
                <template #default="{ row }">
                  <el-input v-if="row.editing" v-model="row.name" size="small" />
                  <span v-else>
                    {{ row.name }}
                    <el-tag v-if="row.isExisting" type="info" size="small" style="margin-left: 4px;">已有</el-tag>
                    <el-tag v-else-if="row.isNew" type="success" size="small" style="margin-left: 4px;">新增</el-tag>
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="test_type" label="测试类型" width="120">
                <template #default="{ row }">
                  <el-select v-if="row.editing" v-model="row.test_type" size="small">
                    <el-option label="功能测试" value="functional" />
                    <el-option label="性能测试" value="performance" />
                    <el-option label="安全测试" value="security" />
                    <el-option label="可靠性测试" value="reliability" />
                  </el-select>
                  <el-tag v-else :type="getTestTypeColor(row.test_type)">{{ getTestTypeLabel(row.test_type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="priority" label="优先级" width="100">
                <template #default="{ row }">
                  <el-select v-if="row.editing" v-model="row.priority" size="small">
                    <el-option label="P0" value="p0" />
                    <el-option label="P1" value="p1" />
                    <el-option label="P2" value="p2" />
                    <el-option label="P3" value="p3" />
                    <el-option label="P4" value="p4" />
                  </el-select>
                  <el-tag v-else :type="getPriorityColor(row.priority)">{{ row.priority?.toUpperCase() }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'approved' ? 'success' : (row.status === 'rejected' ? 'danger' : 'warning')" size="small">
                    {{ row.status === 'approved' ? '已审核' : (row.status === 'rejected' ? '已拒绝' : '待审核') }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="module" label="模块" width="100">
                <template #default="{ row }">
                  <el-input v-if="row.editing" v-model="row.module" size="small" />
                  <span v-else>{{ row.module || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="220" fixed="right">
                <template #default="{ row, $index }">
                  <template v-if="row.editing">
                    <el-button type="success" link @click="saveFpEdit(row)">保存</el-button>
                    <el-button link @click="cancelFpEdit(row)">取消</el-button>
                  </template>
                  <template v-else>
                    <el-button v-if="row.isExisting && row.status !== 'approved'" type="success" link @click="approveExistingFp(row)">审核</el-button>
                    <el-button v-if="row.isExisting && row.status !== 'rejected'" type="warning" link @click="rejectExistingFp(row)">拒绝</el-button>
                    <el-button v-if="!row.isExisting" type="primary" link @click="editFp(row)">编辑</el-button>
                    <el-button v-if="!row.isExisting" type="warning" link @click="refineFp(row)">AI优化</el-button>
                    <el-button v-if="!row.isExisting" type="danger" link @click="removeFunctionPoint($index)">删除</el-button>
                  </template>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        
        <div v-show="currentStep === 3" class="step-panel">
          <div class="review-header">
            <el-alert type="info" :closable="false" show-icon>
              <template #title>
                <span>请审核以下 <strong>{{ allFunctionPoints.length }}</strong> 个功能点，已审核通过 <strong>{{ approvedFpCount }}</strong> 个，确认后继续生成测试用例</span>
              </template>
            </el-alert>
          </div>
          
          <div class="batch-actions" style="margin-top: 16px;">
            <el-button type="success" @click="approveAllFps" :disabled="pendingFpCount === 0">
              <el-icon><Check /></el-icon>
              全部通过 ({{ pendingFpCount }} 个待审核)
            </el-button>
            <el-button type="danger" @click="rejectAllFps" :disabled="pendingFpCount === 0">
              <el-icon><Close /></el-icon>
              全部拒绝
            </el-button>
          </div>
          
          <el-table :data="allFunctionPoints" stripe max-height="350" style="margin-top: 16px;">
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="name" label="功能点名称" min-width="180">
              <template #default="{ row }">
                {{ row.name }}
                <el-tag v-if="row.isExisting" type="info" size="small" style="margin-left: 4px;">已有</el-tag>
                <el-tag v-else-if="row.isNew" type="success" size="small" style="margin-left: 4px;">新增</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="test_type" label="测试类型" width="100">
              <template #default="{ row }">
                <el-tag :type="getTestTypeColor(row.test_type)">{{ getTestTypeLabel(row.test_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="80">
              <template #default="{ row }">
                <el-tag :type="getPriorityColor(row.priority)">{{ row.priority?.toUpperCase() }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'approved' ? 'success' : (row.status === 'rejected' ? 'danger' : 'warning')">
                  {{ row.status === 'approved' ? '已审核' : (row.status === 'rejected' ? '已拒绝' : '待审核') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="module" label="模块" width="100" />
            <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button 
                  type="success" 
                  link 
                  @click="reviewFp(row, 'approved')" 
                  :disabled="row.status === 'approved'"
                >
                  通过
                </el-button>
                <el-button 
                  type="danger" 
                  link 
                  @click="reviewFp(row, 'rejected')" 
                  :disabled="row.status === 'rejected'"
                >
                  拒绝
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="review-actions">
            <el-button @click="currentStep = 2">
              <el-icon><Back /></el-icon>
              返回修改
            </el-button>
            <el-button type="primary" @click="confirmFunctionPoints" :disabled="approvedFpCount === 0">
              确认并生成测试用例 ({{ approvedFpCount }} 个)
              <el-icon><Right /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div v-show="currentStep === 4" class="step-panel">
          <div class="generating" v-if="isGenerating">
            <el-icon class="is-loading" :size="40"><Loading /></el-icon>
            <p>{{ generateStatus }}</p>
            <el-progress :percentage="generateProgress" :stroke-width="8" style="width: 300px; margin-top: 20px;" />
          </div>
          <div v-else>
            <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px;">
              <template #title>
                <span>已确认 <strong>{{ savedFpIds.length }}</strong> 个功能点，可用于生成测试用例</span>
              </template>
            </el-alert>
            
            <div class="tc-header">
              <span>测试用例列表 ({{ generatedTestCases.length }} 个)</span>
              <div class="tc-actions">
                <el-button type="primary" @click="aiGenerateTestCases" :loading="isAiGenerating">
                  <el-icon><MagicStick /></el-icon>
                  AI辅助生成
                </el-button>
                <el-button @click="showAddTcDialog">
                  <el-icon><Plus /></el-icon>
                  手动添加
                </el-button>
              </div>
            </div>
            
            <div v-if="generatedTestCases.length === 0" class="empty-hint">
              <el-empty description="暂无测试用例，请点击「AI辅助生成」或「手动添加」">
                <el-button type="primary" @click="aiGenerateTestCases" :loading="isAiGenerating">
                  <el-icon><MagicStick /></el-icon>
                  AI辅助生成
                </el-button>
              </el-empty>
            </div>
            
            <el-table v-else :data="generatedTestCases" stripe max-height="400">
              <el-table-column type="selection" width="50" />
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="title" label="用例标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="test_type" label="测试类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getTestTypeColor(row.test_type)" size="small">{{ getTestTypeLabel(row.test_type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="test_category" label="分类" width="100" show-overflow-tooltip />
              <el-table-column prop="priority" label="优先级" width="80">
                <template #default="{ row }">
                  <el-tag :type="getPriorityColor(row.priority)" size="small">{{ row.priority?.toUpperCase() }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="getTcStatusColor(row.status)" size="small">{{ getTcStatusLabel(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="220" fixed="right">
                <template #default="{ row, $index }">
                  <el-button type="primary" link size="small" @click="viewTestCase(row)">查看</el-button>
                  <el-button type="success" link size="small" @click="approveTc(row)" :disabled="row.status === 'approved'">通过</el-button>
                  <el-button type="warning" link size="small" @click="rejectTc(row)" :disabled="row.status === 'approved' || row.status === 'rejected'">拒绝</el-button>
                  <el-button type="danger" link size="small" @click="removeTestCase($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <div class="final-actions" v-if="generatedTestCases.length > 0">
              <el-button type="success" size="large" @click="approveAllTcs" :disabled="pendingTcCount === 0">
                全部通过 ({{ pendingTcCount }} 个待审核)
              </el-button>
              <el-button type="primary" size="large" @click="saveAllTestCases" :loading="isSaving">
                <el-icon><Check /></el-icon>
                保存审核通过的用例 ({{ approvedTcCount }} 个)
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="step-actions" v-if="currentStep < 4 || (currentStep === 4 && !isGenerating)">
        <el-button v-if="currentStep > 0 && currentStep !== 3" @click="prevStep">上一步</el-button>
        <el-button 
          v-if="currentStep < 2" 
          type="primary" 
          @click="nextStep" 
          :disabled="!canNextStep"
        >
          下一步
        </el-button>
        <el-button 
          v-if="currentStep === 2 && allFunctionPoints.length > 0" 
          type="primary" 
          @click="goToReview"
        >
          下一步：审核确认
        </el-button>
      </div>
    </div>
  </div>
    
    <el-dialog v-model="refineDialogVisible" title="AI优化功能点" width="500px">
      <el-form label-width="80px">
        <el-form-item label="功能点">
          <el-input :model-value="currentRefineFp?.name" disabled />
        </el-form-item>
        <el-form-item label="优化建议">
          <el-input
            v-model="refineFeedback"
            type="textarea"
            :rows="4"
            placeholder="请输入您的优化建议，例如：&#10;- 增加异常场景测试&#10;- 调整优先级为P0&#10;- 补充验收标准"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="refineDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRefine" :loading="refineLoading">优化</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="addFpDialogVisible" title="添加功能点" width="500px">
      <el-form :model="newFpData" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="newFpData.name" placeholder="请输入功能点名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newFpData.description" type="textarea" :rows="2" placeholder="请输入功能点描述" />
        </el-form-item>
        <el-form-item label="测试类型">
          <el-select v-model="newFpData.test_type" style="width: 100%;">
            <el-option label="功能测试" value="functional" />
            <el-option label="性能测试" value="performance" />
            <el-option label="安全测试" value="security" />
            <el-option label="可靠性测试" value="reliability" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="newFpData.priority" style="width: 100%;">
            <el-option label="P0 - 核心" value="p0" />
            <el-option label="P1 - 重要" value="p1" />
            <el-option label="P2 - 一般" value="p2" />
            <el-option label="P3 - 次要" value="p3" />
            <el-option label="P4 - 边缘" value="p4" />
          </el-select>
        </el-form-item>
        <el-form-item label="模块">
          <el-input v-model="newFpData.module" placeholder="请输入所属模块" />
        </el-form-item>
        <el-form-item label="验收标准">
          <el-input v-model="newFpData.acceptance_criteria" type="textarea" :rows="2" placeholder="请输入验收标准" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addFpDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addNewFp">添加</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="addTcDialogVisible" title="添加测试用例" width="600px">
      <el-form :model="newTcData" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="newTcData.title" placeholder="请输入测试用例标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newTcData.description" type="textarea" :rows="2" placeholder="请输入测试用例描述" />
        </el-form-item>
        <el-form-item label="测试类型">
          <el-select v-model="newTcData.test_type" style="width: 100%;">
            <el-option label="功能测试" value="functional" />
            <el-option label="性能测试" value="performance" />
            <el-option label="安全测试" value="security" />
            <el-option label="可靠性测试" value="reliability" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="newTcData.priority" style="width: 100%;">
            <el-option label="P0" value="p0" />
            <el-option label="P1" value="p1" />
            <el-option label="P2" value="p2" />
            <el-option label="P3" value="p3" />
          </el-select>
        </el-form-item>
        <el-form-item label="前置条件">
          <el-input v-model="newTcData.preconditions" type="textarea" :rows="2" placeholder="请输入前置条件" />
        </el-form-item>
        <el-form-item label="预期结果">
          <el-input v-model="newTcData.expected_results" type="textarea" :rows="2" placeholder="请输入预期结果" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addTcDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addNewTc">添加</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="viewTcDialogVisible" :title="currentViewTc?.title" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="测试类型">{{ getTestTypeLabel(currentViewTc?.test_type) }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ currentViewTc?.priority?.toUpperCase() }}</el-descriptions-item>
        <el-descriptions-item label="测试分类">{{ currentViewTc?.test_category }}</el-descriptions-item>
        <el-descriptions-item label="前置条件">{{ currentViewTc?.preconditions || '-' }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentViewTc?.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="预期结果" :span="2">{{ currentViewTc?.expected_results || '-' }}</el-descriptions-item>
      </el-descriptions>
      
      <div class="test-steps" v-if="Array.isArray(currentViewTc?.test_steps) && currentViewTc.test_steps.length > 0">
        <h4>测试步骤</h4>
        <el-table :data="currentViewTc.test_steps" stripe size="small">
          <el-table-column prop="step_num" label="步骤" width="60" />
          <el-table-column prop="action" label="操作" />
          <el-table-column prop="expected_result" label="预期结果" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Loading, Plus, MagicStick, Back, Right, Check, Close } from '@element-plus/icons-vue'
import { projectApi, documentApi, functionPointApi, generatorApi, type Project, type Document, type ProjectStats, type FunctionPoint } from '@/api'
import { useGenerateStore } from '@/stores/generate'

const router = useRouter()
const generateStore = useGenerateStore()

const stepLabels = ['选择项目', '上传文档', '生成功能点', '审核确认', '生成用例']

const currentStep = ref(0)
const isGenerating = ref(false)
const isAiGenerating = ref(false)
const isSaving = ref(false)
const generateStatus = ref('')
const generateProgress = ref(0)
const projects = ref<Project[]>([])
const projectStats = ref<ProjectStats | null>(null)
const fileList = ref<any[]>([])
const existingDocuments = ref<Document[]>([])
const existingFunctionPoints = ref<FunctionPoint[]>([])
const uploadedDocs = ref<Document[]>([])
const generatedFunctionPoints = ref<any[]>([])
const generatedTestCases = ref<any[]>([])
const savedFpIds = ref<string[]>([])

const formData = reactive({
  projectId: '',
  testTypes: ['functional'] as string[],
  userRequirements: ''
})

const refineDialogVisible = ref(false)
const refineFeedback = ref('')
const refineLoading = ref(false)
const currentRefineFp = ref<any>(null)
const currentRefineIndex = ref(-1)

const addFpDialogVisible = ref(false)
const newFpData = reactive({
  name: '',
  description: '',
  test_type: 'functional',
  priority: 'p2',
  module: '',
  acceptance_criteria: ''
})

const addTcDialogVisible = ref(false)
const newTcData = reactive({
  title: '',
  description: '',
  test_type: 'functional',
  priority: 'p2',
  preconditions: '',
  expected_results: ''
})

const viewTcDialogVisible = ref(false)
const currentViewTc = ref<any>(null)

const allFunctionPoints = computed(() => {
  const existing = existingFunctionPoints.value.map(fp => ({
    ...fp,
    isExisting: true,
    isNew: false,
    editing: false
  }))
  const generated = generatedFunctionPoints.value.map(fp => ({
    ...fp,
    isExisting: false,
    isNew: true,
    status: fp.status || 'pending'
  }))
  return [...existing, ...generated]
})

const approvedFpCount = computed(() => {
  return allFunctionPoints.value.filter(fp => fp.status === 'approved').length
})

const pendingFpCount = computed(() => {
  return allFunctionPoints.value.filter(fp => fp.status === 'pending').length
})

const approvedTcCount = computed(() => {
  return generatedTestCases.value.filter(tc => tc.status === 'approved').length
})

const pendingTcCount = computed(() => {
  return generatedTestCases.value.filter(tc => !tc.status || tc.status === 'draft').length
})

const canNextStep = computed(() => {
  switch (currentStep.value) {
    case 0:
      return formData.projectId !== ''
    case 1:
      return fileList.value.length > 0 || formData.userRequirements.trim() !== '' || existingDocuments.value.length > 0
    case 2:
      return allFunctionPoints.value.length > 0
    default:
      return true
  }
})

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

const tcStatusLabels: Record<string, string> = {
  draft: '待审核',
  reviewed: '已审核',
  approved: '已通过',
  rejected: '已拒绝'
}

const tcStatusColors: Record<string, string> = {
  draft: 'warning',
  reviewed: 'info',
  approved: 'success',
  rejected: 'danger'
}

const getTestTypeLabel = (type: string) => testTypeLabels[type] || type
const getTestTypeColor = (type: string) => testTypeColors[type] || 'info'
const getPriorityColor = (priority: string) => priorityColors[priority] || 'info'
const getTcStatusLabel = (status: string) => tcStatusLabels[status] || '待审核'
const getTcStatusColor = (status: string) => tcStatusColors[status] || 'warning'

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadProjects = async () => {
  try {
    projects.value = await projectApi.list()
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

const onProjectChange = async (projectId: string) => {
  if (!projectId) return
  
  existingDocuments.value = []
  existingFunctionPoints.value = []
  generatedFunctionPoints.value = []
  generatedTestCases.value = []
  savedFpIds.value = []
  projectStats.value = null
  
  try {
    await loadExistingDocuments()
    await loadExistingFunctionPoints()
    await loadExistingTestCases()
    const stats = await projectApi.stats(projectId)
    projectStats.value = stats
  } catch (error) {
    console.error('Failed to load project data:', error)
  }
}

const loadExistingDocuments = async () => {
  if (!formData.projectId) return
  
  try {
    const docs = await documentApi.list({ project_id: formData.projectId })
    existingDocuments.value = docs || []
  } catch (error) {
    console.error('Failed to load documents:', error)
  }
}

const loadExistingFunctionPoints = async () => {
  if (!formData.projectId) return
  
  try {
    const fps = await functionPointApi.list({ project_id: formData.projectId })
    existingFunctionPoints.value = fps || []
    generatedFunctionPoints.value = fps || []
  } catch (error) {
    console.error('Failed to load function points:', error)
  }
}

const handleFileChange = (file: any, files: any[]) => {
  fileList.value = files
}

const handleFileRemove = (file: any, files: any[]) => {
  fileList.value = files
}

const formatFileSize = (bytes: number) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const viewDocument = (doc: Document) => {
  ElMessage.info('文档预览功能开发中')
}

const reparseDocument = async (doc: Document) => {
  try {
    await documentApi.parse(doc.id)
    ElMessage.success('文档重新解析成功')
    await loadExistingDocuments()
  } catch (error) {
    console.error('Failed to reparse document:', error)
    ElMessage.error('重新解析失败')
  }
}

const deleteDocument = async (doc: Document) => {
  try {
    await ElMessageBox.confirm(`确定要删除文档「${doc.name}」吗？`, '删除确认', { type: 'warning' })
    await documentApi.delete(doc.id)
    ElMessage.success('删除成功')
    await loadExistingDocuments()
    const stats = await projectApi.stats(formData.projectId)
    projectStats.value = stats
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete document:', error)
    }
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const nextStep = async () => {
  if (currentStep.value === 1) {
    await uploadDocuments()
  } else {
    currentStep.value++
  }
}

const uploadDocuments = async () => {
  if (fileList.value.length === 0) {
    currentStep.value++
    return
  }
  
  isGenerating.value = true
  generateStatus.value = '正在上传文档...'
  generateProgress.value = 0
  
  try {
    const totalFiles = fileList.value.length
    for (let i = 0; i < totalFiles; i++) {
      const file = fileList.value[i]
      generateProgress.value = Math.round((i / totalFiles) * 50)
      generateStatus.value = `正在上传文档 (${i + 1}/${totalFiles}): ${file.name}`
      
      const doc = await documentApi.upload(formData.projectId, file.raw)
      uploadedDocs.value.push(doc)
      
      generateStatus.value = `正在解析文档: ${doc.name}`
      generateProgress.value = Math.round((i / totalFiles) * 50) + 25
      await documentApi.parse(doc.id)
      
      generateProgress.value = Math.round(((i + 1) / totalFiles) * 100)
    }
    
    const docs = await documentApi.list({ project_id: formData.projectId })
    existingDocuments.value = docs.filter((d: Document) => d.status === 'parsed')
    
    const stats = await projectApi.stats(formData.projectId)
    projectStats.value = stats
    
    ElMessage.success('文档上传并解析成功')
    currentStep.value++
  } catch (error) {
    console.error('Failed to upload documents:', error)
    ElMessage.error('文档上传失败')

const goToStep = async (step: number) => {
  if (!formData.projectId && step > 0) {
    ElMessage.warning('请先选择项目')
    return
  }
  currentStep.value = step
  
  if (step === 1) {
    await loadExistingDocuments()
  } else if (step === 2 || step === 3) {
    await loadExistingFunctionPoints()
  } else if (step === 4) {
    await loadExistingTestCases()
  }
}

const loadExistingTestCases = async () => {
  if (!formData.projectId) return
  
  try {
    const tcs = await testCaseApi.list({ project_id: formData.projectId })
    generatedTestCases.value = tcs
  } catch (error) {
    console.error('Failed to load test cases:', error)
  }
}
  } finally {
    isGenerating.value = false
    generateProgress.value = 0
  }
}

const aiGenerateFunctionPoints = async () => {
  if (!formData.userRequirements.trim() && existingDocuments.value.length === 0 && uploadedDocs.value.length === 0) {
    ElMessage.warning('请先上传文档或输入需求描述')
    return
  }
  
  isAiGenerating.value = true
  generateStatus.value = '正在分析需求...'
  generateProgress.value = 10
  
  try {
    const documentIds = [...existingDocuments.value, ...uploadedDocs.value].map(d => d.id)
    
    generateStatus.value = '正在检索文档知识库...'
    generateProgress.value = 30
    
    generateStatus.value = '正在调用AI生成功能点...'
    generateProgress.value = 50
    
    const result = await generatorApi.generateFunctionPoints({
      project_id: formData.projectId,
      document_ids: documentIds,
      test_types: formData.testTypes,
      user_requirements: formData.userRequirements
    })
    
    generateProgress.value = 90
    
    if (!result.success) {
      ElMessage.error(result.message || '功能点生成失败')
      return
    }
    
    const newFps = result.function_points.map((fp: any) => ({
      ...fp,
      project_id: formData.projectId,
      editing: false,
      status: fp.status || 'pending',
      originalData: { ...fp }
    }))
    
    generatedFunctionPoints.value = [...generatedFunctionPoints.value, ...newFps]
    
    generateProgress.value = 100
    ElMessage.success(`成功生成 ${newFps.length} 个功能点`)
    
    await loadExistingFunctionPoints()
  } catch (error) {
    console.error('Failed to generate function points:', error)
    ElMessage.error('功能点生成失败')
  } finally {
    isAiGenerating.value = false
    generateProgress.value = 0
  }
}

const goToReview = () => {
  if (allFunctionPoints.value.length === 0) {
    ElMessage.warning('请先添加功能点')
    return
  }
  currentStep.value = 3
}

const confirmFunctionPoints = async () => {
  const approvedNewFps = generatedFunctionPoints.value.filter(fp => fp.status === 'approved')
  const approvedExistingFps = existingFunctionPoints.value.filter(fp => fp.status === 'approved')
  
  console.log('approvedNewFps:', approvedNewFps)
  console.log('approvedExistingFps:', approvedExistingFps)
  
  if (approvedNewFps.length === 0 && approvedExistingFps.length === 0) {
    ElMessage.warning('请至少审核通过一个功能点')
    return
  }
  
  isGenerating.value = true
  generateStatus.value = '正在处理功能点...'
  generateProgress.value = 20
  
  try {
    savedFpIds.value = []
    
    if (approvedNewFps.length > 0) {
      generateStatus.value = '正在保存新功能点...'
      generateProgress.value = 40
      
      const newFpsToSave = approvedNewFps.map(fp => ({
        project_id: formData.projectId,
        name: fp.name,
        description: fp.description,
        test_type: fp.test_type,
        priority: fp.priority,
        module: fp.module,
        acceptance_criteria: fp.acceptance_criteria
      }))
      
      console.log('newFpsToSave:', newFpsToSave)
      
      const saveResult = await generatorApi.saveFunctionPoints(newFpsToSave)
      
      console.log('saveResult:', saveResult)
      
      if (!saveResult.success) {
        ElMessage.error(saveResult.message || '功能点保存失败')
        return
      }
      
      savedFpIds.value = saveResult.function_points.map((fp: any) => fp.id)
    }
    
    const existingApprovedFpIds = approvedExistingFps.map(fp => fp.id)
    savedFpIds.value = [...savedFpIds.value, ...existingApprovedFpIds]
    
    generateProgress.value = 100
    ElMessage.success(`已确认 ${savedFpIds.value.length} 个功能点`)
    currentStep.value = 4
  } catch (error: any) {
    console.error('Failed to confirm function points:', error)
    const errorMsg = error?.response?.data?.detail || error?.message || '功能点确认失败'
    ElMessage.error(errorMsg)
  } finally {
    isGenerating.value = false
    generateProgress.value = 0
  }
}

const aiGenerateTestCases = async () => {
  console.log('savedFpIds:', savedFpIds.value)
  console.log('existingFunctionPoints:', existingFunctionPoints.value)
  
  let fpIdsToUse = [...savedFpIds.value]
  
  if (fpIdsToUse.length === 0 && existingFunctionPoints.value.length > 0) {
    const approvedFps = existingFunctionPoints.value.filter(fp => fp.status === 'approved' || fp.status === 'pending')
    console.log('approvedFps from existing:', approvedFps)
    if (approvedFps.length > 0) {
      await ElMessageBox.confirm(
        `检测到该项目已有 ${approvedFps.length} 个功能点，是否使用这些功能点生成测试用例？`,
        '使用已有功能点',
        {
          confirmButtonText: '使用已有功能点',
          cancelButtonText: '取消',
          type: 'info'
        }
      )
      fpIdsToUse = approvedFps.map(fp => fp.id)
    }
  }
  
  console.log('fpIdsToUse:', fpIdsToUse)
  
  if (fpIdsToUse.length === 0) {
    ElMessage.warning('请先确认功能点或确保项目已有功能点')
    return
  }
  
  isAiGenerating.value = true
  generateStatus.value = '正在生成测试用例...'
  generateProgress.value = 10
  
  const task = generateStore.startTask('test_cases', formData.projectId)
  generateStore.updateTask(10, '正在初始化...')
  
  try {
    generateProgress.value = 30
    generateStatus.value = `正在为 ${fpIdsToUse.length} 个功能点生成测试用例...`
    generateStore.updateTask(30, `正在为 ${fpIdsToUse.length} 个功能点生成测试用例...`)
    saveCurrentState()
    
    const result = await generatorApi.generateTestCases({
      project_id: formData.projectId,
      function_point_ids: fpIdsToUse
    })
    
    generateProgress.value = 80
    generateStore.updateTask(80, '正在处理生成结果...')
    
    if (!result.success) {
      generateStore.failTask(result.message || '测试用例生成失败')
      ElMessage.error(result.message || '测试用例生成失败')
      return
    }
    
    if (!result.test_cases || result.test_cases.length === 0) {
      generateStore.failTask('AI未能生成测试用例')
      ElMessage.warning('AI未能生成测试用例，请检查功能点内容或稍后重试')
      return
    }
    
    const newTcs = result.test_cases.map((tc: any) => ({
      ...tc,
      project_id: formData.projectId
    }))
    
    generatedTestCases.value = [...generatedTestCases.value, ...newTcs]
    
    generateProgress.value = 100
    generateStore.completeTask(newTcs)
    ElMessage.success(`成功生成 ${newTcs.length} 个测试用例`)
  } catch (error: any) {
    console.error('Failed to generate test cases:', error)
    const errorMsg = error?.response?.data?.detail || error?.message || '测试用例生成失败'
    generateStore.failTask(errorMsg)
    ElMessage.error(errorMsg)
  } finally {
    isAiGenerating.value = false
    generateProgress.value = 0
    saveCurrentState()
  }
}

const saveAllTestCases = async () => {
  const approvedTcs = generatedTestCases.value.filter(tc => tc.status === 'approved')
  
  if (approvedTcs.length === 0) {
    ElMessage.warning('请先审核通过测试用例')
    return
  }
  
  isSaving.value = true
  try {
    const result = await generatorApi.saveTestCases(approvedTcs)
    
    if (!result.success) {
      ElMessage.error(result.message || '测试用例保存失败')
      return
    }
    
    ElMessage.success(`成功保存 ${approvedTcs.length} 个测试用例`)
    
    const stats = await projectApi.stats(formData.projectId)
    projectStats.value = stats
    
    generatedTestCases.value = generatedTestCases.value.filter(tc => tc.status !== 'approved')
    
    ElMessageBox.confirm('测试用例已保存成功，是否前往用例管理页面查看？', '提示', {
      confirmButtonText: '前往查看',
      cancelButtonText: '继续生成',
      type: 'success'
    }).then(() => {
      router.push('/test-cases')
    }).catch(() => {
      resetGenerate()
    })
  } catch (error) {
    console.error('Failed to save test cases:', error)
    ElMessage.error('测试用例保存失败')
  } finally {
    isSaving.value = false
  }
}

const approveTc = (row: any) => {
  row.status = 'approved'
  ElMessage.success('测试用例审核通过')
}

const rejectTc = (row: any) => {
  row.status = 'rejected'
  ElMessage.success('测试用例已拒绝')
}

const approveAllTcs = () => {
  for (const tc of generatedTestCases.value) {
    if (!tc.status || tc.status === 'draft') {
      tc.status = 'approved'
    }
  }
  ElMessage.success('已全部审核通过')
}

const editFp = (row: any) => {
  row.editing = true
  row.originalData = { ...row }
}

const approveExistingFp = async (row: any) => {
  try {
    await functionPointApi.approve(row.id)
    row.status = 'approved'
    ElMessage.success('功能点审核通过')
    const stats = await projectApi.stats(formData.projectId)
    projectStats.value = stats
  } catch (error) {
    console.error('Failed to approve:', error)
    ElMessage.error('审核失败')
  }
}

const rejectExistingFp = async (row: any) => {
  try {
    await functionPointApi.reject(row.id)
    row.status = 'rejected'
    ElMessage.success('功能点已拒绝')
    const stats = await projectApi.stats(formData.projectId)
    projectStats.value = stats
  } catch (error) {
    console.error('Failed to reject:', error)
    ElMessage.error('操作失败')
  }
}

const reviewFp = async (row: any, status: string) => {
  if (row.isExisting) {
    if (status === 'approved') {
      await approveExistingFp(row)
    } else {
      await rejectExistingFp(row)
    }
  } else {
    const index = generatedFunctionPoints.value.findIndex(fp => 
      fp.name === row.name && fp.test_type === row.test_type
    )
    if (index !== -1) {
      generatedFunctionPoints.value[index].status = status
      row.status = status
      ElMessage.success(status === 'approved' ? '功能点审核通过' : '功能点已拒绝')
    }
  }
}

const approveAllFps = async () => {
  for (const fp of allFunctionPoints.value) {
    if (fp.status === 'pending') {
      if (fp.isExisting) {
        try {
          await functionPointApi.approve(fp.id)
          fp.status = 'approved'
        } catch (error) {
          console.error('Failed to approve:', error)
        }
      } else {
        const index = generatedFunctionPoints.value.findIndex(gfp => 
          gfp.name === fp.name && gfp.test_type === fp.test_type
        )
        if (index !== -1) {
          generatedFunctionPoints.value[index].status = 'approved'
        }
      }
    }
  }
  const stats = await projectApi.stats(formData.projectId)
  projectStats.value = stats
  ElMessage.success('已全部审核通过')
}

const rejectAllFps = async () => {
  for (const fp of allFunctionPoints.value) {
    if (fp.status === 'pending') {
      if (fp.isExisting) {
        try {
          await functionPointApi.reject(fp.id)
          fp.status = 'rejected'
        } catch (error) {
          console.error('Failed to reject:', error)
        }
      } else {
        const index = generatedFunctionPoints.value.findIndex(gfp => 
          gfp.name === fp.name && gfp.test_type === fp.test_type
        )
        if (index !== -1) {
          generatedFunctionPoints.value[index].status = 'rejected'
        }
      }
    }
  }
  const stats = await projectApi.stats(formData.projectId)
  projectStats.value = stats
  ElMessage.success('已全部拒绝')
}

const saveFpEdit = (row: any) => {
  row.editing = false
  delete row.originalData
}

const cancelFpEdit = (row: any) => {
  Object.assign(row, row.originalData)
  row.editing = false
}

const removeFunctionPoint = (index: number) => {
  generatedFunctionPoints.value.splice(index, 1)
}

const refineFp = (row: any) => {
  currentRefineFp.value = row
  currentRefineIndex.value = generatedFunctionPoints.value.indexOf(row)
  refineFeedback.value = ''
  refineDialogVisible.value = true
}

const submitRefine = async () => {
  if (!refineFeedback.value.trim()) {
    ElMessage.warning('请输入优化建议')
    return
  }
  
  refineLoading.value = true
  try {
    const result = await generatorApi.refineFunctionPoint({
      function_point: currentRefineFp.value,
      user_feedback: refineFeedback.value,
      project_id: formData.projectId
    })
    
    if (!result.success) {
      ElMessage.error(result.message || '优化失败')
      return
    }
    
    Object.assign(generatedFunctionPoints.value[currentRefineIndex.value], result.function_point)
    refineDialogVisible.value = false
    ElMessage.success('功能点优化成功')
  } catch (error) {
    console.error('Failed to refine:', error)
    ElMessage.error('优化失败')
  } finally {
    refineLoading.value = false
  }
}

const showAddFpDialog = () => {
  newFpData.name = ''
  newFpData.description = ''
  newFpData.test_type = 'functional'
  newFpData.priority = 'p2'
  newFpData.module = ''
  newFpData.acceptance_criteria = ''
  addFpDialogVisible.value = true
}

const addNewFp = () => {
  if (!newFpData.name.trim()) {
    ElMessage.warning('请输入功能点名称')
    return
  }
  
  generatedFunctionPoints.value.push({
    ...newFpData,
    project_id: formData.projectId,
    editing: false
  })
  
  addFpDialogVisible.value = false
  ElMessage.success('功能点添加成功')
}

const showAddTcDialog = () => {
  newTcData.title = ''
  newTcData.description = ''
  newTcData.test_type = 'functional'
  newTcData.priority = 'p2'
  newTcData.preconditions = ''
  newTcData.expected_results = ''
  addTcDialogVisible.value = true
}

const addNewTc = () => {
  if (!newTcData.title.trim()) {
    ElMessage.warning('请输入测试用例标题')
    return
  }
  
  generatedTestCases.value.push({
    ...newTcData,
    project_id: formData.projectId,
    test_steps: [],
    test_category: 'functional'
  })
  
  addTcDialogVisible.value = false
  ElMessage.success('测试用例添加成功')
}

const viewTestCase = (row: any) => {
  currentViewTc.value = row
  viewTcDialogVisible.value = true
}

const removeTestCase = (index: number) => {
  generatedTestCases.value.splice(index, 1)
}

const resetGenerate = () => {
  currentStep.value = 0
  formData.projectId = ''
  formData.testTypes = ['functional']
  formData.userRequirements = ''
  fileList.value = []
  existingDocuments.value = []
  existingFunctionPoints.value = []
  uploadedDocs.value = []
  generatedFunctionPoints.value = []
  generatedTestCases.value = []
  savedFpIds.value = []
  projectStats.value = null
  generateStore.clearState()
}

const saveCurrentState = () => {
  generateStore.saveState({
    projectId: formData.projectId,
    currentStep: currentStep.value,
    testTypes: formData.testTypes,
    userRequirements: formData.userRequirements,
    existingDocuments: existingDocuments.value,
    existingFunctionPoints: existingFunctionPoints.value,
    generatedFunctionPoints: generatedFunctionPoints.value,
    generatedTestCases: generatedTestCases.value,
    savedFpIds: savedFpIds.value,
    uploadedDocs: uploadedDocs.value,
    fileList: fileList.value
  })
}

const restoreState = async () => {
  const savedState = generateStore.loadState()
  
  if (savedState.projectId) {
    formData.projectId = savedState.projectId
    formData.testTypes = savedState.testTypes || ['functional']
    formData.userRequirements = savedState.userRequirements || ''
    currentStep.value = savedState.currentStep || 0
    
    if (savedState.projectId) {
      try {
        projectStats.value = await projectApi.stats(savedState.projectId)
        await loadExistingDocuments()
        await loadExistingFunctionPoints()
        await loadExistingTestCases()
      } catch (error) {
        console.error('Failed to restore state:', error)
      }
    }
  }
  
  if (generateStore.currentTask && generateStore.currentTask.status === 'running') {
    isAiGenerating.value = true
    generateStatus.value = generateStore.currentTask.message
    generateProgress.value = generateStore.currentTask.progress
    
    if (generateStore.currentTask.type === 'test_cases') {
      pollTaskStatus()
    }
  }
}

const pollTaskStatus = () => {
  const checkStatus = () => {
    if (!generateStore.currentTask || generateStore.currentTask.status !== 'running') {
      isAiGenerating.value = false
      return
    }
    
    generateStatus.value = generateStore.currentTask.message
    generateProgress.value = generateStore.currentTask.progress
    
    if (generateStore.currentTask.status === 'running') {
      setTimeout(checkStatus, 1000)
    } else if (generateStore.currentTask.status === 'completed') {
      isAiGenerating.value = false
      if (generateStore.currentTask.result) {
        generatedTestCases.value = generateStore.currentTask.result
        ElMessage.success('测试用例生成完成')
      }
    } else if (generateStore.currentTask.status === 'failed') {
      isAiGenerating.value = false
      ElMessage.error(generateStore.currentTask.error || '生成失败')
    }
  }
  
  checkStatus()
}

onMounted(async () => {
  await loadProjects()
  
  const urlParams = new URLSearchParams(window.location.search)
  const projectId = urlParams.get('project_id')
  const reset = urlParams.get('reset')
  
  if (reset === 'true' || projectId) {
    resetGenerate()
    
    if (projectId) {
      formData.projectId = projectId
      currentStep.value = 1
      await loadProjectStats(projectId)
      await loadExistingDocuments(projectId)
      await loadExistingFunctionPoints(projectId)
    }
  } else {
    restoreState()
  }
})

onUnmounted(() => {
  saveCurrentState()
})

watch([currentStep, formData, generatedFunctionPoints, generatedTestCases, savedFpIds], () => {
  saveCurrentState()
}, { deep: true })
</script>

<style lang="scss" scoped>
.generate-page {
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
  }
  
  .steps-container {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    
    .step-item {
      display: flex;
      align-items: center;
      position: relative;
      padding: 0 20px;
      
      &.is-clickable {
        cursor: pointer;
        
        &:hover {
          .step-icon {
            transform: scale(1.1);
            box-shadow: 0 4px 15px rgba(255, 255, 255, 0.3);
          }
          
          .step-title {
            color: #fff;
          }
        }
      }
      
      .step-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        color: rgba(255, 255, 255, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        border: 2px solid rgba(255, 255, 255, 0.3);
      }
      
      .step-title {
        margin-left: 12px;
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.8);
        white-space: nowrap;
        transition: all 0.3s ease;
      }
      
      .step-line {
        width: 60px;
        height: 2px;
        background: rgba(255, 255, 255, 0.3);
        margin: 0 15px;
      }
      
      &.is-active {
        .step-icon {
          background: #fff;
          color: #667eea;
          border-color: #fff;
          box-shadow: 0 4px 15px rgba(255, 255, 255, 0.4);
        }
        
        .step-title {
          color: #fff;
          font-weight: 600;
        }
      }
      
      &.is-finished {
        .step-icon {
          background: rgba(255, 255, 255, 0.9);
          color: #67c23a;
          border-color: #67c23a;
        }
        
        .step-title {
          color: #fff;
        }
        
        .step-line {
          background: rgba(255, 255, 255, 0.6);
        }
      }
    }
  }
  
  .content-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 24px;
  }
  
  .step-content {
    min-height: 450px;
    
    .step-panel {
      padding: 20px;
    }
    
    .upload-area {
      width: 100%;
      
      :deep(.el-upload-dragger) {
        width: 100%;
        background: rgba(255, 255, 255, 0.03);
        border: 1px dashed rgba(255, 255, 255, 0.2);
        
        &:hover {
          border-color: #667eea;
        }
        
        .el-icon--upload {
          color: rgba(255, 255, 255, 0.5);
        }
        
        .el-upload__text {
          color: rgba(255, 255, 255, 0.7);
          
          em {
            color: #667eea;
          }
        }
      }
      
      :deep(.el-upload__tip) {
        color: rgba(255, 255, 255, 0.4);
      }
    }
    
    .existing-docs {
      margin-bottom: 20px;
    }
    
    .existing-fps-section {
      margin-bottom: 20px;
      padding: 16px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 8px;
    }
    
    .project-stats {
      margin-top: 20px;
      padding: 20px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 8px;
      
      :deep(.el-divider__text) {
        background: transparent;
        color: rgba(255, 255, 255, 0.6);
      }
      
      :deep(.el-statistic) {
        .el-statistic__head {
          color: rgba(255, 255, 255, 0.6);
        }
        
        .el-statistic__content {
          color: #fff;
        }
      }
      
      .existing-fps {
        margin-top: 16px;
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
        color: rgba(255, 255, 255, 0.6);
      }
    }
    
    .fp-header, .tc-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      span {
        font-weight: 500;
        font-size: 16px;
        color: #fff;
      }
      
      .fp-actions, .tc-actions {
        display: flex;
        gap: 10px;
        
        .el-button--primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          
          &:hover {
            opacity: 0.9;
          }
        }
      }
    }
    
    .empty-hint {
      padding: 40px 0;
      
      :deep(.el-empty__description) {
        color: rgba(255, 255, 255, 0.5);
      }
    }
    
    .review-header {
      margin-bottom: 10px;
    }
    
    .review-actions {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-top: 30px;
      
      .el-button--primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
      }
    }
    
    .final-actions {
      display: flex;
      justify-content: center;
      margin-top: 30px;
      gap: 16px;
      
      .el-button--primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
      }
    }
    
    .test-steps {
      margin-top: 20px;
      
      h4 {
        margin-bottom: 10px;
        color: #fff;
      }
    }
    
    .batch-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .step-actions {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-top: 30px;
    
    .el-button--primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border: none;
    }
  }
  
  :deep(.el-form-item__label) {
    color: rgba(255, 255, 255, 0.8);
  }
  
  :deep(.el-input__wrapper),
  :deep(.el-textarea__inner),
  :deep(.el-select .el-input__wrapper) {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: none;
    
    &:hover, &:focus {
      border-color: rgba(102, 126, 234, 0.5);
    }
    
    input, textarea {
      color: #fff;
      
      &::placeholder {
        color: rgba(255, 255, 255, 0.3);
      }
    }
  }
  
  :deep(.el-select-dropdown) {
    background: #1a1a2e;
    border: 1px solid rgba(255, 255, 255, 0.1);
    
    .el-select-dropdown__item {
      color: rgba(255, 255, 255, 0.8);
      
      &:hover, &.hover {
        background: rgba(255, 255, 255, 0.05);
      }
      
      &.selected {
        color: #667eea;
      }
    }
  }
  
  :deep(.el-checkbox) {
    color: rgba(255, 255, 255, 0.8);
    
    .el-checkbox__inner {
      background: rgba(255, 255, 255, 0.05);
      border-color: rgba(255, 255, 255, 0.2);
    }
    
    &.is-checked .el-checkbox__inner {
      background: #667eea;
      border-color: #667eea;
    }
  }
  
  :deep(.el-table) {
    background: transparent;
    
    &::before {
      display: none;
    }
    
    th.el-table__cell {
      background: rgba(255, 255, 255, 0.05);
      color: rgba(255, 255, 255, 0.8);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    td.el-table__cell {
      background: transparent;
      color: rgba(255, 255, 255, 0.8);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    tr:hover td.el-table__cell {
      background: rgba(255, 255, 255, 0.03);
    }
    
    .el-table__empty-text {
      color: rgba(255, 255, 255, 0.4);
    }
  }
  
  :deep(.el-alert) {
    background: rgba(102, 126, 234, 0.1);
    border: 1px solid rgba(102, 126, 234, 0.3);
    
    .el-alert__title {
      color: rgba(255, 255, 255, 0.9);
    }
    
    .el-alert__icon {
      color: #667eea;
    }
    
    &.el-alert--success {
      background: rgba(103, 194, 58, 0.1);
      border-color: rgba(103, 194, 58, 0.3);
      
      .el-alert__icon {
        color: #67c23a;
      }
    }
  }
  
  :deep(.el-divider__text) {
    background: transparent;
    color: rgba(255, 255, 255, 0.5);
  }
  
  :deep(.el-dialog) {
    background: #1a1a2e;
    border: 1px solid rgba(255, 255, 255, 0.1);
    
    .el-dialog__title {
      color: #fff;
    }
    
    .el-dialog__header {
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .el-dialog__body {
      color: rgba(255, 255, 255, 0.8);
    }
  }
  
  :deep(.el-descriptions) {
    .el-descriptions__label {
      color: rgba(255, 255, 255, 0.6);
    }
    
    .el-descriptions__content {
      color: rgba(255, 255, 255, 0.9);
    }
    
    .el-descriptions__cell {
      border-color: rgba(255, 255, 255, 0.1);
    }
  }
}
</style>
