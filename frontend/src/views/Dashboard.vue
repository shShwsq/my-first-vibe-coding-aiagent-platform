<template>
  <div class="dashboard">
    <Sidebar :isOpen="sidebarOpen" @toggle="toggleSidebar" @navigate="handleNavigate" />
    
    <div class="main-content" :class="{ expanded: !sidebarOpen }">
      <header class="top-header">
        <div class="header-left">
          <button v-if="isKnowledgeBasePage && selectedKBName" class="btn-back" @click="handleBackToKBList">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
            </svg>
          </button>
          <button v-if="isTestCasesPage && selectedTestCaseFolder" class="btn-back" @click="handleBackToTestCaseFolderList">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
            </svg>
          </button>
          <button v-if="isTestResultsPage && selectedResultFolder" class="btn-back" @click="handleBackToResultFolderList">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
            </svg>
          </button>
          <button v-if="isTestResultsPage && selectedResultAgent && !selectedResultFolder" class="btn-back" @click="handleBackToResultAgentList">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
            </svg>
          </button>
          <h1 class="page-title">{{ basePageTitle }}</h1>
          <template v-if="isChatPage && chatTitle">
            <span v-if="!editingTitle" class="chat-title clickable" @click="startEditTitle" :title="chatTitle">{{ truncateTitle(chatTitle) }}</span>
            <input 
              v-else 
              ref="titleInput"
              v-model="editingTitleText" 
              class="title-input"
              @blur="saveTitle"
              @keyup.enter="saveTitle"
              @keyup.escape="cancelEditTitle"
            />
          </template>
          <button v-if="isApiConfigPage" class="btn-add" @click="handleAddModel">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
            </svg>
          </button>
          <button v-if="isAgentsPage" class="btn-primary header-btn" @click="handleAddAgent">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
            </svg>
            新建智能体
          </button>
          <button v-if="isAgentsPage" class="btn-primary header-btn" @click="handleAddWorkflowAgent">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
            </svg>
            工作流智能体
          </button>
          <div v-if="isAgentsPage" class="agent-search-box">
            <svg viewBox="0 0 24 24" class="search-icon">
              <path fill="currentColor" d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
            </svg>
            <input 
              type="text" 
              v-model="agentSearchQuery" 
              placeholder="搜索智能体..."
              class="agent-search-input"
            />
          </div>
          <button v-if="isKnowledgeBasePage && !selectedKBName" class="btn-add" @click="handleAddKB">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
            </svg>
          </button>
          <button v-if="isTestCasesPage && !selectedTestCaseFolder" class="btn-add" @click="handleAddTestCaseFolder">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
            </svg>
          </button>
          <button v-if="isTestCasesPage && selectedTestCaseFolder" class="btn-secondary header-btn" @click="handleImportFromKB">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M5 20H19V18H5M19 9H15V3H9V9H5L12 16L19 9Z"/>
            </svg>
            从知识库导入
          </button>
          <button v-if="isTestCasesPage && selectedTestCaseFolder" class="btn-primary header-btn" @click="handleAddTestCase">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19 13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
            </svg>
            添加用例
          </button>
          <button v-if="isTestCasesPage && selectedTestCaseFolder" class="btn-secondary header-btn" @click="showGenerateTestCaseModal = true">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/>
            </svg>
            智能生成用例
          </button>
          <button v-if="isTestResultsPage && selectedResultFolder" class="btn-primary header-btn" @click="handleExportTestResults" :disabled="exporting">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
            </svg>
            {{ exporting ? '导出中...' : '导出 Excel' }}
          </button>
          <div v-if="isChatPage" class="model-selector">
            <button ref="modelButtonRef" class="model-select-btn" @click="toggleModelDropdown">
              <svg viewBox="0 0 24 24" class="model-icon">
                <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
              </svg>
              <span>{{ selectedModel?.name || '选择模型' }}</span>
              <svg viewBox="0 0 24 24" class="dropdown-icon">
                <path fill="currentColor" d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/>
              </svg>
            </button>
            <div v-if="showModelDropdown" class="model-dropdown" :style="modelDropdownStyle">
              <div v-if="models.length === 0" class="dropdown-empty">
                暂无可用模型，请先配置
              </div>
              <div 
                v-for="model in models" 
                :key="model.id" 
                class="dropdown-item"
                :class="{ active: selectedModel?.id === model.id }"
                @click="selectModel(model)"
              >
                <div class="model-name">{{ model.name }}</div>
                <div class="model-code">{{ model.code }}</div>
              </div>
            </div>
          </div>
          <div v-if="isChatPage" class="mode-selector">
            <button 
              ref="modeButtonRef"
              class="mode-select-btn" 
              :class="{ disabled: hasMessages }"
              :title="hasMessages ? '对话进行中无法切换模式' : '选择对话模式'"
              @click="!hasMessages && toggleModeDropdown()"
            >
              <svg viewBox="0 0 24 24" class="mode-icon">
                <path fill="currentColor" d="M12,3L2,12H5V20H19V12H22L12,3M12,8.75A2.25,2.25 0 0,1 14.25,11A2.25,2.25 0 0,1 12,13.25A2.25,2.25 0 0,1 9.75,11A2.25,2.25 0 0,1 12,8.75Z"/>
              </svg>
              <span>{{ modeLabels[chatMode] }}</span>
              <svg v-if="!hasMessages" viewBox="0 0 24 24" class="dropdown-icon">
                <path fill="currentColor" d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/>
              </svg>
            </button>
            <div v-if="showModeDropdown && !hasMessages" class="mode-dropdown" :style="modeDropdownStyle">
              <div 
                class="dropdown-item"
                :class="{ active: chatMode === 'chat' }"
                @click="selectMode('chat')"
              >
                <div class="mode-name">通用模式</div>
                <div class="mode-desc">普通对话，可选择知识库</div>
              </div>
              <div 
                class="dropdown-item"
                :class="{ active: chatMode === 'agent' }"
                @click="selectMode('agent')"
              >
                <div class="mode-name">智能体调用</div>
                <div class="mode-desc">使用 @智能体名称 调用智能体</div>
              </div>
              <div 
                class="dropdown-item"
                :class="{ active: chatMode === 'test' }"
                @click="selectMode('test')"
              >
                <div class="mode-name">测试智能体</div>
                <div class="mode-desc">使用测试用例测试智能体</div>
              </div>
            </div>
          </div>
          <button v-if="isChatPage" class="btn-secondary header-btn" @click="handleNewChat">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
            </svg>
            新对话
          </button>
          <div v-if="isCodeToolsPage && !codeToolEditorState.show" class="code-tools-search-box">
            <svg viewBox="0 0 24 24" class="search-icon">
              <path fill="currentColor" d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
            </svg>
            <input 
              type="text" 
              v-model="codeToolsSearchQuery" 
              placeholder="搜索工具..."
              class="code-tools-search-input"
            />
          </div>
          <button v-if="isCodeToolsPage && !codeToolEditorState.show" class="btn-primary header-btn" @click="handleAddCodeTool">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
            </svg>
            新建工具
          </button>
          <template v-if="isCodeToolsPage && codeToolEditorState.show">
            <button v-if="codeToolEditorState.mode === 'editor'" class="btn-back" @click="handleCloseCodeToolEditor">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
              </svg>
            </button>
            <button v-if="codeToolEditorState.mode === 'test'" class="btn-back" @click="handleCloseCodeToolTest">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
              </svg>
            </button>
            <h3 v-if="codeToolEditorState.mode === 'editor'" class="editor-title">
              {{ codeToolEditorState.editingTool ? '编辑工具' : '新建工具' }}
            </h3>
            <h3 v-if="codeToolEditorState.mode === 'test'" class="test-title">
              测试运行: {{ codeToolEditorState.testingTool?.display_name || codeToolEditorState.testingTool?.name }}
            </h3>
          </template>
        </div>
        <div class="header-actions">
          <button class="help-btn" @click="showHelpCenter = true">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/>
            </svg>
          </button>
          <span class="welcome">欢迎，{{ displayUsername }}</span>
        </div>
      </header>
      
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>

  <!-- 智能体生成测试用例模态框 -->
  <div class="modal-overlay" v-if="showGenerateTestCaseModal" @click.self="!generatingTestCases && (showGenerateTestCaseModal = false)">
    <div class="modal">
      <div class="modal-header">
        <h3>智能体生成测试用例</h3>
        <button class="btn-close" @click="showGenerateTestCaseModal = false" :disabled="generatingTestCases">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
          </svg>
        </button>
      </div>
      <form @submit.prevent="generateTestCases" class="modal-body">
        <div v-if="generatingTestCases" class="loading-overlay">
          <div class="loading-spinner"></div>
          <p>正在生成测试用例，请稍候...</p>
        </div>
        <div v-else>
          <div class="form-group">
            <label>智能体名称（多个智能体用逗号分隔）</label>
            <input 
              type="text" 
              v-model="generateTestCaseForm.agentNames" 
              placeholder="例如: 吃货智能体, 旅游智能体"
              required
            />
          </div>
          <div class="form-group">
            <label>生成要求</label>
            <textarea 
              v-model="generateTestCaseForm.requirement" 
              placeholder="请描述测试用例的生成要求，例如：生成5个关于美食推荐的测试用例"
              rows="3"
            ></textarea>
          </div>
          <div class="form-group">
            <label>生成数量</label>
            <input 
              type="number" 
              v-model.number="generateTestCaseForm.count" 
              min="1" 
              max="20"
              value="5"
            />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showGenerateTestCaseModal = false">取消</button>
            <button type="submit" class="btn-primary">开始生成</button>
          </div>
        </div>
      </form>
    </div>
  </div>
  
  <div class="toast" v-if="toast.show" :class="toast.type">
    {{ toast.message }}
  </div>
  
  <!-- 帮助中心模态框 -->
  <div class="modal-overlay help-modal-overlay" v-if="showHelpCenter" @click.self="showHelpCenter = false">
    <div class="help-modal">
      <div class="help-modal-header">
        <h3>帮助中心</h3>
        <button class="btn-close" @click="showHelpCenter = false">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
          </svg>
        </button>
      </div>
      <div class="help-modal-body">
        <div class="help-sidebar">
          <div 
            v-for="section in helpSections" 
            :key="section.id"
            class="help-nav-item"
            :class="{ active: activeHelpSection === section.id }"
            @click="activeHelpSection = section.id"
          >
            <svg viewBox="0 0 24 24" class="help-nav-icon">
              <path fill="currentColor" :d="section.icon"/>
            </svg>
            <span>{{ section.title }}</span>
          </div>
        </div>
        <div class="help-content">
          <MarkdownRenderer :content="currentHelpContent" @link-click="onHelpLinkClick" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, provide, inject, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import axios from 'axios'

