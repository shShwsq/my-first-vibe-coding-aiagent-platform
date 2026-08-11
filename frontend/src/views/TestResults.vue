<template>
  <div class="test-results-page">
    <div v-if="!selectedAgent" class="agent-list-view">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="agents.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" class="empty-icon">
          <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4Z"/>
        </svg>
        <p>暂无测试结果</p>
      </div>
      <div v-else class="card-list">
        <div 
          v-for="agent in agents" 
          :key="`${agent.agent_type}-${agent.agent_id}`" 
          class="card"
          :class="{ 'workflow-card': agent.agent_type === 'workflow_agent' }"
          @click="selectAgent(agent)"
        >
          <div class="card-icon" :class="{ 'workflow-icon': agent.agent_type === 'workflow_agent' }">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M12,2A2,2 0 0,1 14,4A2,2 0 0,1 12,6A2,2 0 0,1 10,4A2,2 0 0,1 12,2M21,9H15V22H13V16H11V22H9V9H3V7H21V9Z"/>
            </svg>
          </div>
          <div class="card-info">
            <div class="card-name">
              {{ agent.agent_name }}
              <span v-if="agent.agent_type === 'workflow_agent'" class="agent-type-badge">工作流</span>
            </div>
            <div class="card-meta">{{ agent.test_count }} 条测试记录</div>
          </div>
          <svg viewBox="0 0 24 24" class="arrow-icon">
            <path fill="currentColor" d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
          </svg>
        </div>
      </div>
    </div>
    
    <div v-else-if="!selectedFolder" class="folder-list-view">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="folders.length === 0" class="empty-state">
        <p>暂无测试记录</p>
      </div>
      <div v-else class="card-list">
        <div 
          v-for="folder in folders" 
          :key="folder.folder_id" 
          class="card"
          @click="selectFolder(folder)"
        >
          <div class="card-icon">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z"/>
            </svg>
          </div>
          <div class="card-info">
            <div class="card-name">{{ folder.folder_name }}</div>
            <div class="card-meta">{{ folder.test_count }} 条测试记录</div>
          </div>
          <svg viewBox="0 0 24 24" class="arrow-icon">
            <path fill="currentColor" d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
          </svg>
        </div>
      </div>
    </div>
    
    <div v-else class="detail-list-view">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="details.length === 0" class="empty-state">
        <p>暂无测试详情</p>
      </div>
      <div v-else class="table-container">
        <div class="table-header" v-if="selectedIds.size > 0">
          <div class="selection-info" v-if="selectedIds.size > 0">
            已选择 {{ selectedIds.size }} 条记录
          </div>
          <button 
            v-if="selectedIds.size > 0" 
            class="btn-delete"
            @click="deleteSelected"
            :disabled="deleting"
          >
            <svg viewBox="0 0 24 24" class="btn-icon">
              <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
            </svg>
            {{ deleting ? '删除中...' : '删除选中' }}
          </button>
        </div>
        <table class="detail-table">
          <colgroup>
            <col style="width: 3%">
            <col style="width: 3%">
            <col style="width: 14%">
            <col v-if="hasImages" style="width: 15%">
            <col v-if="hasFiles" style="width: 8%">
            <col style="width: 18%">
            <col v-if="hasSampleAnswers" style="width: 18%">
            <col v-if="hasErrors" style="width: 15%">
            <col style="width: 6%">
          </colgroup>
          <thead>
            <tr>
              <th class="col-checkbox">
                <input 
                  type="checkbox" 
                  :checked="isAllSelected"
                  @change="toggleSelectAll"
                  class="checkbox"
                />
              </th>
              <th class="col-index">#</th>
              <th class="col-question">问题</th>
              <th v-if="hasImages" class="col-images">图片</th>
              <th v-if="hasFiles" class="col-file">文件</th>
              <th class="col-response">智能体回答</th>
              <th v-if="hasSampleAnswers" class="col-sample">预设回答</th>
              <th v-if="hasErrors" class="col-error">错误信息</th>
              <th class="col-time">耗时</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(detail, index) in details" :key="detail.id" :class="{ 'selected-row': selectedIds.has(detail.id) }">
              <td class="col-checkbox">
                <input 
                  type="checkbox" 
                  :checked="selectedIds.has(detail.id)"
                  @change="toggleSelect(detail.id)"
                  class="checkbox"
                />
              </td>
              <td class="col-index">{{ index + 1 }}</td>
              <td class="col-question">
                <div class="cell-content">{{ detail.question }}</div>
              </td>
              <td v-if="hasImages" class="col-images">
                <div v-if="detail.images && detail.images.length > 0" class="images-cell">
                  <div 
                    v-for="img in detail.images" 
                    :key="img.image_id" 
                    class="image-thumb"
                    @click="openImagePreview(img.image_id)"
                  >
                    <img 
                      v-if="imageCache[img.image_id]" 
                      :src="imageCache[img.image_id]" 
                      alt="图片"
                    />
                    <div v-else class="image-loading">
                      <div class="loading-spinner-small"></div>
                    </div>
                  </div>
                </div>
                <span v-else class="empty-cell">-</span>
              </td>
              <td v-if="hasFiles" class="col-file">
                <div v-if="detail.file_info" class="file-cell">
                  <span class="file-name">{{ detail.file_info.filename }}</span>
                </div>
                <span v-else class="empty-cell">-</span>
              </td>
              <td class="col-response">
                <div class="cell-content response-text">{{ detail.response || '无响应' }}</div>
              </td>
              <td v-if="hasSampleAnswers" class="col-sample">
                <div class="cell-content sample-text">{{ detail.sample_answer || '无预设回答' }}</div>
              </td>
              <td v-if="hasErrors" class="col-error">
                <div v-if="detail.error_message" class="cell-content error-text">{{ detail.error_message }}</div>
                <span v-else class="empty-cell">-</span>
              </td>
              <td class="col-time">{{ detail.request_time?.toFixed(2) || '0.00' }}s</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="modal-overlay image-preview-overlay" v-if="showImagePreview" @click="closeImagePreview">
      <div class="image-preview-modal" @click.stop>
        <img v-if="previewImageUrl" :src="previewImageUrl" alt="预览图片" />
        <div v-else class="preview-loading">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        <button class="btn-close-preview" @click="closeImagePreview">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, watch, onMounted, reactive, computed } from 'vue'
