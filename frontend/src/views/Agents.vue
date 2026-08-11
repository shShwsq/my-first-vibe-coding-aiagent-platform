<template>
  <div class="agents-page">
    <div class="section-title">API 智能体</div>
    <div class="agents-list" v-if="filteredAgents.length > 0">
      <div 
        v-for="agent in filteredAgents" 
        :key="agent.id" 
        class="agent-card"
        :class="{ 'is-inactive': !agent.is_active }"
      >
        <div class="agent-header">
          <div class="agent-info">
            <h3>{{ agent.name }}</h3>
            <span class="agent-status" :class="{ active: agent.is_active }">
              {{ agent.is_active ? '启用' : '禁用' }}
            </span>
          </div>
          <div class="agent-actions">
            <button class="btn-icon" @click="openCodeEditor(agent)" title="编辑代码">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z"/>
              </svg>
            </button>
            <button class="btn-icon" @click="openModal(agent)" title="编辑">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
              </svg>
            </button>
            <button class="btn-icon delete" @click="deleteAgent(agent)" title="删除">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="agent-details">
          <div class="detail-item">
            <span class="label">API URL:</span>
            <span class="value">{{ truncateUrl(agent.api_url) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">API Key:</span>
            <span class="value masked">{{ maskApiKey(agent.api_key) }}</span>
          </div>
          <div class="detail-item" v-if="agent.description">
            <span class="label">描述:</span>
            <span class="value">{{ agent.description }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="loading-state" v-else-if="loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div class="empty-state" v-else>
      <svg viewBox="0 0 24 24">
        <path fill="currentColor" d="M12,2A2,2 0 0,1 14,4A2,2 0 0,1 12,6A2,2 0 0,1 10,4A2,2 0 0,1 12,2M21,9H15V22H13V16H11V22H9V9H3V7H21V9Z"/>
      </svg>
      <h3>暂无API智能体</h3>
      <p>点击上方"+"按钮添加您的第一个智能体</p>
    </div>

    <div class="section-title workflow-section-title">工作流智能体</div>
    <div class="agents-list" v-if="filteredWorkflowAgents.length > 0">
      <div 
        v-for="agent in filteredWorkflowAgents" 
        :key="agent.id" 
        class="agent-card workflow-agent-card"
        :class="{ 'is-inactive': !agent.is_active }"
      >
        <div class="agent-header">
          <div class="agent-info">
            <h3>{{ agent.name }}</h3>
            <span class="agent-status" :class="{ active: agent.is_active }">
              {{ agent.is_active ? '启用' : '禁用' }}
            </span>
          </div>
          <div class="agent-actions">
            <button class="btn-icon workflow-btn" @click="openWorkflowEditor(agent)" title="编写工作流">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z"/>
              </svg>
            </button>
            <button class="btn-icon" @click="openWorkflowModal(agent)" title="编辑">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
              </svg>
            </button>
            <button class="btn-icon" @click="clearLongMemory(agent)" title="清除永久记忆">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M12,2C6.47,2 2,6.47 2,12C2,17.53 6.47,22 12,22C17.53,22 22,17.53 22,12C22,6.47 17.53,2 12,2M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M15.54,8.46L14.13,7.05L12,9.17L9.88,7.05L8.46,8.46L10.59,10.59L8.46,12.71L9.88,14.13L12,12L14.13,14.13L15.54,12.71L13.42,10.59L15.54,8.46Z"/>
              </svg>
            </button>
            <button class="btn-icon delete" @click="deleteWorkflowAgent(agent)" title="删除">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="agent-details">
          <div class="detail-item" v-if="agent.description">
            <span class="label">描述:</span>
            <span class="value">{{ agent.description }}</span>
          </div>
          <div class="detail-item" v-if="agent.workflow_code">
            <span class="label">工作流:</span>
            <span class="value code-preview">{{ getWorkflowPreview(agent.workflow_code) }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="loading-state" v-else-if="loadingWorkflow">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div class="empty-state" v-else>
      <svg viewBox="0 0 24 24">
        <path fill="currentColor" d="M12,2A2,2 0 0,1 14,4A2,2 0 0,1 12,6A2,2 0 0,1 10,4A2,2 0 0,1 12,2M21,9H15V22H13V16H11V22H9V9H3V7H21V9Z"/>
      </svg>
      <h3>暂无工作流智能体</h3>
      <p>点击上方"新建工作流智能体"按钮添加</p>
    </div>

    <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
      <div class="modal agent-modal">
        <div class="modal-header">
          <h3>{{ editingAgent ? '编辑智能体' : '添加智能体' }}</h3>
          <button class="btn-close" @click="closeModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveAgent" class="modal-body">
          <div class="form-group">
            <label>智能体名称</label>
            <input 
              type="text" 
              v-model="formData.name" 
              placeholder="例如: 天气查询智能体"
              required
            />
            <span class="form-hint">名称需要唯一，不能与已有智能体重复</span>
          </div>
          
          <div class="form-group">
            <label>API URL</label>
            <input 
              type="text" 
              v-model="formData.api_url" 
              placeholder="例如: https://api.example.com/v1/chat"
              required
            />
          </div>
          
          <div class="form-group">
            <label>API Key</label>
            <div class="input-wrapper">
              <input 
                :type="showApiKey ? 'text' : 'password'" 
                v-model="formData.api_key" 
                placeholder="输入 API Key"
                required
              />
              <button type="button" class="toggle-visibility" @click="showApiKey = !showApiKey">
                <svg viewBox="0 0 24 24">
                  <path v-if="showApiKey" fill="currentColor" d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z"/>
                  <path v-else fill="currentColor" d="M11.83,9L15,12.16C15,12.11 15,12.05 15,12A3,3 0 0,0 12,9C11.94,9 11.89,9 11.83,9M7.53,9.8L9.08,11.35C9.03,11.56 9,11.77 9,12A3,3 0 0,0 12,15C12.22,15 12.44,14.97 12.65,14.92L14.2,16.47C13.53,16.8 12.79,17 12,17A5,5 0 0,1 7,12C7,11.21 7.2,10.47 7.53,9.8M2,4.27L4.28,6.55L4.73,7C2.08,9.3 0.46,12.46 0,12C0.77,14.77 2.39,17.17 4.55,18.94L2,21.5H8V15.5L5.89,17.61C4.16,16.07 2.86,14.12 2.2,12C2.86,9.88 4.16,7.93 5.89,6.39L8,8.5V2.5H2M16,12A5,5 0 0,0 12,7C11.21,7 10.47,7.2 9.8,7.53L8.25,5.98C8.92,5.66 9.66,5.46 10.4,5.37L12,2L13.59,5.36C16.27,5.73 18.5,7.56 19.43,10.04C19.46,10.06 19.5,10.09 19.53,10.12L21.71,8.94L20.29,11.35L21.71,13.76L19.53,12.58C19.5,12.61 19.46,12.64 19.43,12.66C18.5,15.14 16.27,16.95 13.59,17.32L12,20.66L10.41,17.31C9.67,17.22 8.92,17.02 8.25,16.7L9.8,15.15C10.47,15.47 11.21,15.67 12,15.67A5,5 0 0,0 17,12.16L16.84,12L17,11.84Z"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div class="form-group">
            <label>调用参数示例</label>
            <textarea 
              v-model="formData.call_params_example" 
              placeholder='例如: {"message": "你好", "user_id": "123"}'
              rows="4"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label>描述 (可选)</label>
            <textarea 
              v-model="formData.description" 
              placeholder="智能体功能描述"
              rows="2"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label>响应格式</label>
            <select v-model="formData.response_type" class="form-select">
              <option value="non_stream">非流式响应</option>
              <option value="stream">流式响应</option>
            </select>
          </div>
          
          <div class="form-group checkbox">
            <label>
              <input type="checkbox" v-model="formData.is_active" />
              启用智能体
            </label>
          </div>
          
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeModal">取消</button>
            <button type="button" class="btn-secondary" @click="generateCode" :disabled="generatingCode">
              {{ generatingCode ? '生成中...' : (formData.call_code ? '重新生成代码' : '生成代码') }}
            </button>
            <button type="submit" class="btn-primary" :disabled="generatingCode">
              {{ generatingCode ? '生成代码中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div class="modal-overlay" v-if="showCodeEditor" @click.self="closeCodeEditor">
      <div class="modal code-editor-modal">
        <div class="modal-header">
          <h3>编辑调用代码 - {{ currentAgent?.name }}</h3>
          <button class="btn-close" @click="closeCodeEditor">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="code-editor-container">
            <div class="editor-header">
              <span class="file-name">call_agent 函数</span>
              <div class="editor-actions">
                <button class="btn-small" @click="formatCode" title="格式化代码">
                  <svg viewBox="0 0 24 24">
                    <path fill="currentColor" d="M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z"/>
                  </svg>
                </button>
              </div>
            </div>
            <textarea 
              v-model="codeContent" 
              class="code-editor"
              spellcheck="false"
            ></textarea>
          </div>
          
          <div class="test-section">
            <div class="test-input-row">
              <h4>测试调用</h4>
              <div class="test-message-input">
                <input 
                  type="text" 
                  v-model="testMessage" 
                  placeholder="输入测试消息（默认：你好）"
                />
              </div>
            </div>
            <div class="test-kwargs-section">
              <label>额外参数 (kwargs, JSON格式)</label>
              <textarea 
                v-model="testKwargs" 
                placeholder='例如: {"user_id": "123", "temperature": 0.7}'
                rows="3"
                class="kwargs-input"
              ></textarea>
              <small class="form-hint">这些参数将作为 **kwargs 传递给 call_agent 函数</small>
            </div>
            <h4>测试结果</h4>
            <div class="test-result" :class="testResult?.success ? 'success' : 'error'" v-if="testResult">
              <div class="result-header" v-if="testResult.success && testResult.result?.type">
                <span class="result-type">响应类型: {{ testResult.result.type }}</span>
                <span class="result-content-label" v-if="testResult.result.content">内容摘要:</span>
              </div>
              <div class="result-content" v-if="testResult.success && testResult.result?.content">
                <pre>{{ testResult.result.content }}</pre>
              </div>
              <div class="result-full">
                <pre>{{ testResult.success ? JSON.stringify(testResult.result, null, 2) : testResult.error }}</pre>
              </div>
            </div>
            <div class="test-result empty" v-else>
              <p>点击"测试调用"按钮运行代码</p>
            </div>
            
            <div class="extract-config-section" v-if="showExtractConfig">
              <h4>响应提取配置</h4>
              <div class="form-group">
                <textarea 
                  v-model="extractConfig" 
                  placeholder='JSON格式，如: {"type": "openai_chat"} 或 {"path": "choices[0].message.content"}'
                  rows="3"
                ></textarea>
                <small class="form-hint">
                  预设类型: openai_chat, openai_responses, anthropic, text<br>
                  自定义路径: {"path": "data.result.content"}
                </small>
              </div>
            </div>
          </div>
          
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeCodeEditor">取消</button>
            <button type="button" class="btn-secondary" @click="testCall" :disabled="testingCall">
              {{ testingCall ? '测试中...' : '测试调用' }}
            </button>
            <button type="button" class="btn-primary" @click="saveCode">保存代码</button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showWorkflowModal" @click.self="closeWorkflowModal">
      <div class="modal workflow-modal">
        <div class="modal-header">
          <h3>{{ editingWorkflowAgent ? '编辑工作流智能体' : '新建工作流智能体' }}</h3>
          <button class="btn-close" @click="closeWorkflowModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveWorkflowAgent" class="modal-body">
          <div class="form-group">
            <label>智能体名称</label>
            <input 
              type="text" 
              v-model="workflowFormData.name" 
              placeholder="例如: 数据处理工作流"
              required
            />
            <span class="form-hint">名称需要唯一，不能与已有智能体重复</span>
          </div>
          
          <div class="form-group">
            <label>描述 (可选)</label>
            <textarea 
              v-model="workflowFormData.description" 
              placeholder="工作流智能体功能描述"
              rows="3"
            ></textarea>
          </div>
          
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeWorkflowModal">取消</button>
            <button type="submit" class="btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>
    
    <div class="toast" v-if="toast.show" :class="toast.type">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const agents = ref([])
const loading = ref(true)
const showModal = ref(false)
const showCodeEditor = ref(false)
const showApiKey = ref(false)
const editingAgent = ref(null)
const currentAgent = ref(null)
const codeContent = ref('')
const testMessage = ref('')
const testKwargs = ref('')
const testResult = ref(null)
const extractConfig = ref('')
const toast = ref({ show: false, message: '', type: 'success' })
const generatingCode = ref(false)
const testingCall = ref(false)
const addAgentTrigger = inject('addAgentTrigger', ref(0))
const addWorkflowAgentTrigger = inject('addWorkflowAgentTrigger', ref(0))
const agentSearchQuery = inject('agentSearchQuery', ref(''))

const workflowAgents = ref([])
const loadingWorkflow = ref(true)
const showWorkflowModal = ref(false)
const editingWorkflowAgent = ref(null)

const workflowFormData = ref({
  name: '',
  description: ''
})

const filteredAgents = computed(() => {
  if (!agentSearchQuery.value.trim()) {
    return agents.value
  }
  const query = agentSearchQuery.value.toLowerCase().trim()
  return agents.value.filter(agent => 
    agent.name.toLowerCase().includes(query)
  )
})

const filteredWorkflowAgents = computed(() => {
  if (!agentSearchQuery.value.trim()) {
    return workflowAgents.value
  }
  const query = agentSearchQuery.value.toLowerCase().trim()
  return workflowAgents.value.filter(agent => 
    agent.name.toLowerCase().includes(query)
  )
})

const showExtractConfig = computed(() => {
  return testResult.value?.success && testResult.value?.response_type_detected === 'custom'
})

watch(addAgentTrigger, () => {
  if (addAgentTrigger.value > 0) {
    openModal()
  }
})

watch(addWorkflowAgentTrigger, () => {
  if (addWorkflowAgentTrigger.value > 0) {
    openWorkflowModal()
  }
})

const formData = ref({
  name: '',
  api_url: '',
  api_key: '',
  call_params_example: '',
  call_code: '',
  description: '',
  response_type: 'non_stream',
  is_active: true
})

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

const maskApiKey = (key) => {
  if (!key) return ''
  if (key.length <= 8) return '****'
  return key.substring(0, 4) + '****' + key.substring(key.length - 4)
}

const truncateUrl = (url) => {
  if (!url) return ''
  if (url.length <= 50) return url
  return url.substring(0, 47) + '...'
}

const loadAgents = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/agents')
    agents.value = response.data
  } catch (error) {
    console.error('Failed to load agents:', error)
  } finally {
    loading.value = false
  }
}

const loadWorkflowAgents = async () => {
  loadingWorkflow.value = true
  try {
    const response = await axios.get('/api/workflow-agents')
    workflowAgents.value = response.data
  } catch (error) {
    console.error('Failed to load workflow agents:', error)
  } finally {
    loadingWorkflow.value = false
  }
}

const getWorkflowPreview = (code) => {
  if (!code) return ''
  const lines = code.split('\n').slice(0, 3)
  return lines.join('\n') + (code.split('\n').length > 3 ? '...' : '')
}

const openWorkflowModal = (agent = null) => {
  editingWorkflowAgent.value = agent
  if (agent) {
    workflowFormData.value = {
      name: agent.name,
      description: agent.description || ''
    }
  } else {
    workflowFormData.value = {
      name: '',
      description: ''
    }
  }
  showWorkflowModal.value = true
}

const closeWorkflowModal = () => {
  showWorkflowModal.value = false
  editingWorkflowAgent.value = null
}

const saveWorkflowAgent = async () => {
  try {
    if (!workflowFormData.value.name || !workflowFormData.value.name.trim()) {
      showToast('请填写智能体名称', 'error')
      return
    }
    
    const checkResponse = await axios.get(`/api/workflow-agents/check-name/${encodeURIComponent(workflowFormData.value.name)}`, {
      params: { agent_id: editingWorkflowAgent.value?.id }
    })
    
    if (!checkResponse.data.available) {
      showToast(`工作流智能体名称 '${workflowFormData.value.name}' 已存在，请使用其他名称`, 'error')
      return
    }
    
    if (editingWorkflowAgent.value) {
      await axios.put(`/api/workflow-agents/${editingWorkflowAgent.value.id}`, workflowFormData.value)
      showToast('工作流智能体更新成功')
    } else {
      await axios.post('/api/workflow-agents', workflowFormData.value)
      showToast('工作流智能体创建成功')
    }
    closeWorkflowModal()
    loadWorkflowAgents()
  } catch (error) {
    const errorMsg = error.response?.data?.detail || '操作失败'
    showToast(errorMsg, 'error')
  }
}

const deleteWorkflowAgent = async (agent) => {
  if (!confirm(`确定要删除工作流智能体 "${agent.name}" 吗？`)) {
    return
  }
  
  try {
    await axios.delete(`/api/workflow-agents/${agent.id}`)
    showToast('删除成功')
    loadWorkflowAgents()
  } catch (error) {
    showToast('删除失败', 'error')
  }
}

const clearLongMemory = async (agent) => {
  if (!confirm(`确定要清除智能体 "${agent.name}" 的永久记忆吗？此操作不可撤销。`)) {
    return
  }
  
  try {
    await axios.post(`/api/workflow-agents/${agent.id}/clear-long-memory`)
    showToast('永久记忆已清除')
  } catch (error) {
    showToast('清除失败', 'error')
  }
}

const openWorkflowEditor = (agent) => {
  router.push(`/workflow-editor/${agent.id}`)
}

const openModal = (agent = null) => {
  editingAgent.value = agent
  if (agent) {
    formData.value = {
      name: agent.name,
      api_url: agent.api_url,
      api_key: agent.api_key,
      call_params_example: agent.call_params_example || '',
      call_code: agent.call_code || '',
      description: agent.description || '',
      response_type: agent.response_type || 'non_stream',
      is_active: agent.is_active
    }
  } else {
    formData.value = {
      name: '',
      api_url: '',
      api_key: '',
      call_params_example: '',
      call_code: '',
      description: '',
      response_type: 'non_stream',
      is_active: true
    }
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingAgent.value = null
}

const saveAgent = async () => {
  try {
    if (!formData.value.name || !formData.value.name.trim()) {
      showToast('请填写智能体名称', 'error')
      return
    }
    
    if (!formData.value.api_url || !formData.value.api_key || !formData.value.call_params_example) {
      showToast('请填写 API URL、API Key 和调用参数示例', 'error')
      return
    }
    
    const checkResponse = await axios.get(`/api/agents/check-name/${encodeURIComponent(formData.value.name)}`, {
      params: { agent_id: editingAgent.value?.id }
    })
    
    if (!checkResponse.data.available) {
      showToast(`智能体名称 '${formData.value.name}' 已存在，请使用其他名称`, 'error')
      return
    }
    
    if (!formData.value.call_code) {
      generatingCode.value = true
      try {
        const codeResponse = await axios.post('/api/agents/generate-code', {
          api_url: formData.value.api_url,
          api_key: formData.value.api_key,
          call_params_example: formData.value.call_params_example
        })
        formData.value.call_code = codeResponse.data.code
      } catch (error) {
        showToast(error.response?.data?.detail || '代码生成失败', 'error')
        generatingCode.value = false
        return
      } finally {
        generatingCode.value = false
      }
    }
    
    if (editingAgent.value) {
      await axios.put(`/api/agents/${editingAgent.value.id}`, formData.value)
      showToast('智能体更新成功')
    } else {
      await axios.post('/api/agents', formData.value)
      showToast('智能体创建成功')
    }
    closeModal()
    loadAgents()
  } catch (error) {
    const errorMsg = error.response?.data?.detail || '操作失败'
    showToast(errorMsg, 'error')
  }
}

const deleteAgent = async (agent) => {
  if (!confirm(`确定要删除智能体 "${agent.name}" 吗？`)) {
    return
  }
  
  try {
    await axios.delete(`/api/agents/${agent.id}`)
    showToast('删除成功')
    loadAgents()
  } catch (error) {
    showToast('删除失败', 'error')
  }
}

const generateCode = async () => {
  if (!formData.value.name || !formData.value.name.trim()) {
    showToast('请先填写智能体名称', 'error')
    return
  }
  
  if (!formData.value.api_url || !formData.value.api_key || !formData.value.call_params_example) {
    showToast('请先填写 API URL、API Key 和调用参数示例', 'error')
    return
  }
  
  try {
    const checkResponse = await axios.get(`/api/agents/check-name/${encodeURIComponent(formData.value.name)}`, {
      params: { agent_id: editingAgent.value?.id }
    })
    
    if (!checkResponse.data.available) {
      showToast(`智能体名称 '${formData.value.name}' 已存在，请使用其他名称`, 'error')
      return
    }
  } catch (error) {
    showToast('检查名称失败', 'error')
    return
  }
  
  generatingCode.value = true
  try {
    const response = await axios.post('/api/agents/generate-code', {
      api_url: formData.value.api_url,
      api_key: formData.value.api_key,
      call_params_example: formData.value.call_params_example
    })
    formData.value.call_code = response.data.code
    showToast('代码生成成功')
  } catch (error) {
    showToast(error.response?.data?.detail || '代码生成失败', 'error')
  } finally {
    generatingCode.value = false
  }
}

const openCodeEditor = (agent) => {
  currentAgent.value = agent
  codeContent.value = agent.call_code || getDefaultCode(agent)
  extractConfig.value = agent.response_extract_config || ''
  testMessage.value = ''
  testResult.value = null
  showCodeEditor.value = true
}

const closeCodeEditor = () => {
  showCodeEditor.value = false
  currentAgent.value = null
  testMessage.value = ''
  testResult.value = null
  extractConfig.value = ''
}

const getDefaultCode = (agent) => {
  return `import httpx
import json

def call_agent(api_key: str, message: str = "你好", **kwargs):
    """
    调用智能体API
    
    Args:
        api_key: API密钥
        message: 测试消息，默认为"你好"
        **kwargs: 其他参数
    
    Returns:
        API响应内容
    """
    url = "${agent.api_url}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 默认参数示例
    data = ${agent.call_params_example || '{}'}
    data.update(kwargs)
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"error": str(e)}
`
}

const testCall = async () => {
  testingCall.value = true
  testResult.value = null
  
  let kwargs = null
  if (testKwargs.value && testKwargs.value.trim()) {
    try {
      kwargs = JSON.parse(testKwargs.value)
    } catch (e) {
      testResult.value = {
        success: false,
        error: 'kwargs JSON 格式错误: ' + e.message
      }
      testingCall.value = false
      return
    }
  }
  
  try {
    const response = await axios.post('/api/agents/test-call', {
      call_code: codeContent.value,
      api_key: currentAgent.value.api_key,
      message: testMessage.value || '你好',
      response_type: currentAgent.value.response_type || 'non_stream',
      response_extract_config: extractConfig.value || null,
      kwargs: kwargs
    })
    testResult.value = response.data
    
    if (response.data.success && response.data.response_type_detected === 'custom' && response.data.raw_response) {
      try {
        const configResponse = await axios.post('/api/agents/generate-extract-config', {
          response_data: response.data.raw_response
        })
        
        if (configResponse.data.config) {
          extractConfig.value = configResponse.data.config
          showToast('已自动生成响应提取配置')
        }
      } catch (configError) {
        console.error('自动生成提取配置失败:', configError)
      }
    }
  } catch (error) {
    testResult.value = {
      success: false,
      error: error.response?.data?.detail || '测试调用失败'
    }
  } finally {
    testingCall.value = false
  }
}

const saveCode = async () => {
  try {
    await axios.put(`/api/agents/${currentAgent.value.id}`, {
      call_code: codeContent.value,
      response_extract_config: extractConfig.value || null
    })
    showToast('代码保存成功')
    closeCodeEditor()
    loadAgents()
  } catch (error) {
    showToast('保存失败', 'error')
  }
}

const formatCode = () => {
  try {
    const lines = codeContent.value.split('\n')
    const formatted = lines.map(line => line).join('\n')
    codeContent.value = formatted
    showToast('代码已格式化')
  } catch (error) {
    showToast('格式化失败', 'error')
  }
}

onMounted(() => {
  loadAgents()
  loadWorkflowAgents()
})
</script>

<style scoped>
.agents-page {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.agents-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.agent-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.agent-card.is-inactive {
  opacity: 0.7;
  border-color: #e0e0e0;
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.agent-info h3 {
  font-size: 18px;
  color: #1a1a2e;
  margin-bottom: 6px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  background: #f5f5f5;
  color: #999;
}

.agent-status.active {
  background: #e8f5e9;
  color: #4caf50;
}

.agent-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-icon svg {
  width: 18px;
  height: 18px;
  color: #666;
}

.btn-icon:hover {
  background: #667eea;
}

.btn-icon:hover svg {
  color: #fff;
}

.btn-icon.delete:hover {
  background: #f44336;
}

.agent-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-item .label {
  font-size: 13px;
  color: #999;
  min-width: 60px;
}

.detail-item .value {
  font-size: 13px;
  color: #333;
  word-break: break-all;
}

.detail-item .value.masked {
  font-family: monospace;
  color: #666;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.loading-state .loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-state p {
  color: #666;
  font-size: 14px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.empty-state svg {
  width: 80px;
  height: 80px;
  color: #ddd;
  margin-bottom: 20px;
}

.empty-state h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 8px;
}

.empty-state p {
  color: #999;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
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
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal.code-editor-modal {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  font-size: 18px;
  color: #1a1a2e;
}

.btn-close {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
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
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.form-group input[type="text"],
.form-group input[type="password"],
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
}

.form-hint {
  display: block;
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}

.form-group textarea {
  resize: vertical;
  font-family: 'Consolas', 'Monaco', monospace;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  padding-right: 44px;
}

.toggle-visibility {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-visibility svg {
  width: 20px;
  height: 20px;
  color: #999;
}

.form-group.checkbox label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.form-group.checkbox input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.btn-primary,
.btn-secondary {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #f5f7fa;
  color: #333;
  border: 1px solid #e0e0e0;
}

.btn-secondary:hover {
  background: #e8e8e8;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.code-editor-container {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e0e0e0;
}

.file-name {
  font-size: 13px;
  color: #666;
  font-family: 'Consolas', 'Monaco', monospace;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.btn-small {
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-small:hover {
  background: #e0e0e0;
}

.btn-small svg {
  width: 16px;
  height: 16px;
  color: #666;
}

.code-editor {
  width: 100%;
  min-height: 300px;
  padding: 16px;
  border: none;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  background: #fafafa;
}

.code-editor:focus {
  outline: none;
  background: #fff;
}

.test-section {
  margin-bottom: 20px;
}

.test-section h4 {
  font-size: 14px;
  color: #333;
  margin-bottom: 12px;
}

.test-input-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.test-input-row h4 {
  margin-bottom: 0;
  white-space: nowrap;
}

.test-message-input {
  flex: 1;
}

.test-message-input input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
}

.test-kwargs-section {
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.test-kwargs-section label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #555;
  margin-bottom: 8px;
}

.kwargs-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
  resize: vertical;
  background: #fff;
}

.kwargs-input:focus {
  outline: none;
  border-color: #667eea;
}

.test-kwargs-section .form-hint {
  margin-top: 6px;
  font-size: 11px;
  color: #888;
}

.test-message-input input:focus {
  outline: none;
  border-color: #667eea;
}

.test-result {
  padding: 16px;
  border-radius: 8px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  max-height: 300px;
  overflow-y: auto;
}

.test-result.success {
  background: #e8f5e9;
  border: 1px solid #c8e6c9;
}

.test-result.error {
  background: #ffebee;
  border: 1px solid #ffcdd2;
}

.test-result.empty {
  background: #f5f7fa;
  border: 1px solid #e0e0e0;
  text-align: center;
}

.test-result.empty p {
  color: #999;
}

.result-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #a5d6a7;
}

.result-type {
  font-weight: bold;
  color: #2e7d32;
  font-size: 14px;
}

.result-content-label {
  font-size: 12px;
  color: #388e3c;
}

.result-content {
  background: #fff;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  border: 1px solid #c8e6c9;
}

.result-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: #1b5e20;
  font-size: 14px;
  line-height: 1.5;
}

.result-full {
  background: rgba(0, 0, 0, 0.05);
  padding: 12px;
  border-radius: 6px;
}

.test-result pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.extract-config-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.extract-config-section h4 {
  font-size: 14px;
  color: #333;
  margin: 0 0 12px 0;
}

.extract-config-section .form-group {
  margin-bottom: 0;
}

.extract-config-section textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  resize: vertical;
}

.extract-config-section textarea:focus {
  outline: none;
  border-color: #667eea;
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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #667eea;
}

.workflow-section-title {
  margin-top: 32px;
}

.workflow-agent-card {
  border-left: 4px solid #764ba2;
}

.btn-icon.workflow-btn {
  background: #f0e6ff;
}

.btn-icon.workflow-btn:hover {
  background: #764ba2;
}

.btn-icon.workflow-btn svg {
  color: #764ba2;
}

.btn-icon.workflow-btn:hover svg {
  color: #fff;
}

.code-preview {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  color: #666;
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
}

.workflow-modal {
  max-width: 450px;
}
</style>
