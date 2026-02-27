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
          </div>
        </div>
        
        <div v-show="currentStep === 1" class="step-panel">
          <div v-if="existingDocuments.length > 0" class="existing-docs">
            <el-alert type="success" :closable="false" show-icon style="margin-bottom: 16px;">
              <template #title>
                <span>该项目已有 <strong>{{ existingDocuments.length }}</strong> 个文档</span>
              </template>
            </el-alert>
            <div class="document-list">
              <div v-for="doc in existingDocuments" :key="doc.id" class="document-item">
                <div class="doc-icon">
                  <el-icon><DocumentIcon /></el-icon>
                </div>
                <div class="doc-info">
                  <div class="doc-name">{{ doc.name }}</div>
                  <div class="doc-meta">
                    <span class="meta-tag">{{ getDocTypeLabel(doc.doc_type) }}</span>
                    <span class="meta-size">{{ formatFileSize(doc.file_size) }}</span>
                    <span class="meta-date">{{ formatDate(doc.created_at) }}</span>
                  </div>
                </div>
                <div class="doc-status" :class="doc.status">
                  {{ getDocStatusLabel(doc.status) }}
                </div>
                <div class="doc-actions">
                  <el-button type="primary" text size="small" @click="viewDocument(doc)">
                    <el-icon><View /></el-icon>
                    查看
                  </el-button>
                  <el-button type="warning" text size="small" @click="reparseDocument(doc)" :disabled="doc.status === 'parsed'">
                    <el-icon><Refresh /></el-icon>
                    重解析
                  </el-button>
                  <el-button type="danger" text size="small" @click="deleteDocument(doc)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
              </div>
            </div>
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
          
          <el-form label-width="auto">
            <el-form-item>
              <template #label>
                <span class="form-label">需求描述</span>
              </template>
              <el-input
                v-model="formData.userRequirements"
                type="textarea"
                :rows="5"
                placeholder="请输入您的测试需求描述，例如：&#10;- 测试用户登录功能&#10;- 测试API接口响应时间&#10;- 测试数据安全性"
                class="full-width-textarea"
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
            
            <div v-else class="function-point-list">
              <div 
                v-for="(fp, index) in allFunctionPoints" 
                :key="index"
                class="function-point-item"
                :class="{ 'editing': fp.editing }"
              >
                <div class="fp-icon" :class="fp.test_type">
                  <el-icon v-if="fp.test_type === 'functional'"><DocumentIcon /></el-icon>
                  <el-icon v-else-if="fp.test_type === 'performance'"><Timer /></el-icon>
                  <el-icon v-else-if="fp.test_type === 'security'"><Lock /></el-icon>
                  <el-icon v-else><SetUp /></el-icon>
                </div>
                <div class="fp-info">
                  <div class="fp-name">
                    <el-input v-if="fp.editing" v-model="fp.name" size="small" />
                    <span v-else>
                      {{ fp.name }}
                      <el-tag v-if="fp.isExisting" type="info" size="small" style="margin-left: 8px;">已有</el-tag>
                      <el-tag v-else-if="fp.isNew" type="success" size="small" style="margin-left: 8px;">新增</el-tag>
                    </span>
                  </div>
                  <div class="fp-meta">
                    <span class="meta-tag">{{ getTestTypeLabel(fp.test_type) }}</span>
                    <span class="meta-priority">{{ fp.priority?.toUpperCase() }}</span>
                    <span class="meta-module">{{ fp.module || '-' }}</span>
                  </div>
                </div>
                <div class="fp-status" :class="fp.status">
                  {{ fp.status === 'approved' ? '已审核' : (fp.status === 'rejected' ? '已拒绝' : '待审核') }}
                </div>
                <div class="fp-actions">
                  <template v-if="fp.editing">
                    <el-button type="success" text size="small" @click="saveFpEdit(fp)">
                      <el-icon><Check /></el-icon>
                      保存
                    </el-button>
                    <el-button text size="small" @click="cancelFpEdit(fp)">
                      <el-icon><Close /></el-icon>
                      取消
                    </el-button>
                  </template>
                  <template v-else>
                    <el-button type="primary" text size="small" @click="viewFunctionPoint(fp)">
                      <el-icon><View /></el-icon>
                      查看
                    </el-button>
                    <el-button type="primary" text size="small" @click="editFp(fp)">
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-button>
                    <el-button v-if="!fp.isExisting" type="warning" text size="small" @click="refineFp(fp)">
                      <el-icon><MagicStick /></el-icon>
                      AI优化
                    </el-button>
                    <el-button type="success" text size="small" @click="approveFp(fp)" :disabled="fp.status === 'approved'">
                      <el-icon><Check /></el-icon>
                      通过
                    </el-button>
                    <el-button type="warning" text size="small" @click="rejectFp(fp)" :disabled="fp.status === 'rejected'">
                      <el-icon><Close /></el-icon>
                      拒绝
                    </el-button>
                    <el-button type="danger" text size="small" @click="deleteFunctionPoint(fp)">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </template>
                </div>
              </div>
            </div>
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
          
          <div v-if="allFunctionPoints.length > 0" class="function-point-list" style="margin-top: 16px;">
            <div 
              v-for="(fp, index) in allFunctionPoints" 
              :key="index"
              class="function-point-item"
            >
              <div class="fp-icon" :class="fp.test_type">
                <el-icon v-if="fp.test_type === 'functional'"><DocumentIcon /></el-icon>
                <el-icon v-else-if="fp.test_type === 'performance'"><Timer /></el-icon>
                <el-icon v-else-if="fp.test_type === 'security'"><Lock /></el-icon>
                <el-icon v-else><SetUp /></el-icon>
              </div>
              <div class="fp-info">
                <div class="fp-name">
                  {{ fp.name }}
                  <el-tag v-if="fp.isExisting" type="info" size="small" style="margin-left: 8px;">已有</el-tag>
                  <el-tag v-else-if="fp.isNew" type="success" size="small" style="margin-left: 8px;">新增</el-tag>
                </div>
                <div class="fp-meta">
                  <span class="meta-tag">{{ getTestTypeLabel(fp.test_type) }}</span>
                  <span class="meta-priority">{{ fp.priority?.toUpperCase() }}</span>
                  <span class="meta-module">{{ fp.module || '-' }}</span>
                </div>
              </div>
              <div class="fp-status" :class="fp.status">
                {{ fp.status === 'approved' ? '已审核' : (fp.status === 'rejected' ? '已拒绝' : '待审核') }}
              </div>
              <div class="fp-actions">
                <el-button 
                  type="success" 
                  text 
                  size="small"
                  @click="reviewFp(fp, 'approved')" 
                  :disabled="fp.status === 'approved'"
                >
                  <el-icon><Check /></el-icon>
                  通过
                </el-button>
                <el-button 
                  type="danger" 
                  text 
                  size="small"
                  @click="reviewFp(fp, 'rejected')" 
                  :disabled="fp.status === 'rejected'"
                >
                  <el-icon><Close /></el-icon>
                  拒绝
                </el-button>
              </div>
            </div>
          </div>
          
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
          <!-- 优化后的生成加载动画 -->
          <div class="generating-container" v-if="isGenerating">
            <div class="pulse-loader">
              <div class="pulse-circle"></div>
              <div class="pulse-circle"></div>
              <div class="pulse-circle"></div>
              <div class="loader-icon">
                <el-icon><MagicStick /></el-icon>
              </div>
            </div>
            <div class="progress-info">
              <div class="progress-percentage">{{ generateProgress }}%</div>
              <div class="progress-status">{{ generateStatus }}</div>
              <div class="progress-bar-wrapper">
                <div class="progress-bar-fill" :style="{ width: generateProgress + '%' }"></div>
              </div>
            </div>
            <div class="generation-details">
              <span class="detail-text">{{ generateDetailText }}</span>
            </div>
          </div>
          
          <div v-else class="generated-content">
            <!-- 顶部信息提示 -->
            <div class="info-alert">
              <div class="alert-icon">
                <el-icon><InfoFilled /></el-icon>
              </div>
              <div class="alert-content">
                已确认 <strong>{{ savedFpIds.length || existingFunctionPoints.length }}</strong> 个功能点，可用于生成测试用例
              </div>
            </div>
            
            <!-- 操作按钮区 -->
            <div class="action-bar">
              <div class="action-left">
                <span class="list-title">测试用例列表</span>
                <span class="list-count">{{ generatedTestCases.length }} 个</span>
              </div>
              <div class="action-right">
                <el-button type="primary" class="ai-btn" @click="aiGenerateTestCases" :loading="isAiGenerating">
                  <el-icon><MagicStick /></el-icon>
                  AI智能生成
                </el-button>
                <el-button @click="showAddTcDialog">
                  <el-icon><Plus /></el-icon>
                  手动添加
                </el-button>
              </div>
            </div>
            
            <!-- 优化后的空状态 -->
            <div v-if="generatedTestCases.length === 0" class="empty-state">
              <div class="empty-icon">
                <el-icon><DocumentAdd /></el-icon>
              </div>
              <p class="empty-title">暂无测试用例</p>
              <p class="empty-desc">点击下方按钮，AI将根据功能点自动生成测试用例</p>
              <el-button type="primary" size="large" class="empty-btn" @click="aiGenerateTestCases" :loading="isAiGenerating">
                <el-icon><MagicStick /></el-icon>
                AI智能生成
              </el-button>
            </div>
            
            <!-- 优化后的卡片式用例列表 -->
            <div class="testcase-list" v-else>
              <div 
                v-for="(tc, index) in generatedTestCases" 
                :key="index"
                class="testcase-item"
              >
                <div class="testcase-icon" :class="tc.test_type">
                  <el-icon v-if="tc.test_type === 'functional'"><DocumentIcon /></el-icon>
                  <el-icon v-else-if="tc.test_type === 'performance'"><Timer /></el-icon>
                  <el-icon v-else-if="tc.test_type === 'security'"><Lock /></el-icon>
                  <el-icon v-else><SetUp /></el-icon>
                </div>
                <div class="testcase-info">
                  <div class="testcase-title">{{ tc.title }}</div>
                  <div class="testcase-meta">
                    <span class="meta-tag">{{ getTestTypeLabel(tc.test_type) }}</span>
                    <span class="meta-priority">{{ tc.priority?.toUpperCase() }}</span>
                  </div>
                </div>
                <div class="testcase-status" :class="tc.status || 'draft'">
                  {{ getTcStatusLabel(tc.status) }}
                </div>
                <div class="testcase-actions">
                  <el-button type="primary" text size="small" @click="viewTestCase(tc)">
                    <el-icon><View /></el-icon>
                    查看
                  </el-button>
                  <el-button type="success" text size="small" @click="approveTc(tc)" :disabled="tc.status === 'approved'">
                    <el-icon><Check /></el-icon>
                    通过
                  </el-button>
                  <el-button type="warning" text size="small" @click="rejectTc(tc)" :disabled="tc.status === 'approved' || tc.status === 'rejected'">
                    <el-icon><Close /></el-icon>
                    拒绝
                  </el-button>
                  <el-button type="danger" text size="small" @click="removeTestCase(index)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
              </div>
            </div>
            
            <!-- 优化后的底部审核区 -->
            <div class="final-review-section" v-if="generatedTestCases.length > 0">
              <div class="review-summary">
                <div class="summary-title">审核统计</div>
                <div class="summary-stats">
                  <div class="stat-item">
                    <span class="stat-icon total">
                      <el-icon><DocumentIcon /></el-icon>
                    </span>
                    <span>总计 <span class="stat-number">{{ generatedTestCases.length }}</span> 个</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-icon approved">
                      <el-icon><Check /></el-icon>
                    </span>
                    <span>已通过 <span class="stat-number">{{ approvedTcCount }}</span> 个</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-icon pending">
                      <el-icon><Clock /></el-icon>
                    </span>
                    <span>待审核 <span class="stat-number">{{ pendingTcCount }}</span> 个</span>
                  </div>
                </div>
              </div>
              <div class="review-actions">
                <el-button type="success" size="large" @click="approveAllTcs" :disabled="pendingTcCount === 0">
                  <el-icon><Check /></el-icon>
                  全部通过
                </el-button>
                <el-button type="primary" size="large" @click="saveAllTestCases" :loading="isSaving" :disabled="approvedTcCount === 0">
                  <el-icon><FolderChecked /></el-icon>
                  保存已通过 ({{ approvedTcCount }})
                </el-button>
              </div>
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
    
    <el-dialog v-model="viewFpDialogVisible" title="查看功能点" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="功能点名称">
          {{ currentViewFp?.name }}
        </el-descriptions-item>
        <el-descriptions-item label="测试类型">
          <el-tag :type="getTestTypeColor(currentViewFp?.test_type)">
            {{ getTestTypeLabel(currentViewFp?.test_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="优先级">
          <el-tag :type="getPriorityColor(currentViewFp?.priority)">
            {{ currentViewFp?.priority?.toUpperCase() }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentViewFp?.status === 'approved' ? 'success' : (currentViewFp?.status === 'rejected' ? 'danger' : 'warning')">
            {{ currentViewFp?.status === 'approved' ? '已审核' : (currentViewFp?.status === 'rejected' ? '已拒绝' : '待审核') }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="模块" :span="2">
          {{ currentViewFp?.module || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ currentViewFp?.description || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="来源" :span="2">
          <el-tag v-if="currentViewFp?.isExisting" type="info">已有</el-tag>
          <el-tag v-else type="success">新增</el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="viewFpDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
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
    
    <el-dialog v-model="viewTcDialogVisible" :title="currentViewTc?.title" width="720px" class="tc-detail-dialog">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="测试类型">{{ getTestTypeLabel(currentViewTc?.test_type) }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ currentViewTc?.priority?.toUpperCase() }}</el-descriptions-item>
        <el-descriptions-item label="测试分类">{{ currentViewTc?.test_category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <span class="status-text" :class="currentViewTc?.status || 'draft'">
            {{ getTcStatusLabel(currentViewTc?.status) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="前置条件" :span="2">{{ currentViewTc?.preconditions || '-' }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentViewTc?.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="预期结果" :span="2">{{ currentViewTc?.expected_results || '-' }}</el-descriptions-item>
      </el-descriptions>
      
      <div class="test-steps" v-if="Array.isArray(currentViewTc?.test_steps) && currentViewTc.test_steps.length > 0">
        <h4>测试步骤</h4>
        <div class="steps-list">
          <div v-for="(step, idx) in currentViewTc.test_steps" :key="idx" class="step-item">
            <div class="step-number">{{ step.step_num || idx + 1 }}</div>
            <div class="step-content">
              <div class="step-action">{{ step.action }}</div>
              <div class="step-expected" v-if="step.expected_result">
                <span class="expected-label">预期:</span> {{ step.expected_result }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="no-steps" v-else>
        <el-icon><List /></el-icon>
        <span>暂无测试步骤</span>
      </div>
      
      <template #footer>
        <div class="dialog-footer-actions">
          <el-button @click="viewTcDialogVisible = false">关闭</el-button>
          <el-button type="success" @click="approveCurrentTc" :disabled="currentViewTc?.status === 'approved'">
            <el-icon><Check /></el-icon>
            通过审核
          </el-button>
          <el-button type="danger" @click="rejectCurrentTc" :disabled="currentViewTc?.status === 'approved' || currentViewTc?.status === 'rejected'">
            <el-icon><Close /></el-icon>
            拒绝
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Loading, Plus, MagicStick, Back, Right, Check, Close, Document as DocumentIcon, Timer, Lock, SetUp, View, Delete, Clock, FolderChecked, DocumentAdd, InfoFilled, List, Refresh, Edit } from '@element-plus/icons-vue'
import { projectApi, documentApi, functionPointApi, generatorApi, testCaseApi, type Project, type Document, type ProjectStats, type FunctionPoint } from '@/api'
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

const viewFpDialogVisible = ref(false)
const currentViewFp = ref<any>(null)

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
  
  const all = [...existing, ...generated]
  const uniqueFps = []
  const seenNames = new Set()
  
  for (const fp of all) {
    const normalizedName = fp.name.trim().toLowerCase()
    if (!seenNames.has(normalizedName)) {
      seenNames.add(normalizedName)
      uniqueFps.push(fp)
    }
  }
  
  return uniqueFps
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

const docTypeLabels: Record<string, string> = {
  requirement: '需求文档',
  spec: '规格说明书',
  design: '设计文档',
  api: '接口说明',
  manual: '用户手册',
  image: '图片'
}

const docStatusLabels: Record<string, string> = {
  pending: '待解析',
  processing: '解析中',
  parsed: '已解析',
  failed: '解析失败'
}

const getTestTypeLabel = (type: string) => testTypeLabels[type] || type
const getTestTypeColor = (type: string) => testTypeColors[type] || 'info'
const getPriorityColor = (priority: string) => priorityColors[priority] || 'info'
const getTcStatusLabel = (status: string) => tcStatusLabels[status] || '待审核'
const getTcStatusColor = (status: string) => tcStatusColors[status] || 'warning'
const getDocTypeLabel = (type: string) => docTypeLabels[type] || type || '文档'
const getDocStatusLabel = (status: string) => docStatusLabels[status] || status

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
    generatedFunctionPoints.value = []
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
  } finally {
    isGenerating.value = false
    generateProgress.value = 0
  }
}

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

const editFp = (fp: any) => {
  if (fp.isExisting) {
    const index = existingFunctionPoints.value.findIndex(efp => efp.id === fp.id)
    if (index !== -1) {
      existingFunctionPoints.value[index].editing = true
      existingFunctionPoints.value[index].originalData = { ...existingFunctionPoints.value[index] }
    }
  } else {
    const index = generatedFunctionPoints.value.findIndex(gfp => gfp === fp)
    if (index !== -1) {
      generatedFunctionPoints.value[index].editing = true
      generatedFunctionPoints.value[index].originalData = { ...generatedFunctionPoints.value[index] }
    }
  }
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

const approveFp = async (fp: any) => {
  if (fp.isExisting) {
    await approveExistingFp(fp)
  } else {
    fp.status = 'approved'
    ElMessage.success('功能点审核通过')
  }
}

const rejectFp = async (fp: any) => {
  if (fp.isExisting) {
    await rejectExistingFp(fp)
  } else {
    fp.status = 'rejected'
    ElMessage.success('功能点已拒绝')
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

const saveFpEdit = (fp: any) => {
  if (fp.isExisting) {
    const index = existingFunctionPoints.value.findIndex(efp => efp.id === fp.id)
    if (index !== -1) {
      existingFunctionPoints.value[index].editing = false
      delete existingFunctionPoints.value[index].originalData
    }
  } else {
    const index = generatedFunctionPoints.value.findIndex(gfp => gfp === fp)
    if (index !== -1) {
      generatedFunctionPoints.value[index].editing = false
      delete generatedFunctionPoints.value[index].originalData
    }
  }
}

const cancelFpEdit = (fp: any) => {
  if (fp.isExisting) {
    const index = existingFunctionPoints.value.findIndex(efp => efp.id === fp.id)
    if (index !== -1) {
      Object.assign(existingFunctionPoints.value[index], existingFunctionPoints.value[index].originalData)
      existingFunctionPoints.value[index].editing = false
      delete existingFunctionPoints.value[index].originalData
    }
  } else {
    const index = generatedFunctionPoints.value.findIndex(gfp => gfp === fp)
    if (index !== -1) {
      Object.assign(generatedFunctionPoints.value[index], generatedFunctionPoints.value[index].originalData)
      generatedFunctionPoints.value[index].editing = false
      delete generatedFunctionPoints.value[index].originalData
    }
  }
}

const removeFunctionPoint = (fp: any) => {
  ElMessageBox.confirm(
    `确定要删除功能点「${fp.name}」吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    if (fp.isExisting) {
      const index = existingFunctionPoints.value.findIndex(efp => efp.id === fp.id)
      if (index !== -1) {
        existingFunctionPoints.value.splice(index, 1)
      }
    } else {
      const index = generatedFunctionPoints.value.findIndex(gfp => gfp === fp)
      if (index !== -1) {
        generatedFunctionPoints.value.splice(index, 1)
      }
    }
    ElMessage.success('功能点删除成功')
  }).catch(() => {})
}

const viewFunctionPoint = (fp: any) => {
  currentViewFp.value = fp
  viewFpDialogVisible.value = true
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

// 详情弹窗内审核
const approveCurrentTc = () => {
  if (currentViewTc.value) {
    currentViewTc.value.status = 'approved'
    ElMessage.success('测试用例审核通过')
  }
}

const rejectCurrentTc = () => {
  if (currentViewTc.value) {
    currentViewTc.value.status = 'rejected'
    ElMessage.success('测试用例已拒绝')
  }
}

// 生成详情文本
const generateDetailText = computed(() => {
  if (isAiGenerating.value) {
    const fpCount = savedFpIds.value.length || existingFunctionPoints.value.length
    return `正在为 ${fpCount} 个功能点生成测试用例...`
  }
  return ''
})

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
      try {
        projectStats.value = await projectApi.stats(projectId)
        await loadExistingDocuments()
        await loadExistingFunctionPoints()
      } catch (error) {
        console.error('Failed to load project data:', error)
      }
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
  background: linear-gradient(135deg, #0f1624 0%, #1e293b 100%);
  background-image: 
    radial-gradient(circle at 10% 20%, rgba(102, 126, 234, 0.1) 0%, transparent 20%),
    radial-gradient(circle at 90% 80%, rgba(79, 172, 254, 0.1) 0%, transparent 20%);
  padding: 24px;
  color: #fff;
  font-family: 'Inter', 'PingFang SC', sans-serif;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding: 20px 24px;
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    border: 1px solid rgba(102, 126, 234, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    
    .header-content {
      .page-title {
        font-size: 22px;
        font-weight: 600;
        margin: 0 0 6px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
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
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    border: 1px solid rgba(102, 126, 234, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    
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
    backdrop-filter: blur(10px);
    border-radius: 16px;
    border: 1px solid rgba(102, 126, 234, 0.2);
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }
  
  .step-content {
    min-height: 450px;
    
    .step-panel {
      padding: 20px;
      
      .form-label {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 8px;
        display: block;
      }
      
      :deep(.full-width-textarea) {
        width: 100%;
        
        .el-textarea__inner {
          width: 100%;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #fff;
          
          &::placeholder {
            color: rgba(255, 255, 255, 0.3);
          }
          
          &:focus {
            border-color: rgba(102, 126, 234, 0.5);
          }
        }
      }
      
      :deep(.el-form-item) {
        margin-bottom: 24px;
        
        .el-form-item__label {
          display: none;
        }
      }
    }
    
    .upload-area {
      width: 100%;
      
      :deep(.el-upload-dragger) {
        width: 100%;
        background: rgba(255, 255, 255, 0.03);
        border: 1px dashed rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        padding: 40px 20px;
        
        &:hover {
          border-color: #667eea;
          background: rgba(255, 255, 255, 0.06);
        }
        
        .el-icon--upload {
          color: rgba(255, 255, 255, 0.5);
          font-size: 48px;
        }
        
        .el-upload__text {
          color: rgba(255, 255, 255, 0.7);
          font-size: 14px;
          margin-top: 16px;
          
          em {
            color: #667eea;
            font-style: normal;
          }
        }
      }
      
      :deep(.el-upload__tip) {
        color: rgba(255, 255, 255, 0.4);
        font-size: 12px;
        margin-top: 12px;
      }
    }
    
    .existing-docs {
      margin-bottom: 20px;
      
      .document-list {
        .document-item {
          display: flex;
          align-items: center;
          padding: 16px 20px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 10px;
          margin-bottom: 12px;
          transition: all 0.3s ease;
          
          &:hover {
            background: rgba(255, 255, 255, 0.06);
            
            .doc-actions {
              opacity: 1;
            }
          }
          
          .doc-icon {
            width: 44px;
            height: 44px;
            border-radius: 10px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 16px;
            
            .el-icon {
              font-size: 22px;
              color: #fff;
            }
          }
          
          .doc-info {
            flex: 1;
            
            .doc-name {
              font-size: 15px;
              font-weight: 500;
              margin-bottom: 6px;
            }
            
            .doc-meta {
              display: flex;
              align-items: center;
              gap: 12px;
              font-size: 12px;
              color: rgba(255, 255, 255, 0.5);
              
              .meta-tag {
                padding: 2px 8px;
                background: rgba(102, 126, 234, 0.2);
                color: #667eea;
                border-radius: 4px;
              }
            }
          }
          
          .doc-status {
            font-size: 12px;
            padding: 4px 12px;
            border-radius: 4px;
            margin-right: 16px;
            
            &.pending {
              background: rgba(255, 255, 255, 0.1);
              color: rgba(255, 255, 255, 0.6);
            }
            
            &.processing {
              background: rgba(230, 162, 60, 0.2);
              color: #e6a23c;
            }
            
            &.parsed {
              background: rgba(103, 194, 58, 0.2);
              color: #67c23a;
            }
            
            &.failed {
              background: rgba(245, 108, 108, 0.2);
              color: #f56c6c;
            }
          }
          
          .doc-actions {
            display: flex;
            gap: 4px;
            opacity: 0.6;
            transition: opacity 0.3s ease;
          }
        }
      }
    }
    
    .existing-fps-section {
      margin-bottom: 20px;
      padding: 16px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 8px;
    }
    
    .function-point-list {
      .function-point-item {
        display: flex;
        align-items: center;
        padding: 16px 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(255, 255, 255, 0.06);
          
          .fp-actions {
            opacity: 1;
          }
        }
        
        &.editing {
          background: rgba(102, 126, 234, 0.08);
          border: 1px solid rgba(102, 126, 234, 0.3);
        }
        
        .fp-icon {
          width: 44px;
          height: 44px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          
          &.functional {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          &.performance {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          }
          &.security {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          }
          &.reliability {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
          }
          
          .el-icon {
            font-size: 22px;
            color: #fff;
          }
        }
        
        .fp-info {
          flex: 1;
          
          .fp-name {
            font-size: 15px;
            font-weight: 500;
            margin-bottom: 6px;
            
            :deep(.el-input) {
              width: 200px;
            }
          }
          
          .fp-meta {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
            
            .meta-tag {
              padding: 2px 8px;
              background: rgba(102, 126, 234, 0.2);
              color: #667eea;
              border-radius: 4px;
            }
            
            .meta-priority {
              color: rgba(255, 255, 255, 0.6);
            }
            
            .meta-module {
              color: rgba(255, 255, 255, 0.5);
            }
          }
        }
        
        .fp-status {
          font-size: 12px;
          padding: 4px 12px;
          border-radius: 4px;
          margin-right: 16px;
          
          &.pending {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.6);
          }
          
          &.approved {
            background: rgba(103, 194, 58, 0.2);
            color: #67c23a;
          }
          
          &.rejected {
            background: rgba(245, 108, 108, 0.2);
            color: #f56c6c;
          }
        }
        
        .fp-actions {
          display: flex;
          gap: 4px;
          opacity: 0.6;
          transition: opacity 0.3s ease;
        }
      }
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
    
    // ===== 优化后的生成加载动画 =====
    .generating-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 400px;
      padding: 40px;
      
      .pulse-loader {
        position: relative;
        width: 160px;
        height: 160px;
        margin-bottom: 40px;
        
        .pulse-circle {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          border-radius: 50%;
          border: 2px solid;
          animation: pulse-wave 2.4s ease-out infinite;
          
          &:nth-child(1) {
            width: 160px;
            height: 160px;
            border-color: rgba(102, 126, 234, 0.3);
            animation-delay: 0s;
          }
          
          &:nth-child(2) {
            width: 120px;
            height: 120px;
            border-color: rgba(118, 75, 162, 0.4);
            animation-delay: 0.5s;
          }
          
          &:nth-child(3) {
            width: 80px;
            height: 80px;
            border-color: rgba(102, 126, 234, 0.5);
            animation-delay: 1s;
          }
        }
        
        .loader-icon {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 50px;
          height: 50px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          font-size: 26px;
          box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
        }
      }
      
      @keyframes pulse-wave {
        0% {
          transform: translate(-50%, -50%) scale(0.8);
          opacity: 0;
        }
        40% {
          opacity: 1;
        }
        100% {
          transform: translate(-50%, -50%) scale(1.3);
          opacity: 0;
        }
      }
      
      .progress-info {
        text-align: center;
        width: 380px;
        
        .progress-percentage {
          font-size: 52px;
          font-weight: 700;
          background: linear-gradient(135deg, #fff 0%, #a8b2d1 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          line-height: 1;
          margin-bottom: 14px;
          font-family: 'Courier New', Consolas, monospace;
        }
        
        .progress-status {
          font-size: 15px;
          color: rgba(255, 255, 255, 0.6);
          margin-bottom: 22px;
        }
        
        .progress-bar-wrapper {
          width: 100%;
          height: 6px;
          background: rgba(255, 255, 255, 0.08);
          border-radius: 3px;
          overflow: hidden;
          
          .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 3px;
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 16px rgba(102, 126, 234, 0.5);
          }
        }
      }
      
      .generation-details {
        margin-top: 24px;
        padding: 12px 24px;
        background: rgba(255, 255, 255, 0.04);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        
        .detail-text {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.45);
        }
      }
    }
    
    // ===== 生成完成后的内容区 =====
    .generated-content {
      .info-alert {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 20px;
        background: rgba(102, 126, 234, 0.08);
        border-radius: 10px;
        border: 1px solid rgba(102, 126, 234, 0.15);
        margin-bottom: 20px;
        
        .alert-icon {
          color: #667eea;
          font-size: 18px;
          flex-shrink: 0;
        }
        
        .alert-content {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.7);
          
          strong {
            color: #a5b4fc;
          }
        }
      }
      
      .action-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        
        .action-left {
          display: flex;
          align-items: baseline;
          gap: 8px;
          
          .list-title {
            font-size: 16px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.95);
          }
          
          .list-count {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.4);
            padding: 2px 8px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 10px;
          }
        }
        
        .action-right {
          display: flex;
          gap: 10px;
          
          .ai-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            
            &:hover {
              opacity: 0.9;
            }
          }
        }
      }
    }
    
    // ===== 优化后的空状态 =====
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 60px 20px;
      
      .empty-icon {
        width: 80px;
        height: 80px;
        border-radius: 20px;
        background: rgba(102, 126, 234, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
        
        .el-icon {
          font-size: 36px;
          color: #667eea;
        }
      }
      
      .empty-title {
        font-size: 16px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        margin: 0 0 8px 0;
      }
      
      .empty-desc {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.35);
        margin: 0 0 24px 0;
      }
      
      .empty-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        height: 44px;
        padding: 0 28px;
        font-size: 15px;
        border-radius: 10px;
        
        &:hover {
          opacity: 0.9;
          transform: translateY(-1px);
        }
      }
    }
    
    // ===== 卡片式用例列表 =====
    .testcase-list {
      .testcase-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        margin-bottom: 8px;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(255, 255, 255, 0.06);
          
          .testcase-actions {
            opacity: 1;
          }
        }
        
        .testcase-icon {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 12px;
          
          &.functional {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          &.performance {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          }
          &.security {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          }
          &.reliability {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
          }
          
          .el-icon {
            font-size: 18px;
            color: #fff;
          }
        }
        
        .testcase-info {
          flex: 1;
          
          .testcase-title {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
          }
          
          .testcase-meta {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 11px;
            color: rgba(255, 255, 255, 0.5);
            
            .meta-tag {
              padding: 2px 6px;
              background: rgba(102, 126, 234, 0.2);
              color: #667eea;
              border-radius: 3px;
            }
            
            .meta-priority {
              color: rgba(255, 255, 255, 0.6);
            }
          }
        }
        
        .testcase-status {
          font-size: 11px;
          padding: 3px 10px;
          border-radius: 3px;
          margin-right: 12px;
          
          &.draft {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.6);
          }
          
          &.approved {
            background: rgba(103, 194, 58, 0.2);
            color: #67c23a;
          }
          
          &.rejected {
            background: rgba(245, 108, 108, 0.2);
            color: #f56c6c;
          }
        }
        
        .testcase-actions {
          display: flex;
          gap: 3px;
          opacity: 0.6;
          transition: opacity 0.3s ease;
        }
      }
    }
    
    // ===== 底部审核区 =====
    .final-review-section {
      margin-top: 28px;
      padding: 24px;
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.06) 100%);
      border-radius: 14px;
      border: 1px solid rgba(102, 126, 234, 0.12);
      
      .review-summary {
        text-align: center;
        margin-bottom: 20px;
        
        .summary-title {
          font-size: 15px;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.85);
          margin-bottom: 14px;
        }
        
        .summary-stats {
          display: flex;
          justify-content: center;
          gap: 28px;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.6);
          
          .stat-item {
            display: flex;
            align-items: center;
            gap: 8px;
            
            .stat-icon {
              width: 22px;
              height: 22px;
              border-radius: 6px;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 12px;
              
              &.total {
                background: rgba(102, 126, 234, 0.2);
                color: #667eea;
              }
              &.approved {
                background: rgba(103, 194, 58, 0.2);
                color: #67c23a;
              }
              &.pending {
                background: rgba(230, 162, 60, 0.2);
                color: #e6a23c;
              }
            }
            
            .stat-number {
              font-weight: 700;
              color: #fff;
            }
          }
        }
      }
      
      .review-actions {
        display: flex;
        justify-content: center;
        gap: 14px;
        
        .el-button {
          height: 44px;
          padding: 0 28px;
          font-size: 14px;
          font-weight: 500;
          border-radius: 10px;
          transition: all 0.25s;
        }
        
        :deep(.el-button--success) {
          background: linear-gradient(135deg, #67c23a 0%, #43e97b 100%);
          border: none;
          
          &:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(103, 194, 58, 0.3);
          }
        }
        
        :deep(.el-button--primary) {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          
          &:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
          }
        }
      }
    }
    
    .fp-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      span {
        font-weight: 500;
        font-size: 16px;
        color: #fff;
      }
      
      .fp-actions {
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
    
    // ===== 详情弹窗测试步骤 =====
    .test-steps {
      margin-top: 24px;
      
      h4 {
        margin-bottom: 12px;
        color: rgba(255, 255, 255, 0.85);
        font-size: 14px;
        font-weight: 600;
      }
      
      .steps-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        
        .step-item {
          display: flex;
          gap: 14px;
          padding: 12px 16px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.05);
          
          .step-number {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
            flex-shrink: 0;
          }
          
          .step-content {
            flex: 1;
            
            .step-action {
              font-size: 13px;
              color: rgba(255, 255, 255, 0.85);
              line-height: 1.5;
            }
            
            .step-expected {
              margin-top: 6px;
              font-size: 12px;
              color: rgba(255, 255, 255, 0.45);
              
              .expected-label {
                color: rgba(103, 194, 58, 0.8);
                font-weight: 500;
              }
            }
          }
        }
      }
    }
    
    .no-steps {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 24px;
      color: rgba(255, 255, 255, 0.3);
      font-size: 13px;
      margin-top: 16px;
    }
    
    .dialog-footer-actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      
      :deep(.el-button--success) {
        background: linear-gradient(135deg, #67c23a 0%, #43e97b 100%);
        border: none;
      }
      
      :deep(.el-button--danger) {
        background: rgba(245, 108, 108, 0.15);
        border: 1px solid rgba(245, 108, 108, 0.3);
        color: #fca5a5;
        
        &:hover:not(:disabled) {
          background: rgba(245, 108, 108, 0.25);
        }
      }
    }
    
    .status-text {
      font-weight: 500;
      
      &.draft { color: #d1d5db; }
      &.approved { color: #86efac; }
      &.rejected { color: #fca5a5; }
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
      color: rgba(255, 255, 255, 0.9);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      font-weight: 600;
    }
    
    td.el-table__cell {
      background: transparent;
      color: rgba(255, 255, 255, 0.9);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    tr:hover td.el-table__cell {
      background: rgba(255, 255, 255, 0.03);
    }
    
    .el-table__empty-text {
      color: rgba(255, 255, 255, 0.4);
    }
    
    .cell {
      color: #fff;
      
      span {
        color: #fff;
      }
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
  
  :deep(.el-divider) {
    margin: 24px 0 16px 0;
    border: none;
    
    .el-divider__text {
      background-color: transparent;
      color: rgba(255, 255, 255, 0.85);
      padding: 0;
      padding-bottom: 12px;
      font-weight: 600;
      font-size: 14px;
      display: block;
      position: relative;
      
      &::after {
        content: '';
        position: absolute;
        left: 0;
        bottom: 0;
        width: 100%;
        height: 1px;
        background: linear-gradient(90deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%);
      }
    }
    
    &.is-center .el-divider__text {
      text-align: center;
      
      &::after {
        left: 50%;
        transform: translateX(-50%);
        width: 200px;
      }
    }
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
  
  @keyframes shine {
    0% {
      transform: translateX(-100%) translateY(-100%) rotate(30deg);
    }
    100% {
      transform: translateX(100%) translateY(100%) rotate(30deg);
    }
  }
}
</style>