const route = useRoute()
const sidebarOpen = ref(true)
const addModelTrigger = ref(0)
const addAgentTrigger = ref(0)
const addWorkflowAgentTrigger = ref(0)
const agentSearchQuery = ref('')
const codeToolsSearchQuery = ref('')
const addKBTrigger = ref(0)
const selectedKBName = ref(null)
const backToKBList = ref(0)
const addTestCaseFolderTrigger = ref(0)
const selectedTestCaseFolder = ref(null)
const backToTestCaseFolderList = ref(0)
const importFromKBTrigger = ref(0)
const addTestCaseTrigger = ref(0)
const addCodeToolTrigger = ref(0)
const newChatTrigger = ref(0)
const selectedResultAgent = ref(null)
const selectedResultFolder = ref(null)
const backToResultAgentList = ref(0)
const backToResultFolderList = ref(0)
const models = ref([])
const selectedModel = ref(null)
const showModelDropdown = ref(false)
const showModeDropdown = ref(false)
const modelDropdownStyle = ref({})
const modeDropdownStyle = ref({})
const modelButtonRef = ref(null)
const modeButtonRef = ref(null)
const chatMode = ref('chat')
const modeLabels = {
  chat: '通用模式',
  agent: '智能体调用',
  test: '测试智能体'
}
const chatTitle = ref('')
const currentChatId = ref(null)
const editingTitle = ref(false)
const editingTitleText = ref('')
const titleInput = ref(null)
const chatHistory = ref([])

