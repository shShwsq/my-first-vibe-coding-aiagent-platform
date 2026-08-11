<template>
  <div class="workflow-editor-page">
    <header class="editor-header">
      <div class="header-left">
        <div class="logo">
          <svg viewBox="0 0 24 24" class="logo-icon">
            <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
          </svg>
          <span class="logo-text">shwsq's aiagent</span>
        </div>
        <button class="btn-back" @click="handleBack">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
          </svg>
          <span>返回</span>
        </button>
      </div>
      <div class="header-center">
        <h1 class="page-title">{{ agentName || '工作流编辑器' }}</h1>
        <span class="save-status" :class="{ saved: isSaved }">
          {{ isSaved ? '已保存' : '未保存' }}
        </span>
      </div>
      <div class="header-right">
        <button class="btn-restore" @click="restoreCode" :disabled="isSaved" title="恢复上次保存的代码">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M12.5,8C9.85,8 7.45,9 5.6,10.6L2,7V16H11L7.38,12.38C8.77,11.22 10.54,10.5 12.5,10.5C16.04,10.5 19.05,12.81 20.1,16L22.47,15.22C21.08,11.03 17.15,8 12.5,8Z"/>
          </svg>
          <span>恢复</span>
        </button>
        <button class="btn-smart-check" @click="checkWorkflowCode" :disabled="checkingCode">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z"/>
          </svg>
          {{ checkingCode ? '检查中...' : '智能检查' }}
        </button>
        <button class="btn-stop" v-if="checkingCode" @click="stopCheckWorkflowCode">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M6,6H18V18H6V6Z"/>
          </svg>
          暂停
        </button>
        <button class="btn-smart-generate" @click="showGenerateDialog" :disabled="generatingCode">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M12,3 L13.5,10.5 L21,12 L13.5,13.5 L12,21 L10.5,13.5 L3,12 L10.5,10.5 Z M19.5,3.5 L20.207,5.293 L22,6 L20.207,6.707 L19.5,8.5 L18.793,6.707 L17,6 L18.793,5.293 Z"/>
          </svg>
          {{ generatingCode ? '生成中...' : '智能生成' }}
        </button>
        <button class="btn-stop" v-if="generatingCode" @click="stopGenerateWorkflowCode">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M6,6H18V18H6V6Z"/>
          </svg>
          暂停
        </button>
        <button class="btn-save" @click="saveWorkflow" :disabled="saving">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z"/>
          </svg>
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </header>

    <main class="editor-main">
      <div class="code-editor-wrapper">
        <button class="btn-toggle-panel" 
                @click="handleToggleClick" 
                @mousedown="startDrag"
                :title="isSearchPanelCollapsed ? '显示查询面板' : '隐藏查询面板'"
                :style="{ top: toggleButtonPosition + '%' }">
          <svg viewBox="0 0 24 24" v-if="isSearchPanelCollapsed">
            <path fill="currentColor" d="M15.41,16.59L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.59Z"/>
          </svg>
          <svg viewBox="0 0 24 24" v-else>
            <path fill="currentColor" d="M8.59,16.59L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.59Z"/>
          </svg>
        </button>
        <button class="btn-toggle-test" 
                @click="handleTestToggleClick" 
                @mousedown="startTestDrag"
                :title="isTestPanelCollapsed ? '显示测试面板' : '隐藏测试面板'"
                :style="{ top: testButtonPosition + '%' }">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M8 5v14l11-7z"/>
          </svg>
        </button>
        <button class="btn-toggle-ai" 
                v-if="checkOutput || checkIssues.length > 0 || generateOutput"
                @click="handleAIToggleClick"
                @mousedown="startAIDrag"
                :title="isAIPanelCollapsed ? '显示AI面板' : '隐藏AI面板'"
                :style="{ top: aiButtonPosition + '%' }">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M12,3 L13.5,10.5 L21,12 L13.5,13.5 L12,21 L10.5,13.5 L3,12 L10.5,10.5 Z M19.5,3.5 L20.207,5.293 L22,6 L20.207,6.707 L19.5,8.5 L18.793,6.707 L17,6 L18.793,5.293 Z"/>
          </svg>
        </button>
        <div class="editor-toolbar">
          <div class="toolbar-left">
            <span class="file-name">
              <svg viewBox="0 0 24 24" class="file-icon">
                <path fill="currentColor" d="M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z"/>
              </svg>
              workflow code
            </span>
          </div>
          <div class="toolbar-right">
            <span class="line-count">行数: {{ lineCount }}</span>
            <span class="char-count">字符: {{ charCount }}</span>
          </div>
        </div>
        <div class="editor-container" ref="editorContainer">
          <div class="editor-scroll-content">
            <div class="line-numbers">
              <div v-for="n in lineCount" :key="n" class="line-number">{{ n }}</div>
            </div>
            <textarea 
              ref="codeEditor"
              v-model="workflowCode" 
              class="code-textarea"
              spellcheck="false"
              @input="handleCodeChange"
              @keydown="handleKeyDown"
            ></textarea>
          </div>
        </div>
      </div>

      <div class="search-panel" :class="{ 'collapsed': isSearchPanelCollapsed }">
        <div class="search-section">
          <h3 class="search-title">
            <svg viewBox="0 0 24 24" class="search-icon">
              <path fill="currentColor" d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
            </svg>
            查询智能体
          </h3>
          <div class="search-input-group">
            <input 
              v-model="agentSearchQuery" 
              type="text" 
              placeholder="输入智能体名称..."
              class="search-input"
              @keyup.enter="searchAgents"
            />
            <button class="btn-search" @click="searchAgents" :disabled="searching">
              {{ searching ? '查询中...' : '查询' }}
            </button>
          </div>
          <div class="search-results" v-if="agentSearchResults.length > 0">
            <div v-for="agent in agentSearchResults" :key="agent.id" class="result-item">
              <span class="result-name">{{ agent.name }}</span>
              <span class="result-type" :class="agent.type">
                {{ agent.type === 'agent' ? '普通智能体' : '工作流智能体' }}
              </span>
              <button class="btn-copy" @click="copyToClipboard(String(agent.id))" title="复制ID">
                ID: {{ agent.id }}
              </button>
            </div>
          </div>
          <div class="no-results" v-if="agentSearched && agentSearchResults.length === 0">
            未找到匹配的智能体
          </div>
        </div>

        <div class="search-section">
          <h3 class="search-title">
            <svg viewBox="0 0 24 24" class="search-icon">
              <path fill="currentColor" d="M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z"/>
            </svg>
            查询代码工具
          </h3>
          <div class="search-input-group">
            <input 
              v-model="toolSearchQuery" 
              type="text" 
              placeholder="输入代码工具名称..."
              class="search-input"
              @keyup.enter="searchCodeTools"
            />
            <button class="btn-search" @click="searchCodeTools" :disabled="searching">
              {{ searching ? '查询中...' : '查询' }}
            </button>
          </div>
          <div class="search-results" v-if="toolSearchResults.length > 0">
            <div v-for="tool in toolSearchResults" :key="tool.name" class="result-item">
              <span class="result-name">{{ tool.display_name || tool.name }}</span>
              <div class="tool-params" v-if="tool.parameters && tool.parameters.length > 0">
                <span class="params-label">参数:</span>
                <div v-for="param in tool.parameters" :key="param.name" class="param-item">
                  <span class="param-name">{{ param.name }}</span>
                  <span class="param-type">({{ param.type }})</span>
                  <span v-if="param.description" class="param-desc">{{ param.description }}</span>
                </div>
              </div>
              <button class="btn-copy" @click="copyToClipboard(tool.name)" title="复制函数名">
                函数名: {{ tool.name }}
              </button>
            </div>
          </div>
          <div class="no-results" v-if="toolSearched && toolSearchResults.length === 0">
            未找到匹配的代码工具
          </div>
        </div>
      </div>

      <div class="test-panel" :class="{ 'collapsed': isTestPanelCollapsed }">
        <div class="test-section">
          <h3 class="test-title">
            <svg viewBox="0 0 24 24" class="test-icon">
              <path fill="currentColor" d="M8 5v14l11-7z"/>
            </svg>
            运行测试
          </h3>
          <button class="btn-parse-params" @click="parseWorkflowParams" :disabled="parsingParams">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z"/>
            </svg>
            {{ parsingParams ? '解析中...' : '解析参数' }}
          </button>
          <div class="parse-status" v-if="parseMessage" :class="{ 'parse-error': !parseSuccess }">
            {{ parseMessage }}
          </div>
          <div class="test-input-group" v-for="param in parsedParams" :key="param.name">
            <label class="test-label">
              {{ param.name }}
              <span class="param-type" v-if="param.type">({{ param.type }})</span>
              <span class="param-default" v-if="param.default">[默认: {{ param.default }}]</span>
            </label>
            <textarea 
              v-if="param.type === 'text' || param.type === 'str' || param.type === 'string' || param.type === 'df'"
              v-model="paramValues[param.name]" 
              class="test-textarea"
              :placeholder="'输入' + param.name + '...'"
              rows="3"
            ></textarea>
            <input 
              v-else
              v-model="paramValues[param.name]" 
              type="text"
              class="test-input"
              :placeholder="'输入' + param.name + '...'"
            />
          </div>
          <button class="btn-run-test" @click="runTest" :disabled="testRunning || parsedParams.length === 0">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
            </svg>
            {{ testRunning ? '运行中...' : '运行测试' }}
          </button>
        </div>

        <div class="test-section" v-if="testOutput">
          <h3 class="test-title">
            <svg viewBox="0 0 24 24" class="test-icon">
              <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
            运行结果
          </h3>
          <div class="test-output">
            <pre>{{ testOutput }}</pre>
          </div>
        </div>

        <div class="test-section" v-if="testUiConfig">
          <h3 class="test-title">
            <svg viewBox="0 0 24 24" class="test-icon">
              <path fill="currentColor" d="M12,16L2,6H22L12,16M12,19L2,9V19H22V9L12,19Z"/>
            </svg>
            UI Config
          </h3>
          <div class="ui-config-container">
            <WorkflowUI :ui-config="testUiConfig" />
          </div>
        </div>

        <div class="test-section" v-if="testSavedFiles && testSavedFiles.length > 0">
          <h3 class="test-title">
            <svg viewBox="0 0 24 24" class="test-icon">
              <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M12,19L8,15H10.5V12H13.5V15H16L12,19Z"/>
            </svg>
            Saved Files
          </h3>
          <div class="saved-files">
            <div v-for="(file, index) in testSavedFiles" :key="index" class="saved-file-item">
              <span class="file-name">{{ getFileName(file) }}</span>
              <a :href="getFileUrl(file)" target="_blank" class="file-download">下载</a>
            </div>
          </div>
        </div>
      </div>

      <div class="ai-panel" :class="{ 'collapsed': isAIPanelCollapsed }">
        <div class="ai-section" v-if="activeAITab === 'check'">
          <h3 class="ai-title">
            <svg viewBox="0 0 24 24" class="ai-icon">
              <path fill="currentColor" d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z"/>
            </svg>
            智能检查结果
          </h3>
          <div class="check-result" v-if="checkOutput || checkIssues.length > 0">
            <div class="check-summary" :class="checkSuccess ? 'success' : 'has-issues'">
              {{ checkSummary }}
            </div>
            <div class="issues-list" v-if="checkIssues.length > 0">
              <div v-for="(issue, index) in checkIssues" :key="index" class="issue-item" :class="issue.severity">
                <span class="issue-line">第 {{ issue.line }} 行</span>
                <span class="issue-message">{{ issue.message }}</span>
                <span class="issue-severity">{{ issue.severity === 'error' ? '错误' : issue.severity === 'warning' ? '警告' : '提示' }}</span>
              </div>
            </div>
            <div class="check-output" v-if="checkOutput">
              <pre>{{ checkOutput }}</pre>
            </div>
          </div>
        </div>

        <div class="ai-section" v-if="activeAITab === 'generate'">
          <h3 class="ai-title">
            <svg viewBox="0 0 24 24" class="ai-icon">
              <path fill="currentColor" d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M12,6L14.5,11L20,12L16,16L17,22L12,19L7,22L8,16L4,12L9.5,11L12,6Z"/>
            </svg>
            智能生成结果
          </h3>
          <div class="generate-result" v-if="generateOutput">
            <div class="generate-output">
              <pre>{{ generateOutput }}</pre>
            </div>
            <button class="btn-apply-code" @click="applyGeneratedCode" :disabled="!generateComplete">
              应用到编辑器
            </button>
          </div>
        </div>
      </div>
    </main>

    <div class="toast" v-if="toast.show" :class="toast.type">
      {{ toast.message }}
    </div>

    <div class="modal-overlay" v-if="showGenerateModal" @click="closeGenerateModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>智能生成工作流代码</h2>
          <button class="btn-close" @click="closeGenerateModal">×</button>
        </div>
        <div class="modal-body">
          <div class="generate-input">
            <label>请输入您的要求：</label>
            <textarea 
              v-model="generateRequirements" 
              class="requirements-textarea"
              placeholder="例如：创建一个工作流，接收用户输入，调用知识库查询相关信息，然后用模型生成回答..."
              rows="5"
            ></textarea>
          </div>
          <div class="generate-options">
            <label class="checkbox-label">
              <input type="checkbox" v-model="useCurrentCode" />
              基于当前代码修改
            </label>
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" @click="closeGenerateModal">取消</button>
            <button class="btn-generate" @click="generateWorkflowCode" :disabled="generatingCode || !generateRequirements.trim()">
              {{ generatingCode ? '生成中...' : '生成' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import WorkflowUI from '../components/WorkflowUI.vue'

const route = useRoute()
const router = useRouter()

const agentId = computed(() => route.params.id)
const agentName = ref('')
const workflowCode = ref('')
const originalCode = ref('')
const saving = ref(false)
const codeEditor = ref(null)
const toast = ref({ show: false, message: '', type: 'success' })

const checkingCode = ref(false)
const generatingCode = ref(false)
const isAIPanelCollapsed = ref(true)
const activeAITab = ref('')
const checkOutput = ref('')
const checkSuccess = ref(false)
const checkSummary = ref('')
const checkIssues = ref([])
const generateOutput = ref('')
const generateComplete = ref(false)
const generateRequirements = ref('')
const useCurrentCode = ref(true)
const showGenerateModal = ref(false)
const abortController = ref(null)

const agentSearchQuery = ref('')
const agentSearchResults = ref([])
const agentSearched = ref(false)
const toolSearchQuery = ref('')
const toolSearchResults = ref([])
const toolSearched = ref(false)
const searching = ref(false)
const isSearchPanelCollapsed = ref(false)
const toggleButtonPosition = ref(50)
const isDragging = ref(false)

const isTestPanelCollapsed = ref(true)
const testButtonPosition = ref(70)
const isTestDragging = ref(false)

const aiButtonPosition = ref(80)
const isAIDragging = ref(false)
const testInput = ref('')
const testParams = ref('')
const testRunning = ref(false)
const testOutput = ref('')
const testUiConfig = ref(null)
const testSavedFiles = ref([])

const parsingParams = ref(false)
const parsedParams = ref([])
const paramValues = ref({})
const parseMessage = ref('')
const parseSuccess = ref(false)

const isSaved = computed(() => workflowCode.value === originalCode.value)

const lineCount = computed(() => {
  return workflowCode.value.split('\n').length
})

const charCount = computed(() => {
  return workflowCode.value.length
})

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

const loadWorkflowAgent = async () => {
  try {
    const response = await axios.get(`/api/workflow-agents/${agentId.value}`)
    agentName.value = response.data.name
    workflowCode.value = response.data.workflow_code || getDefaultWorkflowCode(response.data)
    originalCode.value = workflowCode.value
  } catch (error) {
    showToast('加载工作流失败，智能体不存在', 'error')
    console.error('Failed to load workflow agent:', error)
    setTimeout(() => {
      router.push('/dashboard/agents')
    }, 1500)
  }
}

const getDefaultWorkflowCode = (agent) => {
  return `// 输入参数在start节点定义, 输出: ctx.final_return

"id": "start", "name": "${agent.name}", "node": "start",  
"params": [{"name": "input_data", "type": "text"}];
"id": 1, "name": "安全审核", "node": "model", 
"messages": [
{"role": "system", 
"content": "你是一个专业的安全审核助手，你需要根据用户输入的内容，判断是否符合安全规范。
如果符合，输出“合规”；如果不符合，输出“违规”。严格只输出“合规”或“违规”，不要输出任何解释，不要输出其它内容。"}, 
memory.get("history")
], "stream": false, "verbose": false, "output_format": "text";

{ 
    if ctx.output(1) == "合规":
        ctx.goto(2)
    elif ctx.output(1) == "违规":
        ctx.final_return("抱歉，暂时无法回答您的问题")
    else:
        ctx.goto(1, max_loops = 2)  # 若次数超过2次，返回false, 继续执行下面的代码
        ctx.final_return("未知错误")
}

"id": 2, "node": "knowledgebase", 
"baselist": ["course_info"], "query": ctx.get("input_data"), "output": ["context", "error"], "next": 3;

{
    if ctx.output(2).error:
        ctx.final_return(ctx.output(2).error)
    elif ctx.output(2).context:
        ctx.verbose_return(memory.get("测试"))
        ctx.verbose_return('\n')
        ctx.verbose_return('')
        ctx.goto(3)
    else:
        ctx.final_return("抱歉，没有找到相关课程")
}

"id": 3, "node": "model", 
"messages": [
{"role": "system", 
"content": "你是一个专业的课程信息助手，你需要根据参考信息回答用户的问题。参考信息为：{ctx.output(2).context}"}, 
memory.get("history")], "stream": true, "end": true;
`
}

const saveWorkflow = async () => {
  saving.value = true
  try {
    await axios.put(`/api/workflow-agents/${agentId.value}`, {
      workflow_code: workflowCode.value
    })
    originalCode.value = workflowCode.value
    showToast('保存成功')
  } catch (error) {
    showToast('保存失败', 'error')
    console.error('Failed to save workflow:', error)
  } finally {
    saving.value = false
  }
}

const handleBack = () => {
  if (!isSaved.value) {
    if (!confirm('工作流未保存，确定要返回吗？')) {
      return
    }
  }
  router.push('/dashboard/agents')
}

const restoreCode = () => {
  if (isSaved.value) {
    return
  }
  if (confirm('确定要恢复上次保存的代码吗？当前未保存的修改将丢失。')) {
    workflowCode.value = originalCode.value
    showToast('已恢复上次保存的代码')
  }
}

const handleCodeChange = () => {
}

const handleKeyDown = (e) => {
  if (e.key === 'Tab') {
    e.preventDefault()
    const start = codeEditor.value.selectionStart
    const end = codeEditor.value.selectionEnd
    workflowCode.value = workflowCode.value.substring(0, start) + '    ' + workflowCode.value.substring(end)
    setTimeout(() => {
      codeEditor.value.selectionStart = codeEditor.value.selectionEnd = start + 4
    }, 0)
  }
  
  if (e.key === 'Enter') {
    e.preventDefault()
    const textarea = codeEditor.value
    const cursorPos = textarea.selectionStart
    const textBefore = workflowCode.value.substring(0, cursorPos)
    const currentLine = textBefore.split('\n').pop()
    const indentMatch = currentLine.match(/^(\s*)/)
    const indent = indentMatch ? indentMatch[1] : ''
    
    const textAfter = workflowCode.value.substring(cursorPos)
    workflowCode.value = textBefore + '\n' + indent + textAfter
    
    setTimeout(() => {
      const newPos = cursorPos + 1 + indent.length
      textarea.selectionStart = textarea.selectionEnd = newPos
    }, 0)
  }
  
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveWorkflow()
  }
}

const handleBeforeUnload = (e) => {
  if (testSavedFiles.value && testSavedFiles.value.length > 0) {
    const filePaths = testSavedFiles.value
      .map(f => f.file_path || f.path)
      .filter(p => p)
    
    if (filePaths.length > 0) {
      const blob = new Blob([JSON.stringify({ file_paths: filePaths })], {
        type: 'application/json'
      })
      navigator.sendBeacon('/api/workflow-files/delete-beacon', blob)
    }
  }
  
  if (!isSaved.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}

const searchAgents = async () => {
  if (!agentSearchQuery.value.trim()) {
    showToast('请输入智能体名称', 'error')
    return
  }
  
  searching.value = true
  try {
    const response = await axios.get('/api/unified-agent-chat/agents/search', {
      params: { name: agentSearchQuery.value }
    })
    agentSearchResults.value = [...response.data.agents, ...response.data.workflow_agents]
    agentSearched.value = true
  } catch (error) {
    showToast('查询智能体失败', 'error')
    console.error('Failed to search agents:', error)
  } finally {
    searching.value = false
  }
}

const searchCodeTools = async () => {
  if (!toolSearchQuery.value.trim()) {
    showToast('请输入代码工具名称', 'error')
    return
  }
  
  searching.value = true
  try {
    const response = await axios.get('/api/unified-agent-chat/code-tools/search', {
      params: { name: toolSearchQuery.value }
    })
    toolSearchResults.value = response.data
    toolSearched.value = true
  } catch (error) {
    showToast('查询代码工具失败', 'error')
    console.error('Failed to search code tools:', error)
  } finally {
    searching.value = false
  }
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    showToast('已复制到剪贴板')
  } catch (error) {
    showToast('复制失败', 'error')
    console.error('Failed to copy:', error)
  }
}

const toggleSearchPanel = () => {
  isSearchPanelCollapsed.value = !isSearchPanelCollapsed.value
}

let dragStartY = 0
let dragStartPosition = 0
let hasDragged = false

const startDrag = (e) => {
  e.preventDefault()
  dragStartY = e.clientY
  dragStartPosition = toggleButtonPosition.value
  hasDragged = false
  isDragging.value = true
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  if (!isDragging.value) return
  
  const deltaY = e.clientY - dragStartY
  if (Math.abs(deltaY) > 3) {
    hasDragged = true
  }
  
  const editorWrapper = document.querySelector('.code-editor-wrapper')
  if (!editorWrapper) return
  
  const wrapperHeight = editorWrapper.offsetHeight
  const deltaPercent = (deltaY / wrapperHeight) * 100
  
  let newPosition = dragStartPosition + deltaPercent
  newPosition = Math.max(5, Math.min(95, newPosition))
  
  toggleButtonPosition.value = newPosition
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

const handleToggleClick = () => {
  if (hasDragged) {
    hasDragged = false
    return
  }
  toggleSearchPanel()
}

const toggleTestPanel = () => {
  isTestPanelCollapsed.value = !isTestPanelCollapsed.value
}

let testDragStartY = 0
let testDragStartPosition = 0
let hasTestDragged = false

const startTestDrag = (e) => {
  e.preventDefault()
  testDragStartY = e.clientY
  testDragStartPosition = testButtonPosition.value
  hasTestDragged = false
  isTestDragging.value = true
  
  document.addEventListener('mousemove', onTestDrag)
  document.addEventListener('mouseup', stopTestDrag)
}

const onTestDrag = (e) => {
  if (!isTestDragging.value) return
  
  const deltaY = e.clientY - testDragStartY
  if (Math.abs(deltaY) > 3) {
    hasTestDragged = true
  }
  
  const editorWrapper = document.querySelector('.code-editor-wrapper')
  if (!editorWrapper) return
  
  const wrapperHeight = editorWrapper.offsetHeight
  const deltaPercent = (deltaY / wrapperHeight) * 100
  
  let newPosition = testDragStartPosition + deltaPercent
  newPosition = Math.max(5, Math.min(95, newPosition))
  
  testButtonPosition.value = newPosition
}

const stopTestDrag = () => {
  isTestDragging.value = false
  document.removeEventListener('mousemove', onTestDrag)
  document.removeEventListener('mouseup', stopTestDrag)
}

const handleTestToggleClick = () => {
  if (hasTestDragged) {
    hasTestDragged = false
    return
  }
  toggleTestPanel()
}

const parseWorkflowParams = async () => {
  parsingParams.value = true
  parseMessage.value = ''
  parseSuccess.value = false
  
  try {
    const response = await axios.post('/api/workflow-test/parse', {
      code: workflowCode.value
    })
    
    if (response.data.success) {
      parsedParams.value = response.data.params || []
      parseSuccess.value = true
      parseMessage.value = response.data.message
      
      paramValues.value = {}
      for (const param of parsedParams.value) {
        if (param.default !== undefined && param.default !== null) {
          paramValues.value[param.name] = param.default
        } else {
          paramValues.value[param.name] = ''
        }
      }
      
      showToast('参数解析成功', 'success')
    } else {
      parseSuccess.value = false
      parseMessage.value = response.data.message
      showToast(response.data.message, 'error')
    }
  } catch (error) {
    parseSuccess.value = false
    parseMessage.value = '解析失败: ' + (error.response?.data?.detail || error.message)
    showToast('解析参数失败', 'error')
    console.error('Parse params failed:', error)
  } finally {
    parsingParams.value = false
  }
}

const runTest = async () => {
  if (parsedParams.value.length === 0) {
    showToast('请先解析参数', 'error')
    return
  }
  
  const params = {}
  for (const param of parsedParams.value) {
    const value = paramValues.value[param.name]
    if (value === '' || value === undefined || value === null) {
      if (param.default !== undefined && param.default !== null) {
        continue
      } else {
        showToast(`请输入参数: ${param.name}`, 'error')
        return
      }
    }
    params[param.name] = value
  }
  
  if (testSavedFiles.value && testSavedFiles.value.length > 0) {
    const filePaths = testSavedFiles.value
      .map(f => f.file_path || f.path)
      .filter(p => p)
    
    if (filePaths.length > 0) {
      const token = localStorage.getItem('token')
      try {
        await fetch('/api/workflow-files/delete', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ file_paths: filePaths })
        })
      } catch (err) {
        console.error('Failed to delete previous test files:', err)
      }
    }
  }
  
  testRunning.value = true
  testOutput.value = ''
  testUiConfig.value = null
  testSavedFiles.value = []
  
  const token = localStorage.getItem('token')
  
  try {
    const response = await fetch(`/api/workflow-test/${agentId.value}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        query: params.input_data || '',
        params: params,
        code: workflowCode.value
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data.trim()) {
            try {
              const item = JSON.parse(data)
              
              if (item.type === 'stream_chunk' || item.type === 'result') {
                testOutput.value += item.content || ''
              } else if (item.type === 'verbose') {
                testOutput.value += item.content + '\n'
              } else if (item.type === 'header') {
                testOutput.value = item.content
              } else if (item.type === 'ui_config') {
                testUiConfig.value = item.ui_config
              } else if (item.type === 'context') {
                if (item.context.ui_config) {
                  testUiConfig.value = item.context.ui_config
                }
                if (item.context.saved_files) {
                  testSavedFiles.value = item.context.saved_files
                }
              } else if (item.type === 'error') {
                testOutput.value += '错误: ' + item.content + '\n'
              }
            } catch (e) {
              console.error('Parse error:', e)
            }
          }
        }
      }
    }
    
    showToast('测试完成', 'success')
  } catch (error) {
    showToast('测试失败: ' + error.message, 'error')
    console.error('Test failed:', error)
  } finally {
    testRunning.value = false
  }
}

const checkWorkflowCode = async () => {
  checkingCode.value = true
  checkOutput.value = ''
  checkSuccess.value = false
  checkSummary.value = ''
  checkIssues.value = []
  activeAITab.value = 'check'
  isAIPanelCollapsed.value = false
  
  abortController.value = new AbortController()
  
  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/workflow-ai/check', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        code: workflowCode.value
      }),
      signal: abortController.value.signal
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data.trim()) {
            try {
              const item = JSON.parse(data)
              
              if (item.type === 'issue') {
                checkIssues.value.push(item.data)
              } else if (item.type === 'chunk') {
                checkOutput.value += item.content
              } else if (item.type === 'complete') {
                try {
                  let content = item.content
                  // 尝试提取JSON（处理可能包含markdown或其他文本的情况）
                  const jsonMatch = content.match(/\{[\s\S]*"success"[\s\S]*\}/)
                  if (jsonMatch) {
                    content = jsonMatch[0]
                  }
                  const parsed = JSON.parse(content)
                  checkSummary.value = parsed.message || '检查完成'
                  checkSuccess.value = parsed.success !== false
                  if (parsed.issues) {
                    checkIssues.value = [...checkIssues.value, ...parsed.issues]
                  }
                } catch (e) {
                  checkSummary.value = item.content
                }
              } else if (item.type === 'error') {
                showToast(item.message || '检查失败', 'error')
              }
            } catch (e) {
              console.error('Parse error:', e)
            }
          }
        }
      }
    }
    
    showToast('检查完成', 'success')
  } catch (error) {
    if (error.name === 'AbortError') {
      showToast('已暂停检查', 'info')
    } else {
      showToast('检查工作流代码失败', 'error')
      console.error('Check workflow code failed:', error)
    }
  } finally {
    checkingCode.value = false
    abortController.value = null
  }
}

const stopCheckWorkflowCode = () => {
  if (abortController.value) {
    abortController.value.abort()
  }
}

const showGenerateDialog = () => {
  generateRequirements.value = ''
  useCurrentCode.value = true
  showGenerateModal.value = true
}

const closeGenerateModal = () => {
  showGenerateModal.value = false
  generateRequirements.value = ''
  useCurrentCode.value = true
}

const generateWorkflowCode = async () => {
  if (!generateRequirements.value.trim()) {
    showToast('请输入要求', 'error')
    return
  }
  
  showGenerateModal.value = false
  generatingCode.value = true
  generateOutput.value = ''
  generateComplete.value = false
  activeAITab.value = 'generate'
  isAIPanelCollapsed.value = false
  
  abortController.value = new AbortController()
  
  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/workflow-ai/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        requirements: generateRequirements.value,
        current_code: useCurrentCode.value ? workflowCode.value : ''
      }),
      signal: abortController.value.signal
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data.trim()) {
            try {
              const item = JSON.parse(data)
              
              if (item.type === 'chunk') {
                generateOutput.value += item.content
              } else if (item.type === 'complete') {
                generateComplete.value = true
              } else if (item.type === 'error') {
                showToast(item.message || '生成失败', 'error')
              }
            } catch (e) {
              console.error('Parse error:', e)
            }
          }
        }
      }
    }
    
    showToast('生成完成', 'success')
  } catch (error) {
    if (error.name === 'AbortError') {
      showToast('已暂停生成', 'info')
    } else {
      showToast('生成工作流代码失败', 'error')
      console.error('Generate workflow code failed:', error)
    }
  } finally {
    generatingCode.value = false
    abortController.value = null
  }
}

const stopGenerateWorkflowCode = () => {
  if (abortController.value) {
    abortController.value.abort()
  }
}

const applyGeneratedCode = () => {
  if (generateOutput.value) {
    workflowCode.value = generateOutput.value
    showToast('已应用到编辑器', 'success')
  }
}

let aiDragStartY = 0
let aiDragStartPosition = 0
let hasAIDragged = false

const startAIDrag = (e) => {
  e.preventDefault()
  aiDragStartY = e.clientY
  aiDragStartPosition = aiButtonPosition.value
  hasAIDragged = false
  isAIDragging.value = true
  
  document.addEventListener('mousemove', onAIDrag)
  document.addEventListener('mouseup', stopAIDrag)
}

const onAIDrag = (e) => {
  if (!isAIDragging.value) return
  
  const deltaY = e.clientY - aiDragStartY
  if (Math.abs(deltaY) > 3) {
    hasAIDragged = true
  }
  
  const editorWrapper = document.querySelector('.code-editor-wrapper')
  if (!editorWrapper) return
  
  const wrapperHeight = editorWrapper.offsetHeight
  const deltaPercent = (deltaY / wrapperHeight) * 100
  
  let newPosition = aiDragStartPosition + deltaPercent
  newPosition = Math.max(5, Math.min(95, newPosition))
  
  aiButtonPosition.value = newPosition
}

const stopAIDrag = () => {
  isAIDragging.value = false
  document.removeEventListener('mousemove', onAIDrag)
  document.removeEventListener('mouseup', stopAIDrag)
}

const handleAIToggleClick = () => {
  if (hasAIDragged) {
    hasAIDragged = false
    return
  }
  isAIPanelCollapsed.value = !isAIPanelCollapsed.value
}

const getFileName = (file) => {
  let name = ''
  if (file.filename) {
    name = file.filename
  } else if (file.name) {
    name = file.name
  } else if (file.file_path) {
    const parts = file.file_path.replace(/\\/g, '/').split('/')
    name = parts[parts.length - 1] || 'file'
  } else if (file.path) {
    const parts = file.path.replace(/\\/g, '/').split('/')
    name = parts[parts.length - 1] || 'file'
  } else {
    name = 'file'
  }
  
  if (name.length > 25) {
    const ext = name.lastIndexOf('.')
    if (ext > 0 && ext > name.length - 10) {
      name = name.substring(0, 22 - (name.length - ext)) + '...' + name.substring(ext)
    } else {
      name = name.substring(0, 22) + '...'
    }
  }
  
  return name
}

const getFileUrl = (file) => {
  if (file.file_path) {
    return `/api/workflow-files/${file.file_path.replace(/\\/g, '/')}`
  }
  if (file.path) {
    return `/api/workflow-files/${file.path.replace(/\\/g, '/')}`
  }
  return '#'
}

onMounted(() => {
  loadWorkflowAgent()
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  
  if (testSavedFiles.value && testSavedFiles.value.length > 0) {
    const filePaths = testSavedFiles.value
      .map(f => f.file_path || f.path)
      .filter(p => p)
    
    if (filePaths.length > 0) {
      const token = localStorage.getItem('token')
      fetch('/api/workflow-files/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ file_paths: filePaths })
      }).catch(err => {
        console.error('Failed to delete test files:', err)
      })
    }
  }
})
</script>

<style scoped>
.workflow-editor-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1e1e1e;
  color: #d4d4d4;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  width: 28px;
  height: 28px;
  color: #667eea;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  color: #d4d4d4;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #3c3c3c;
  border-color: #667eea;
}

.btn-back svg {
  width: 18px;
  height: 18px;
}

.header-center {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.save-status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  background: #5a3d3d;
  color: #f48771;
}

.save-status.saved {
  background: #3d5a3d;
  color: #89d185;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-restore {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  color: #d4d4d4;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-restore:hover:not(:disabled) {
  background: #3c3c3c;
  border-color: #667eea;
  color: #667eea;
}

.btn-restore:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-restore svg {
  width: 18px;
  height: 18px;
}

.btn-save {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-save svg {
  width: 18px;
  height: 18px;
}

.btn-smart-check {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-smart-check:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-smart-check:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-smart-check svg {
  width: 18px;
  height: 18px;
}

.btn-smart-generate {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-smart-generate:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-smart-generate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-smart-generate svg {
  width: 18px;
  height: 18px;
}

.btn-stop {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-stop:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.btn-stop svg {
  width: 18px;
  height: 18px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #2d2d30;
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #3c3c3c;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.btn-close {
  background: transparent;
  border: none;
  color: #d4d4d4;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #3c3c3c;
  color: #fff;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.check-summary {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 14px;
  line-height: 1.6;
}

.check-summary.success {
  background: #1e3a2f;
  border: 1px solid #2d5a47;
  color: #4ade80;
}

.check-summary.has-issues {
  background: #3a1e1e;
  border: 1px solid #5a2d2d;
  color: #f87171;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.issue-item {
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 14px;
}

.issue-item.error {
  background: #3a1e1e;
  border-left: 4px solid #f87171;
}

.issue-item.warning {
  background: #3a2e1e;
  border-left: 4px solid #fbbf24;
}

.issue-item.info {
  background: #1e2a3a;
  border-left: 4px solid #60a5fa;
}

.issue-line {
  font-weight: 600;
  color: #667eea;
  white-space: nowrap;
  min-width: 70px;
}

.issue-message {
  flex: 1;
  color: #d4d4d4;
  line-height: 1.5;
}

.issue-severity {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.issue-item.error .issue-severity {
  background: #f87171;
  color: #fff;
}

.issue-item.warning .issue-severity {
  background: #fbbf24;
  color: #000;
}

.issue-item.info .issue-severity {
  background: #60a5fa;
  color: #fff;
}

.no-issues {
  text-align: center;
  padding: 40px 20px;
  color: #4ade80;
  font-size: 16px;
}

.generate-input {
  margin-bottom: 20px;
}

.generate-input label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #d4d4d4;
}

.requirements-textarea {
  width: 100%;
  padding: 12px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 8px;
  color: #d4d4d4;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 120px;
}

.requirements-textarea:focus {
  outline: none;
  border-color: #667eea;
}

.generate-options {
  margin-bottom: 20px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #d4d4d4;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel {
  padding: 10px 20px;
  background: #3c3c3c;
  border: none;
  border-radius: 8px;
  color: #d4d4d4;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #4c4c4c;
}

.btn-generate {
  padding: 10px 24px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-generate:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.4);
}

.btn-generate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.editor-main {
  flex: 1;
  display: flex;
  overflow: hidden;
  gap: 1px;
}

.search-panel {
  width: 320px;
  background: #252526;
  border-left: 1px solid #3c3c3c;
  overflow-y: auto;
  flex-shrink: 0;
  transition: width 0.3s ease;
}

.search-panel.collapsed {
  width: 0;
  border-left: none;
  overflow: hidden;
}

.search-panel.collapsed .search-section {
  display: none;
}

.search-section {
  padding: 16px;
  border-bottom: 1px solid #3c3c3c;
}

.search-section:last-child {
  border-bottom: none;
}

.search-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 12px 0;
}

.search-icon {
  width: 18px;
  height: 18px;
  color: #667eea;
}

.search-input-group {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  background: #3c3c3c;
  border: 1px solid #555;
  border-radius: 4px;
  color: #d4d4d4;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #667eea;
}

.search-input::placeholder {
  color: #858585;
}

.btn-search {
  padding: 8px 16px;
  background: #667eea;
  border: none;
  border-radius: 4px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.btn-search:hover:not(:disabled) {
  background: #5568d8;
}

.btn-search:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: calc(50vh - 150px);
  overflow-y: auto;
  padding-right: 4px;
}

.search-results::-webkit-scrollbar {
  width: 6px;
}

.search-results::-webkit-scrollbar-track {
  background: #1e1e1e;
  border-radius: 3px;
}

.search-results::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 3px;
}

.search-results::-webkit-scrollbar-thumb:hover {
  background: #667eea;
}

.result-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  background: #1e1e1e;
  border-radius: 4px;
  border: 1px solid #3c3c3c;
}

.result-name {
  font-size: 13px;
  color: #d4d4d4;
  font-weight: 500;
}

.result-type {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 3px;
  display: inline-block;
  width: fit-content;
}

.result-type.agent {
  background: #3d5a3d;
  color: #89d185;
}

.result-type.workflow_agent {
  background: #3d4a5a;
  color: #667eea;
}

.tool-params {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 8px;
  background: #252526;
  border-radius: 3px;
  border-left: 2px solid #667eea;
}

.params-label {
  font-size: 11px;
  color: #858585;
  font-weight: 600;
}

.param-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 12px;
}

.param-name {
  color: #d4d4d4;
  font-weight: 500;
}

.param-type {
  color: #519aba;
  font-size: 11px;
}

.param-desc {
  color: #858585;
  font-size: 11px;
  font-style: italic;
}

.btn-copy {
  padding: 4px 8px;
  background: #3c3c3c;
  border: 1px solid #555;
  border-radius: 3px;
  color: #d4d4d4;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.btn-copy:hover {
  background: #667eea;
  border-color: #667eea;
  color: #fff;
}

.no-results {
  padding: 12px;
  text-align: center;
  color: #858585;
  font-size: 13px;
}

.code-editor-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  position: relative;
}

.btn-toggle-panel {
  position: absolute;
  right: 12px;
  width: 32px;
  height: 32px;
  background: #252526;
  border: 1px solid #3c3c3c;
  border-radius: 50%;
  color: #858585;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, border-color 0.2s, color 0.2s;
  z-index: 10;
  opacity: 0;
}

.btn-toggle-panel:active {
  cursor: grabbing;
}

.code-editor-wrapper:hover .btn-toggle-panel {
  opacity: 1;
}

.btn-toggle-panel:hover {
  background: #667eea;
  border-color: #667eea;
  color: #fff;
}

.btn-toggle-panel svg {
  width: 20px;
  height: 20px;
  pointer-events: none;
}

.btn-toggle-test {
  position: absolute;
  right: 12px;
  width: 32px;
  height: 32px;
  background: #252526;
  border: 1px solid #3c3c3c;
  border-radius: 50%;
  color: #858585;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, border-color 0.2s, color 0.2s;
  z-index: 10;
  opacity: 0;
}

.btn-toggle-test:active {
  cursor: grabbing;
}

.code-editor-wrapper:hover .btn-toggle-test {
  opacity: 1;
}

.btn-toggle-test:hover {
  background: #4caf50;
  border-color: #4caf50;
  color: #fff;
}

.btn-toggle-test svg {
  width: 20px;
  height: 20px;
  pointer-events: none;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #d4d4d4;
}

.file-icon {
  width: 16px;
  height: 16px;
  color: #519aba;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.line-count,
.char-count {
  font-size: 12px;
  color: #858585;
}

.editor-container {
  flex: 1;
  overflow: auto;
}

.editor-container::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.editor-container::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.editor-container::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 5px;
}

.editor-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.editor-container::-webkit-scrollbar-corner {
  background: #1e1e1e;
}

.editor-scroll-content {
  display: flex;
  min-height: 100%;
  min-width: max-content;
}

.line-numbers {
  position: sticky;
  left: 0;
  padding: 16px 0;
  background: #1e1e1e;
  border-right: 1px solid #3c3c3c;
  user-select: none;
  flex-shrink: 0;
  z-index: 1;
}

.line-number {
  padding: 0 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #858585;
  text-align: right;
  min-width: 40px;
}

.code-textarea {
  flex: 1;
  padding: 16px;
  background: #1e1e1e;
  border: none;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  outline: none;
  white-space: pre;
  overflow-x: auto;
  overflow-y: hidden;
  min-width: max-content;
}

.code-textarea::-webkit-scrollbar {
  display: none;
}

.code-textarea {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.code-textarea::selection {
  background: #264f78;
}

.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  color: #fff;
  z-index: 2000;
  animation: slideIn 0.3s ease;
}

.toast.success {
  background: #4caf50;
}

.toast.error {
  background: #f44336;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.test-panel {
  width: 400px;
  background: #252526;
  border-left: 1px solid #3c3c3c;
  overflow-y: auto;
  flex-shrink: 0;
  transition: width 0.3s ease;
}

.test-panel.collapsed {
  width: 0;
  border-left: none;
  overflow: hidden;
}

.test-panel.collapsed .test-section {
  display: none;
}

.test-section {
  padding: 16px;
  border-bottom: 1px solid #3c3c3c;
}

.test-section:last-child {
  border-bottom: none;
}

.test-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 12px 0;
}

.test-icon {
  width: 18px;
  height: 18px;
  color: #4caf50;
}

.test-input-group {
  margin-bottom: 12px;
}

.test-label {
  display: block;
  font-size: 12px;
  color: #858585;
  margin-bottom: 6px;
}

.test-textarea {
  width: 100%;
  padding: 8px 12px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 4px;
  color: #d4d4d4;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.test-textarea:focus {
  border-color: #4caf50;
}

.test-textarea::placeholder {
  color: #858585;
}

.btn-run-test {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-run-test:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
}

.btn-run-test:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-run-test svg {
  width: 18px;
  height: 18px;
}

.btn-parse-params {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 8px 16px;
  background: #3c3c3c;
  border: 1px solid #555;
  border-radius: 6px;
  color: #d4d4d4;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 12px;
}

.btn-parse-params:hover:not(:disabled) {
  background: #667eea;
  border-color: #667eea;
  color: #fff;
}

.btn-parse-params:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-parse-params svg {
  width: 16px;
  height: 16px;
}

.parse-status {
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 12px;
  background: #3d5a3d;
  color: #89d185;
}

.parse-status.parse-error {
  background: #5a3d3d;
  color: #f48771;
}

.test-input {
  width: 100%;
  padding: 8px 12px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 4px;
  color: #d4d4d4;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.test-input:focus {
  border-color: #4caf50;
}

.test-input::placeholder {
  color: #858585;
}

.param-type {
  color: #519aba;
  font-size: 11px;
  margin-left: 4px;
}

.param-default {
  color: #858585;
  font-size: 11px;
  margin-left: 4px;
}

.ui-config-container {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.test-output {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 4px;
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.test-output pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.test-output.ui-config {
  border-left: 3px solid #667eea;
}

.saved-files {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.saved-file-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: #1e1e1e;
  border-radius: 4px;
  border: 1px solid #3c3c3c;
}

.saved-file-item .file-name {
  font-size: 13px;
  color: #4caf50;
  font-weight: 500;
  flex: 1;
}

.saved-file-item .file-download {
  font-size: 12px;
  color: #667eea;
  text-decoration: none;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.saved-file-item .file-download:hover {
  background: #667eea;
  color: #fff;
}

.btn-toggle-ai {
  position: absolute;
  right: 12px;
  width: 32px;
  height: 32px;
  background: #252526;
  border: 1px solid #3c3c3c;
  border-radius: 50%;
  color: #858585;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, border-color 0.2s, color 0.2s;
  z-index: 10;
  opacity: 0;
}

.btn-toggle-ai:active {
  cursor: grabbing;
}

.code-editor-wrapper:hover .btn-toggle-ai {
  opacity: 1;
}

.btn-toggle-ai:hover {
  background: #f093fb;
  border-color: #f093fb;
  color: #fff;
}

.btn-toggle-ai svg {
  width: 20px;
  height: 20px;
  pointer-events: none;
}

.ai-panel {
  width: 450px;
  background: #252526;
  border-left: 1px solid #3c3c3c;
  overflow-y: auto;
  flex-shrink: 0;
  transition: width 0.3s ease;
}

.ai-panel.collapsed {
  width: 0;
  border-left: none;
  overflow: hidden;
}

.ai-panel.collapsed .ai-section {
  display: none;
}

.ai-section {
  padding: 16px;
  border-bottom: 1px solid #3c3c3c;
}

.ai-section:last-child {
  border-bottom: none;
}

.ai-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 12px 0;
}

.ai-icon {
  width: 18px;
  height: 18px;
  color: #f093fb;
}

.btn-check-code {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 12px;
}

.btn-check-code:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);
}

.btn-check-code:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-check-code svg {
  width: 18px;
  height: 18px;
}

.check-result {
  margin-top: 12px;
}

.check-output {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 12px;
}

.check-output pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.check-summary {
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
  line-height: 1.6;
}

.check-summary.success {
  background: #1e3a2f;
  border: 1px solid #2d5a47;
  color: #4ade80;
}

.check-summary.has-issues {
  background: #3a1e1e;
  border: 1px solid #5a2d2d;
  color: #f87171;
}

.ai-section .issues-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.ai-section .issue-item {
  padding: 10px 12px;
  border-radius: 6px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
}

.ai-section .issue-item.error {
  background: #3a1e1e;
  border-left: 3px solid #f87171;
}

.ai-section .issue-item.warning {
  background: #3a2e1e;
  border-left: 3px solid #fbbf24;
}

.ai-section .issue-item.info {
  background: #1e2a3a;
  border-left: 3px solid #60a5fa;
}

.ai-section .issue-line {
  font-weight: 600;
  color: #667eea;
  white-space: nowrap;
  min-width: 60px;
  font-size: 12px;
}

.ai-section .issue-message {
  flex: 1;
  color: #d4d4d4;
  line-height: 1.5;
  font-size: 12px;
}

.ai-section .issue-severity {
  padding: 3px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.ai-section .issue-item.error .issue-severity {
  background: #f87171;
  color: #fff;
}

.ai-section .issue-item.warning .issue-severity {
  background: #fbbf24;
  color: #000;
}

.ai-section .issue-item.info .issue-severity {
  background: #60a5fa;
  color: #fff;
}

.ai-section .generate-input {
  margin-bottom: 12px;
}

.ai-section .requirements-textarea {
  width: 100%;
  padding: 10px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  color: #d4d4d4;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
  box-sizing: border-box;
}

.ai-section .requirements-textarea:focus {
  outline: none;
  border-color: #4facfe;
}

.ai-section .requirements-textarea::placeholder {
  color: #858585;
}

.ai-section .generate-options {
  margin-bottom: 12px;
}

.ai-section .checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #d4d4d4;
  cursor: pointer;
}

.ai-section .checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.btn-generate-code {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 12px;
}

.btn-generate-code:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.4);
}

.btn-generate-code:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-generate-code svg {
  width: 18px;
  height: 18px;
}

.generate-result {
  margin-top: 12px;
}

.generate-output {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.generate-output pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.btn-apply-code {
  width: 100%;
  padding: 10px 16px;
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-apply-code:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
}

.btn-apply-code:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
</style>