import axios from 'axios'

const agents = ref([])
const folders = ref([])
const details = ref([])
const selectedAgent = inject('selectedResultAgent')
const selectedFolder = inject('selectedResultFolder')
const backToResultAgentList = inject('backToResultAgentList')
const backToResultFolderList = inject('backToResultFolderList')
const loading = ref(false)

const imageCache = reactive({})
const showImagePreview = ref(false)
const previewImageUrl = ref('')
const loadingImages = ref(new Set())
const selectedIds = ref(new Set())
const deleting = ref(false)

const hasImages = computed(() => {
  return details.value.some(d => d.images && d.images.length > 0)
})

const isAllSelected = computed(() => {
  return details.value.length > 0 && selectedIds.value.size === details.value.length
})

const hasFiles = computed(() => {
  return details.value.some(d => d.file_info)
})

const hasSampleAnswers = computed(() => {
  return details.value.some(d => d.sample_answer && d.sample_answer.trim() !== '')
})

const hasErrors = computed(() => {
  return details.value.some(d => d.error_message && d.error_message.trim() !== '')
})

const loadImageThumbnail = async (imageId) => {
  if (imageCache[imageId]) return
  
  try {
    const response = await axios.get(`/api/test-cases/images/${imageId}/preview`, {
      responseType: 'blob'
    })
    imageCache[imageId] = window.URL.createObjectURL(new Blob([response.data]))
  } catch (error) {
    console.error('Failed to load image thumbnail:', error)
  }
}

const openImagePreview = async (imageId) => {
  showImagePreview.value = true
  previewImageUrl.value = ''
  
  try {
    const response = await axios.get(`/api/test-cases/images/${imageId}`, {
      responseType: 'blob'
    })
    previewImageUrl.value = window.URL.createObjectURL(new Blob([response.data]))
  } catch (error) {
    console.error('Failed to load full image:', error)
    showImagePreview.value = false
  }
}

const closeImagePreview = () => {
  showImagePreview.value = false
  if (previewImageUrl.value) {
    window.URL.revokeObjectURL(previewImageUrl.value)
    previewImageUrl.value = ''
  }
}

const loadAllImageThumbnails = () => {
  details.value.forEach(detail => {
    if (detail.images && detail.images.length > 0) {
      detail.images.forEach(img => {
        loadImageThumbnail(img.image_id)
      })
    }
  })
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

const loadAgents = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/test-chat/test-results/agents')
    agents.value = response.data
  } catch (error) {
    console.error('Failed to load agents:', error)
  } finally {
    loading.value = false
  }
}