// 智能体生成测试用例相关
const showGenerateTestCaseModal = ref(false)
const generatingTestCases = ref(false)
const generateTestCaseForm = ref({
  agentNames: '',
  requirement: '',
  count: 5
})
const refreshTestCasesTrigger = ref(0)
const toast = ref({ show: false, message: '', type: 'success' })
const exporting = ref(false)

// 帮助中心相关
const showHelpCenter = ref(false)
const activeHelpSection = ref('platform-intro')
const helpSections = [
  {
    id: 'platform-intro',
    title: '平台介绍',
    icon: 'M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z'
  },
  {
    id: 'workflow-language',
    title: '工作流语言',
    icon: 'M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z'
  },
  {
    id: 'code-tool',
    title: '代码工具',
    icon: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M10,19L12,15H9V10H15V15L13,19H10Z'
  },
  {
    id: 'faq',
    title: '常见问题',
    icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z'
  }
]

const helpContentModules = import.meta.glob('../assets/help-content/*.md', { eager: true, query: '?raw', import: 'default' })

const helpContentMap = {}
Object.entries(helpContentModules).forEach(([path, content]) => {
  const fileName = path.split('/').pop().replace('.md', '')
  helpContentMap[fileName] = content
})

const currentHelpContent = computed(() => {
  return helpContentMap[activeHelpSection.value] || ''
})

