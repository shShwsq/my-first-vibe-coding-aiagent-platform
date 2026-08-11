<template>
  <div class="api-config">
    <div class="models-list" v-if="configs.length > 0">
      <div 
        v-for="config in configs" 
        :key="config.id" 
        class="model-card"
        :class="{ 'is-default': config.is_default }"
      >
        <div class="model-header">
          <div class="model-info">
            <h3>{{ config.name }}</h3>
            <span class="model-code">{{ config.code }}</span>
            <span v-if="config.is_default" class="default-badge">默认</span>
          </div>
          <div class="model-actions">
            <button class="btn-icon" @click="setDefault(config)" v-if="!config.is_default" title="设为默认">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M12,17.27L18.18,21L16.54,13.97L22,9.24L14.81,8.62L12,2L9.19,8.62L2,9.24L7.45,13.97L5.82,21L12,17.27Z"/>
              </svg>
            </button>
            <button class="btn-icon" @click="openModal(config)" title="编辑">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
              </svg>
            </button>
            <button class="btn-icon delete" @click="deleteConfig(config)" title="删除">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="model-details">
          <div class="detail-item">
            <span class="label">调用方式:</span>
            <span class="value">{{ config.call_type || 'OpenAI Chat' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">API URL:</span>
            <span class="value">{{ config.api_url || '默认' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">API Key:</span>
            <span class="value masked">{{ maskApiKey(config.api_key) }}</span>
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
        <path fill="currentColor" d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z"/>
      </svg>
      <h3>暂无模型配置</h3>
      <p>点击上方"+"按钮添加您的第一个模型</p>
    </div>
    
    <div class="functional-models-section" v-if="isSuperuser">
      <h2 class="section-title">功能模型配置</h2>
      <p class="section-desc">配置用于特定功能的专用模型（如意图识别）</p>
      
      <div class="functional-models-list" v-if="functionalModels.length > 0">
        <div 
          v-for="model in functionalModels" 
          :key="model.id" 
          class="model-card functional-card"
          :class="{ 'is-active': model.is_active }"
        >
          <div class="model-header">
            <div class="model-info">
              <h3>{{ model.name }}</h3>
              <span class="model-type-badge">{{ getModelTypeLabel(model.functional_type) }}</span>
              <span class="model-code">{{ model.code }}</span>
            </div>
            <div class="model-actions">
              <button class="btn-icon" @click="openFunctionalModal(model)" title="编辑">
                <svg viewBox="0 0 24 24">
                  <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
                </svg>
              </button>
              <button class="btn-icon delete" @click="deleteFunctionalModel(model)" title="删除">
                <svg viewBox="0 0 24 24">
                  <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="model-details">
            <div class="detail-item">
              <span class="label">调用方式:</span>
              <span class="value">{{ model.call_type || 'OpenAI Chat' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">API URL:</span>
              <span class="value">{{ model.api_url || '默认' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">状态:</span>
              <span class="value" :class="model.is_active ? 'active-status' : 'inactive-status'">
                {{ model.is_active ? '已启用' : '已禁用' }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div class="loading-state" v-else-if="loading">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <div class="empty-functional" v-else>
        <p>暂无功能模型配置</p>
        <button class="btn-add-functional" @click="openFunctionalModal()">添加功能模型</button>
      </div>
      
      <button v-if="functionalModels.length > 0" class="btn-add-functional" @click="openFunctionalModal()">
        添加功能模型
      </button>
    </div>
    
    <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingConfig ? '编辑模型' : '添加模型' }}</h3>
          <button class="btn-close" @click="closeModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveConfig" class="modal-body">
          <div class="form-group">
            <label>模型名称</label>
            <input 
              type="text" 
              v-model="formData.name" 
              placeholder="例如: GPT-4、Claude-3"
              required
            />
          </div>
          
          <div class="form-group">
            <label>模型代码</label>
            <input 
              type="text" 
              v-model="formData.code" 
              placeholder="例如: gpt-4、claude-3-opus"
              required
            />
          </div>
          
          <div class="form-group">
            <label>调用方式</label>
            <select v-model="formData.call_type" class="form-select">
              <option value="OpenAI Chat">OpenAI Chat</option>
              <option value="OpenAI Responses">OpenAI Responses</option>
              <option value="Anthropic">Anthropic</option>
              <option value="Custom">Custom</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>API URL</label>
            <input 
              type="text" 
              v-model="formData.api_url" 
              placeholder="例如: https://api.openai.com/v1 (可选)"
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
          
          <div class="form-group checkbox">
            <label>
              <input type="checkbox" v-model="formData.is_default" />
              设为默认模型
            </label>
          </div>
          
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeModal">取消</button>
            <button type="submit" class="btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>
    
    <div class="toast" v-if="toast.show" :class="toast.type">
      {{ toast.message }}
    </div>
    
    <div class="modal-overlay" v-if="showFunctionalModal" @click.self="closeFunctionalModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingFunctionalModel ? '编辑功能模型' : '添加功能模型' }}</h3>
          <button class="btn-close" @click="closeFunctionalModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveFunctionalModel" class="modal-body">
          <div class="form-group">
            <label>模型名称</label>
            <input 
              type="text" 
              v-model="functionalFormData.name" 
              placeholder="例如: 意图识别模型"
              required
            />
          </div>
          
          <div class="form-group">
            <label>模型类型</label>
            <select v-model="functionalFormData.functional_type" class="form-select" required>
              <option value="intent_recognition">意图识别</option>
              <option value="code_generation">代码生成</option>
              <option value="embedding">向量嵌入</option>
              <option value="ocr">OCR文字识别</option>
            </select>
          </div>
          
          <div class="form-group checkbox">
            <label>
              <input type="checkbox" v-model="useExistingModel" @change="onUseExistingModelChange" />
              使用已有API模型配置
            </label>
          </div>
          
          <div class="form-group" v-if="useExistingModel">
            <label>选择模型</label>
            <select v-model="selectedExistingModelId" class="form-select" @change="onExistingModelSelect">
              <option value="">请选择...</option>
              <option v-for="config in configs" :key="config.id" :value="config.id">
                {{ config.name }} ({{ config.code }})
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>模型代码</label>
            <input 
              type="text" 
              v-model="functionalFormData.code" 
              placeholder="例如: gpt-4o-mini"
              required
              :disabled="useExistingModel"
            />
          </div>
          
          <div class="form-group">
            <label>调用方式</label>
            <select v-model="functionalFormData.call_type" class="form-select" :disabled="useExistingModel">
              <option value="OpenAI Chat">OpenAI Chat</option>
              <option v-if="functionalFormData.functional_type !== 'ocr'" value="OpenAI Responses">OpenAI Responses</option>
              <option value="Anthropic">Anthropic</option>
              <option v-if="functionalFormData.functional_type === 'embedding' || functionalFormData.functional_type === 'ocr'" value="DashScope SDK">DashScope SDK</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>API URL</label>
            <input 
              type="text" 
              v-model="functionalFormData.api_url" 
              placeholder="例如: https://api.openai.com/v1 (可选)"
              :disabled="useExistingModel"
            />
          </div>
          
          <div class="form-group">
            <label>API Key</label>
            <div class="input-wrapper">
              <input 
                :type="showFunctionalApiKey ? 'text' : 'password'" 
                v-model="functionalFormData.api_key" 
                placeholder="输入 API Key"
                required
                :disabled="useExistingModel"
              />
              <button type="button" class="toggle-visibility" @click="showFunctionalApiKey = !showFunctionalApiKey">
                <svg viewBox="0 0 24 24">
                  <path v-if="showFunctionalApiKey" fill="currentColor" d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z"/>
                  <path v-else fill="currentColor" d="M11.83,9L15,12.16C15,12.11 15,12.05 15,12A3,3 0 0,0 12,9C11.94,9 11.89,9 11.83,9M7.53,9.8L9.08,11.35C9.03,11.56 9,11.77 9,12A3,3 0 0,0 12,15C12.22,15 12.44,14.97 12.65,14.92L14.2,16.47C13.53,16.8 12.79,17 12,17A5,5 0 0,1 7,12C7,11.21 7.2,10.47 7.53,9.8M2,4.27L4.28,6.55L4.73,7C2.08,9.3 0.46,12.46 0,12C0.77,14.77 2.39,17.17 4.55,18.94L2,21.5H8V15.5L5.89,17.61C4.16,16.07 2.86,14.12 2.2,12C2.86,9.88 4.16,7.93 5.89,6.39L8,8.5V2.5H2M16,12A5,5 0 0,0 12,7C11.21,7 10.47,7.2 9.8,7.53L8.25,5.98C8.92,5.66 9.66,5.46 10.4,5.37L12,2L13.59,5.36C16.27,5.73 18.5,7.56 19.43,10.04C19.46,10.06 19.5,10.09 19.53,10.12L21.71,8.94L20.29,11.35L21.71,13.76L19.53,12.58C19.5,12.61 19.46,12.64 19.43,12.66C18.5,15.14 16.27,16.95 13.59,17.32L12,20.66L10.41,17.31C9.67,17.22 8.92,17.02 8.25,16.7L9.8,15.15C10.47,15.47 11.21,15.67 12,15.67A5,5 0 0,0 17,12.16L16.84,12L17,11.84Z"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div class="form-group checkbox">
            <label>
              <input type="checkbox" v-model="functionalFormData.is_active" />
              启用此模型
            </label>
          </div>
          
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeFunctionalModal">取消</button>
            <button type="submit" class="btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, watch, computed } from 'vue'
import axios from 'axios'

const configs = ref([])
const showModal = ref(false)
const showApiKey = ref(false)
const editingConfig = ref(null)
const toast = ref({ show: false, message: '', type: 'success' })
const addModelTrigger = inject('addModelTrigger', ref(0))
const loading = ref(true)

const functionalModels = ref([])
const showFunctionalModal = ref(false)
const showFunctionalApiKey = ref(false)
const editingFunctionalModel = ref(null)

const isSuperuser = computed(() => localStorage.getItem('is_superuser') === 'true')

const functionalFormData = ref({
  name: '',
  functional_type: 'intent_recognition',
  code: '',
  call_type: 'OpenAI Chat',
  api_key: '',
  api_url: '',
  is_active: true
})

const useExistingModel = ref(false)
const selectedExistingModelId = ref('')

const MODEL_TYPE_LABELS = {
  'intent_recognition': '意图识别',
  'code_generation': '代码生成',
  'embedding': '向量嵌入',
  'ocr': 'OCR文字识别'
}

const getModelTypeLabel = (type) => {
  return MODEL_TYPE_LABELS[type] || type
}

const onUseExistingModelChange = () => {
  if (!useExistingModel.value) {
    selectedExistingModelId.value = ''
    functionalFormData.value.code = ''
    functionalFormData.value.call_type = 'OpenAI Chat'
    functionalFormData.value.api_url = ''
    functionalFormData.value.api_key = ''
  }
}

const onExistingModelSelect = () => {
  if (selectedExistingModelId.value) {
    const selectedConfig = configs.value.find(c => c.id === selectedExistingModelId.value)
    if (selectedConfig) {
      functionalFormData.value.code = selectedConfig.code
      functionalFormData.value.call_type = selectedConfig.call_type || 'OpenAI Chat'
      functionalFormData.value.api_url = selectedConfig.api_url || ''
      functionalFormData.value.api_key = selectedConfig.api_key
    }
  }
}

watch(addModelTrigger, () => {
  if (addModelTrigger.value > 0) {
    openModal()
  }
})

const formData = ref({
  name: '',
  code: '',
  call_type: 'OpenAI Chat',
  api_key: '',
  api_url: '',
  is_default: false
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

const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/api-config')
    configs.value = response.data
  } catch (error) {
    console.error('Failed to load configs:', error)
  } finally {
    loading.value = false
  }
}

const openModal = (config = null) => {
  if (config) {
    editingConfig.value = config
    formData.value = {
      name: config.name,
      code: config.code,
      call_type: config.call_type || 'OpenAI Chat',
      api_key: config.api_key,
      api_url: config.api_url || '',
      is_default: config.is_default
    }
  } else {
    editingConfig.value = null
    formData.value = {
      name: '',
      code: '',
      call_type: 'OpenAI Chat',
      api_key: '',
      api_url: '',
      is_default: configs.value.length === 0
    }
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingConfig.value = null
  formData.value = {
    name: '',
    code: '',
    call_type: 'OpenAI Chat',
    api_key: '',
    api_url: '',
    is_default: false
  }
}

const saveConfig = async () => {
  try {
    if (editingConfig.value) {
      await axios.put(`/api/api-config/${editingConfig.value.id}`, formData.value)
      showToast('配置更新成功！')
    } else {
      await axios.post('/api/api-config', formData.value)
      showToast('配置添加成功！')
    }
    closeModal()
    loadConfigs()
  } catch (error) {
    showToast(error.response?.data?.detail || '操作失败', 'error')
  }
}

const deleteConfig = async (config) => {
  if (!confirm(`确定要删除 "${config.name}" 吗？`)) return
  
  try {
    await axios.delete(`/api/api-config/${config.id}`)
    showToast('配置删除成功！')
    loadConfigs()
  } catch (error) {
    showToast(error.response?.data?.detail || '删除失败', 'error')
  }
}

const setDefault = async (config) => {
  try {
    await axios.put(`/api/api-config/${config.id}`, { is_default: true })
    showToast('已设为默认模型')
    loadConfigs()
  } catch (error) {
    showToast('操作失败', 'error')
  }
}

const loadFunctionalModels = async () => {
  if (!isSuperuser.value) return
  try {
    const response = await axios.get('/api/functional-models')
    functionalModels.value = response.data
  } catch (error) {
    console.error('Failed to load functional models:', error)
  }
}

const openFunctionalModal = (model = null) => {
  useExistingModel.value = false
  selectedExistingModelId.value = ''
  if (model) {
    editingFunctionalModel.value = model
    functionalFormData.value = {
      name: model.name,
      functional_type: model.functional_type,
      code: model.code,
      call_type: model.call_type || 'OpenAI Chat',
      api_key: model.api_key,
      api_url: model.api_url || '',
      is_active: model.is_active
    }
  } else {
    editingFunctionalModel.value = null
    functionalFormData.value = {
      name: '',
      functional_type: 'intent_recognition',
      code: '',
      call_type: 'OpenAI Chat',
      api_key: '',
      api_url: '',
      is_active: true
    }
  }
  showFunctionalModal.value = true
}

const closeFunctionalModal = () => {
  showFunctionalModal.value = false
  editingFunctionalModel.value = null
  useExistingModel.value = false
  selectedExistingModelId.value = ''
  functionalFormData.value = {
    name: '',
    functional_type: 'intent_recognition',
    code: '',
    call_type: 'OpenAI Chat',
    api_key: '',
    api_url: '',
    is_active: true
  }
}

const saveFunctionalModel = async () => {
  try {
    if (editingFunctionalModel.value) {
      await axios.put(`/api/functional-models/${editingFunctionalModel.value.id}`, functionalFormData.value)
      showToast('功能模型更新成功！')
    } else {
      await axios.post('/api/functional-models', functionalFormData.value)
      showToast('功能模型添加成功！')
    }
    closeFunctionalModal()
    loadFunctionalModels()
  } catch (error) {
    showToast(error.response?.data?.detail || '操作失败', 'error')
  }
}

const deleteFunctionalModel = async (model) => {
  if (!confirm(`确定要删除功能模型 "${model.name}" 吗？`)) return
  
  try {
    await axios.delete(`/api/functional-models/${model.id}`)
    showToast('功能模型删除成功！')
    loadFunctionalModels()
  } catch (error) {
    showToast(error.response?.data?.detail || '删除失败', 'error')
  }
}

onMounted(() => {
  loadConfigs()
  loadFunctionalModels()
})
</script>

<style scoped>
.api-config {
  max-width: 900px;
}

.models-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.model-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 2px solid transparent;
  transition: all 0.2s;
}

.model-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.model-card.is-default {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.model-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.model-info h3 {
  margin: 0;
  font-size: 18px;
  color: #1a1a2e;
}

.model-code {
  padding: 4px 10px;
  background: #f0f0f0;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
  font-family: monospace;
}

.default-badge {
  padding: 4px 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.model-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  width: 36px;
  height: 36px;
  border: none;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: #667eea;
  color: #fff;
}

.btn-icon.delete:hover {
  background: #ef4444;
}

.btn-icon svg {
  width: 18px;
  height: 18px;
}

.model-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.detail-item .label {
  color: #999;
  min-width: 70px;
}

.detail-item .value {
  color: #333;
}

.detail-item .value.masked {
  font-family: monospace;
  color: #666;
}

.loading-state {
  text-align: center;
  padding: 60px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.loading-state .loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

.loading-state p {
  color: #666;
  font-size: 14px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: #fff;
  border-radius: 12px;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: #ccc;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.empty-state p {
  margin: 0;
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
  z-index: 2000;
}

.modal {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1a1a2e;
}

.btn-close {
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.btn-close:hover {
  background: #eee;
}

.btn-close svg {
  width: 20px;
  height: 20px;
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

.form-group input[type="text"],
.form-group input[type="password"] {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
  color: #999;
}

.form-select {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-select:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
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

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  padding-right: 48px;
}

.toggle-visibility {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  padding: 4px;
}

.toggle-visibility:hover {
  color: #667eea;
}

.toggle-visibility svg {
  width: 20px;
  height: 20px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #fff;
  color: #666;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #f5f7fa;
}

.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 14px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 3000;
  animation: slideIn 0.3s ease;
}

.toast.success {
  background: #10b981;
  color: #fff;
}

.toast.error {
  background: #ef4444;
  color: #fff;
}

@keyframes slideIn {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.functional-models-section {
  margin-top: 40px;
  padding-top: 30px;
  border-top: 1px solid #eee;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 8px 0;
}

.section-desc {
  color: #666;
  font-size: 14px;
  margin: 0 0 20px 0;
}

.functional-models-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.functional-card {
  border-left: 4px solid #764ba2;
}

.functional-card.is-active {
  border-left-color: #10b981;
}

.model-type-badge {
  padding: 4px 10px;
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  color: #fff;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.active-status {
  color: #10b981;
  font-weight: 500;
}

.inactive-status {
  color: #999;
}

.empty-functional {
  text-align: center;
  padding: 30px;
  background: #f9f9f9;
  border-radius: 12px;
  margin-bottom: 16px;
}

.empty-functional p {
  color: #666;
  margin: 0 0 16px 0;
}

.btn-add-functional {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-functional:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(118, 75, 162, 0.4);
}

@media (max-width: 768px) {
  .models-list,
  .functional-models-list {
    grid-template-columns: 1fr;
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