const loadFolders = async () => {
  loading.value = true
  try {
    const agentType = selectedAgent.value.agent_type || 'agent'
    const response = await axios.get(`/api/test-chat/test-results/${selectedAgent.value.agent_id}/folders`, {
      params: { agent_type: agentType }
    })
    folders.value = response.data
  } catch (error) {
    console.error('Failed to load folders:', error)
  } finally {
    loading.value = false
  }
}

const loadDetails = async () => {
  loading.value = true
  try {
    const agentType = selectedAgent.value.agent_type || 'agent'
    const response = await axios.get(`/api/test-chat/test-results/${selectedAgent.value.agent_id}/folder/${selectedFolder.value.folder_id}`, {
      params: { agent_type: agentType }
    })
    details.value = response.data
    loadAllImageThumbnails()
  } catch (error) {
    console.error('Failed to load details:', error)
  } finally {
    loading.value = false
  }
}

const selectAgent = (agent) => {
  selectedAgent.value = agent
  loadFolders()
}

const selectFolder = (folder) => {
  selectedFolder.value = folder
  selectedIds.value.clear()
  loadDetails()
}

const toggleSelect = (id) => {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value.clear()
  } else {
    selectedIds.value = new Set(details.value.map(d => d.id))
  }
}

const deleteSelected = async () => {
  if (selectedIds.value.size === 0) return
  
  if (!confirm(`确定要删除选中的 ${selectedIds.value.size} 条测试结果吗？`)) {
    return
  }
  
  deleting.value = true
  try {
    const response = await axios.post('/api/test-chat/test-results/batch-delete', Array.from(selectedIds.value))
    alert(response.data.message)
    selectedIds.value.clear()
    await loadDetails()
  } catch (error) {
    console.error('Failed to delete test results:', error)
    alert(error.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}

watch(backToResultAgentList, () => {
  selectedAgent.value = null
  selectedFolder.value = null
  folders.value = []
  details.value = []
  loadAgents()
})

watch(backToResultFolderList, () => {
  selectedFolder.value = null
  details.value = []
  loadFolders()
})

onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.test-results-page {
  padding: 24px;
  max-width: 100%;
  margin: 0;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.card-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: flex-start;
}

.card {
  display: flex;
  align-items: center;
  width: 320px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.card.workflow-card {
  border: 1px solid rgba(240, 147, 251, 0.3);
}

.card.workflow-card:hover {
  box-shadow: 0 4px 16px rgba(240, 147, 251, 0.25);
}

.card-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
}

.card-icon.workflow-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.card-icon svg {
  width: 24px;
  height: 24px;
  color: #fff;
}

.card-info {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-type-badge {
  font-size: 12px;
  font-weight: 500;
  color: #fff;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
}

.card-meta {
  font-size: 14px;
  color: #666;
}

.arrow-icon {
  width: 24px;
  height: 24px;
  color: #ccc;
  flex-shrink: 0;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-radius: 12px 12px 0 0;
  border-bottom: 1px solid #eee;
}

.selection-info {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.btn-delete {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete:hover:not(:disabled) {
  background: #dc2626;
}

.btn-delete:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.table-container {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.detail-table th {
  background: #f8f9fa;
  padding: 12px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #666;
  border-bottom: 1px solid #eee;
  white-space: nowrap;
}

.detail-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: top;
}

.detail-table tr:last-child td {
  border-bottom: none;
}

.detail-table tr:hover {
  background: #fafafa;
}

.col-index {
  text-align: center;
}

.col-time {
  text-align: center;
}

.col-checkbox {
  text-align: center;
}

.checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #667eea;
}

.selected-row {
  background: #f0f4ff !important;
}

.selected-row:hover {
  background: #e8efff !important;
}

.cell-content {
  font-size: 13px;
  color: #333;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 120px;
  overflow-y: auto;
}

.response-text {
  background: #e8f5e9;
  padding: 8px;
  border-radius: 6px;
}

.sample-text {
  background: #fff3e0;
  padding: 8px;
  border-radius: 6px;
}

.error-text {
  color: #c62828;
  background: #ffebee;
  padding: 8px;
  border-radius: 6px;
}

.images-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.image-thumb {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

.image-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.image-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-loading {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid #e0e0e0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.image-preview-modal {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview-modal img {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 8px;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #fff;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.btn-close-preview {
  position: absolute;
  top: -40px;
  right: 0;
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.btn-close-preview:hover {
  background: rgba(255, 255, 255, 0.3);
}

.btn-close-preview svg {
  width: 20px;
  height: 20px;
  color: #fff;
}

.file-cell {
  font-size: 13px;
}

.file-name {
  color: #333;
  font-weight: 500;
}

.empty-cell {
  color: #999;
  font-size: 13px;
}
</style>