const onHelpLinkClick = (sectionId) => {
  if (helpContentMap[sectionId]) {
    activeHelpSection.value = sectionId
  }
}

const hasMessages = ref(false)
provide('hasMessages', hasMessages)

provide('chatTitle', chatTitle)
provide('selectedModel', selectedModel)
provide('addModelTrigger', addModelTrigger)
provide('addAgentTrigger', addAgentTrigger)
provide('addWorkflowAgentTrigger', addWorkflowAgentTrigger)
provide('agentSearchQuery', agentSearchQuery)
provide('addKBTrigger', addKBTrigger)
provide('selectedKBName', selectedKBName)
provide('backToKBList', backToKBList)
provide('currentChatId', currentChatId)
provide('addTestCaseFolderTrigger', addTestCaseFolderTrigger)
provide('selectedTestCaseFolder', selectedTestCaseFolder)
provide('backToTestCaseFolderList', backToTestCaseFolderList)
provide('importFromKBTrigger', importFromKBTrigger)
provide('addTestCaseTrigger', addTestCaseTrigger)
provide('newChatTrigger', newChatTrigger)
provide('chatHistory', chatHistory)
provide('chatMode', chatMode)
provide('selectedResultAgent', selectedResultAgent)
provide('selectedResultFolder', selectedResultFolder)
provide('backToResultAgentList', backToResultAgentList)
provide('backToResultFolderList', backToResultFolderList)
provide('refreshTestCasesTrigger', refreshTestCasesTrigger)
provide('codeToolsSearchQuery', codeToolsSearchQuery)
provide('addCodeToolTrigger', addCodeToolTrigger)

const updateChatHistory = (updatedChat) => {
  const index = chatHistory.value.findIndex(c => c.id === updatedChat.id)
  if (index !== -1) {
    chatHistory.value[index] = { ...chatHistory.value[index], ...updatedChat }
  }
}

provide('chatHistoryUpdate', updateChatHistory)

const username = computed(() => localStorage.getItem('username') || 'User')
const displayUsername = computed(() => {
  const name = username.value
  return name.length > 9 ? name.slice(0, 9) + '...' : name
})

const isApiConfigPage = computed(() => route.path === '/dashboard/api-config')
const isAgentsPage = computed(() => route.path === '/dashboard/agents')
const isKnowledgeBasePage = computed(() => route.path === '/dashboard/knowledge-base')
const isTestCasesPage = computed(() => route.path === '/dashboard/test-cases')
const isChatPage = computed(() => route.path === '/dashboard' || route.path === '/dashboard/home')
const isTestResultsPage = computed(() => route.path === '/dashboard/test-results')
const isCodeToolsPage = computed(() => route.path === '/dashboard/code-tools')

// CodeTools 编辑器和测试面板状态
const codeToolEditorState = ref({
  show: false,
  mode: 'editor', // 'editor' 或 'test'
  editingTool: null,
  testingTool: null
})

provide('codeToolEditorState', codeToolEditorState)

const basePageTitle = computed(() => {
  if (isCodeToolsPage.value && codeToolEditorState.value.show) {
    return ''
  }
  
  if (route.path === '/dashboard/test-results') {
    const agentName = selectedResultAgent.value?.agent_name || ''
    const truncatedAgentName = agentName.length > 6 ? agentName.slice(0, 6) + '...' : agentName
    const folder_name = selectedResultFolder.value?.folder_name || ''
    const truncatedFolderName = folder_name.length > 6 ? folder_name.slice(0, 6) + '...' : folder_name
    if (selectedResultFolder.value) {
      return `测试结果 / ${truncatedAgentName} / ${truncatedFolderName}`
    }
    if (selectedResultAgent.value) {
      return `测试结果 / ${truncatedAgentName}`
    }
    return '测试结果'
  }
  const folder_name = selectedTestCaseFolder.value?.name || ''
  const truncatedFolderName = folder_name.length > 6 ? folder_name.slice(0, 6) + '...' : folder_name
  const KBName = selectedKBName.value || ''
  const truncatedKBName = KBName.length > 6 ? KBName.slice(0, 6) + '...' : KBName
  const titles = {
    '/dashboard': '对话',
    '/dashboard/home': '对话',
    '/dashboard/api-config': '模型 API',
    '/dashboard/agents': '智能体管理',
    '/dashboard/knowledge-base': selectedKBName.value ? `知识库 / ${truncatedKBName}` : '知识库',
    '/dashboard/test-cases': selectedTestCaseFolder.value ? `测试用例 / ${truncatedFolderName}` : '测试用例',
    '/dashboard/code-tools': '代码工具'
  }
  return titles[route.path] || '对话'
})

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

const loadModels = async () => {
  try {
    const response = await axios.get('/api/api-config')
    models.value = response.data
    const defaultModel = models.value.find(m => m.is_default)
    if (defaultModel) {
      selectedModel.value = defaultModel
    } else if (models.value.length > 0) {
      selectedModel.value = models.value[0]
    }
  } catch (error) {
    console.error('Failed to load models:', error)
  }
}

const selectModel = (model) => {
  selectedModel.value = model
  showModelDropdown.value = false
}

const selectMode = (mode) => {
  if (hasMessages.value) {
    return
  }
  chatMode.value = mode
  showModeDropdown.value = false
}

const toggleModelDropdown = () => {
  showModelDropdown.value = !showModelDropdown.value
  if (showModelDropdown.value) {
    nextTick(() => {
      const btn = modelButtonRef.value
      if (btn) {
        const rect = btn.getBoundingClientRect()
        modelDropdownStyle.value = {
          top: `${rect.bottom + 8}px`,
          left: `${rect.left}px`
        }
      }
    })
  }
}

const toggleModeDropdown = () => {
  showModeDropdown.value = !showModeDropdown.value
  if (showModeDropdown.value) {
    nextTick(() => {
      const btn = modeButtonRef.value
      if (btn) {
        const rect = btn.getBoundingClientRect()
        modeDropdownStyle.value = {
          top: `${rect.bottom + 8}px`,
          left: `${rect.left}px`
        }
      }
    })
  }
}

const truncateTitle = (title) => {
  if (!title) return ''
  return title.length > 8 ? title.slice(0, 8) + '...' : title
}

const startEditTitle = () => {
  if (!isChatPage.value || !chatTitle.value) return
  editingTitleText.value = chatTitle.value
  editingTitle.value = true
  nextTick(() => {
    titleInput.value?.focus()
    titleInput.value?.select()
  })
}

const saveTitle = async () => {
  if (!editingTitle.value) return
  
  const newTitle = editingTitleText.value.trim()
  if (newTitle && newTitle !== chatTitle.value && currentChatId.value) {
    try {
      await axios.put(`/api/conversations/${currentChatId.value}`, { title: newTitle })
      chatTitle.value = newTitle
      updateChatHistory({ id: currentChatId.value, title: newTitle })
    } catch (error) {
      console.error('Failed to update title:', error)
    }
  }
  editingTitle.value = false
}

const cancelEditTitle = () => {
  editingTitle.value = false
  editingTitleText.value = ''
}

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const handleNavigate = () => {
  if (route.path === '/dashboard/knowledge-base') {
    selectedKBName.value = null
  }
  if (route.path === '/dashboard/test-cases') {
    selectedTestCaseFolder.value = null
  }
}

const handleAddModel = () => {
  addModelTrigger.value++
}

const handleAddAgent = () => {
  addAgentTrigger.value++
}

const handleAddWorkflowAgent = () => {
  addWorkflowAgentTrigger.value++
}

const handleAddKB = () => {
  addKBTrigger.value++
}

const handleBackToKBList = () => {
  backToKBList.value++
}

const handleAddTestCaseFolder = () => {
  addTestCaseFolderTrigger.value++
}

const handleBackToTestCaseFolderList = () => {
  backToTestCaseFolderList.value++
}

const handleImportFromKB = () => {
  importFromKBTrigger.value++
}

const handleAddTestCase = () => {
  addTestCaseTrigger.value++
}

const handleNewChat = () => {
  newChatTrigger.value++
}

const handleAddCodeTool = () => {
  addCodeToolTrigger.value++
}

const handleCloseCodeToolEditor = () => {
  codeToolEditorState.value.show = false
  codeToolEditorState.value.mode = 'editor'
  codeToolEditorState.value.editingTool = null
}

const handleCloseCodeToolTest = () => {
  codeToolEditorState.value.show = false
  codeToolEditorState.value.mode = 'test'
  codeToolEditorState.value.testingTool = null
}

const handleBackToResultAgentList = () => {
  backToResultAgentList.value++
}

const handleBackToResultFolderList = () => {
  backToResultFolderList.value++
}

const handleExportTestResults = async () => {
  if (!selectedResultAgent.value || !selectedResultFolder.value) {
    alert('请先选择智能体和文件夹')
    return
  }
  
  exporting.value = true
  
  try {
    const response = await axios.get(
      `/api/test-chat/test-results/${selectedResultAgent.value.agent_id}/folder/${selectedResultFolder.value.folder_id}/export`,
      { responseType: 'blob' }
    )
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const a = document.createElement('a')
    a.href = url
    const folderName = selectedResultFolder.value.folder_name || '测试结果'
    const agentName = selectedResultAgent.value.agent_name || '智能体'
    a.download = `测试结果_${agentName}_${folderName}.xlsx`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (error) {
    console.error('Failed to export test results:', error)
    alert('导出失败')
  } finally {
    exporting.value = false
  }
}

const generateTestCases = async () => {
  if (!generateTestCaseForm.value.agentNames.trim()) {
    alert('请输入智能体名称')
    return
  }
  
  if (!selectedTestCaseFolder.value) {
    alert('请先选择测试用例文件夹')
    return
  }
  
  generatingTestCases.value = true
  
  try {
    const agentNames = generateTestCaseForm.value.agentNames
      .split(',')
      .map(name => name.trim())
      .filter(name => name)
    
    const requestData = {
      agent_names: agentNames,
      requirement: generateTestCaseForm.value.requirement,
      count: generateTestCaseForm.value.count
    }
    
    if (selectedTestCaseFolder.value && selectedTestCaseFolder.value.id) {
      requestData.folder_id = selectedTestCaseFolder.value.id.toString()
    }
    
    const response = await axios.post('/api/test-chat/generate-test-case', requestData)
    
    // 重置表单
    generateTestCaseForm.value = {
      agentNames: '',
      requirement: '',
      count: 5
    }
    
    // 等待一段时间后刷新测试用例列表（后台任务需要时间）
    setTimeout(() => {
      refreshTestCasesTrigger.value++
    }, 2000)
    
    showToast('测试用例生成任务已开始，请稍候查看结果', 'success')
  } catch (error) {
    console.error('Failed to generate test cases:', error)
    console.error('Error details:', {
      message: error.message,
      response: error.response ? {
        status: error.response.status,
        data: error.response.data
      } : null,
      request: error.request ? error.request.url : null
    })
    
    let errorMessage = '生成测试用例失败，请稍后重试'
    if (error.response) {
      if (error.response.status === 422) {
        errorMessage = `参数错误: ${JSON.stringify(error.response.data.detail || error.response.data)}`
      } else if (error.response.status === 404) {
        errorMessage = '接口未找到，请检查后端服务是否正常运行'
      } else if (error.response.status === 500) {
        errorMessage = '服务器内部错误，请检查后端日志'
      } else {
        errorMessage = `请求失败 (${error.response.status}): ${error.response.data.message || '未知错误'}`
      }
    } else if (error.request) {
      errorMessage = '无法连接到服务器，请检查网络连接'
    }
    
    showToast(errorMessage, 'error')
  } finally {
    generatingTestCases.value = false
    showGenerateTestCaseModal.value = false
  }
}

watch(() => route.path, (newPath) => {
  if (newPath === '/dashboard/knowledge-base') {
    selectedKBName.value = null
  }
  if (newPath === '/dashboard/test-cases') {
    selectedTestCaseFolder.value = null
  }
  if (newPath === '/dashboard/test-results') {
    selectedResultAgent.value = null
    selectedResultFolder.value = null
  }
})

watch(showModelDropdown, (val) => {
  if (val) {
    document.addEventListener('click', closeDropdownOnClickOutside)
  } else {
    document.removeEventListener('click', closeDropdownOnClickOutside)
  }
})

watch(showModeDropdown, (val) => {
  if (val) {
    document.addEventListener('click', closeModeDropdownOnClickOutside)
  } else {
    document.removeEventListener('click', closeModeDropdownOnClickOutside)
  }
})

const closeDropdownOnClickOutside = (e) => {
  if (!e.target.closest('.model-selector')) {
    showModelDropdown.value = false
  }
}

const closeModeDropdownOnClickOutside = (e) => {
  if (!e.target.closest('.mode-selector')) {
    showModeDropdown.value = false
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  min-height: 100vh;
  background: #f5f7fa;
  overflow: hidden;
}

.main-content {
  flex: 1;
  margin-left: 260px;
  transition: margin-left 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.main-content.expanded {
  margin-left: 0;
}

.top-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  z-index: 100;
  padding-left: 24px;
  transition: padding-left 0.3s ease;
  flex-shrink: 0;
  overflow-x: auto;
  overflow-y: visible;
  -webkit-overflow-scrolling: touch;
}

.top-header::-webkit-scrollbar {
  height: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
  min-width: max-content;
}

.main-content.expanded .top-header {
  padding-left: 80px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.chat-title {
  font-size: 20px;
  font-weight: 600;
  color: #667eea;
}

.chat-title.clickable {
  cursor: pointer;
  padding: 4px 8px;
  margin: -4px -8px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.chat-title.clickable:hover {
  background-color: rgba(102, 126, 234, 0.1);
}

.title-input {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  padding: 4px 8px;
  border: 2px solid #667eea;
  border-radius: 6px;
  outline: none;
  background: #fff;
  min-width: 200px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.agent-search-box {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 0 12px;
  height: 36px;
  transition: all 0.2s;
}

.agent-search-box:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.agent-search-box .search-icon {
  width: 18px;
  height: 18px;
  color: #999;
  flex-shrink: 0;
}

.agent-search-input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: #333;
  width: 160px;
  margin-left: 8px;
}

.agent-search-input::placeholder {
  color: #aaa;
}

.code-tools-search-box {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 0 12px;
  height: 36px;
  transition: all 0.2s;
}

.code-tools-search-box:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.code-tools-search-box .search-icon {
  width: 18px;
  height: 18px;
  color: #999;
  flex-shrink: 0;
}

.code-tools-search-input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: #333;
  width: 160px;
  margin-left: 8px;
}

.code-tools-search-input::placeholder {
  color: #aaa;
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 16px;
}

.welcome {
  color: #666;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.btn-add {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-add svg {
  width: 22px;
  height: 22px;
}

.header-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.header-btn svg {
  width: 16px;
  height: 16px;
}

.btn-primary.header-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
}

.btn-primary.header-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary.header-btn {
  background: #fff;
  color: #666;
  border: 1px solid #e0e0e0;
}

.btn-secondary.header-btn:hover {
  background: #f5f5f5;
  border-color: #ccc;
}

.btn-back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  background: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 12px;
}

.btn-back:hover {
  background: #e5e5e5;
  color: #333;
}

.btn-back svg {
  width: 22px;
  height: 22px;
}

.editor-title, .test-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.content-area {
  flex: 1;
  padding: 24px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overscroll-behavior: none;
}

.content-area:has(.chat-container) {
  padding: 0;
  overflow: hidden;
}

.model-selector {
  position: relative;
}

.model-select-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: #f5f7fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.model-select-btn:hover {
  background: #eee;
  border-color: #667eea;
}

.model-icon {
  width: 18px;
  height: 18px;
  color: #667eea;
}

.dropdown-icon {
  width: 18px;
  height: 18px;
  color: #999;
}

.model-dropdown {
  position: fixed;
  min-width: 220px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  overflow: hidden;
}

.dropdown-empty {
  padding: 16px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.dropdown-item {
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.dropdown-item:hover {
  background: #f5f7fa;
}

.dropdown-item.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
}

.model-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.model-code {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.mode-selector {
  position: relative;
}

.mode-select-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: #f5f7fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.mode-select-btn:hover {
  background: #eee;
  border-color: #764ba2;
}

.mode-select-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.mode-select-btn.disabled:hover {
  background: #f5f7fa;
  border-color: #e0e0e0;
}

.mode-icon {
  width: 18px;
  height: 18px;
  color: #764ba2;
}

.mode-dropdown {
  position: fixed;
  min-width: 200px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  overflow: hidden;
}

.mode-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.mode-desc {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #fff;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}

.btn-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: background 0.2s;
}

.btn-close:hover {
  background: #f5f5f5;
}

.btn-close svg {
  width: 20px;
  height: 20px;
  color: #666;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.modal-actions button {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-actions .btn-secondary {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #e0e0e0;
}

.modal-actions .btn-secondary:hover {
  background: #e5e5e5;
}

.modal-actions .btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
}

.modal-actions .btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.modal-actions .btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-overlay p {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  animation: fadeInUp 0.3s ease;
}

.toast.success {
  background: #10b981;
}

.toast.error {
  background: #ef4444;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translate(-50%, 20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

.help-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.help-btn:hover {
  background: #f5f5f5;
  color: #667eea;
}

.help-btn svg {
  width: 20px;
  height: 20px;
}

.help-modal-overlay {
  z-index: 2000;
}

.help-modal {
  background: #fff;
  border-radius: 16px;
  width: 90%;
  max-width: 1000px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.help-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.help-modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
}

.help-modal-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.help-sidebar {
  width: 200px;
  background: #f5f7fa;
  border-right: 1px solid #e0e0e0;
  padding: 16px 12px;
  overflow-y: auto;
  flex-shrink: 0;
}

.help-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  color: #666;
  cursor: pointer;
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.2s;
  font-size: 14px;
}

.help-nav-item:hover {
  background: #fff;
  color: #333;
}

.help-nav-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.help-nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.help-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.help-content :deep(.md-editor) {
  max-width: 800px;
}
</style>
