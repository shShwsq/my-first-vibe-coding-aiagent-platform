<template>
  <div class="knowledge-base-page">
    <div class="kb-section" v-if="!selectedKB">
      <div class="kb-list" v-if="knowledgeBases.length > 0">
        <div 
          v-for="kb in knowledgeBases" 
          :key="kb.id" 
          class="kb-card"
          @click="selectKB(kb)"
        >
          <div class="kb-icon">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
            </svg>
          </div>
          <div class="kb-info">
            <div class="kb-name">{{ kb.name }}</div>
            <div class="kb-meta">
              <span class="kb-count">{{ kb.file_count || 0 }} 个文件</span>
              <span class="kb-date">{{ formatDate(kb.created_at) }}</span>
            </div>
            <div class="kb-desc" v-if="kb.description">{{ kb.description }}</div>
          </div>
          <div class="kb-actions">
            <button class="btn-icon" @click.stop="openEditModal(kb)" title="编辑">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
              </svg>
            </button>
            <button class="btn-icon delete" @click.stop="deleteKB(kb)" title="删除">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div class="loading-state" v-else-if="loading">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <div class="empty-state" v-else>
        <svg viewBox="0 0 24 24">
          <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4Z"/>
        </svg>
        <h3>暂无知识库</h3>
        <p>点击上方"新建知识库"按钮创建您的第一个知识库</p>
      </div>
    </div>

    <div class="files-section" v-else>
      <div class="files-header">
        <h3>文件列表</h3>
        <div class="upload-buttons">
          <button class="btn-primary" @click="triggerFileInput">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M12,11L16,15H13.5V18H10.5V15H8L12,11Z"/>
            </svg>
            上传文件
          </button>
          <button class="btn-secondary" @click="triggerFolderInput">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z"/>
            </svg>
            上传文件夹
          </button>
        </div>
      </div>

      <input 
        type="file" 
        ref="fileInput"
        @change="handleFileSelect"
        accept=".pdf,.xlsx,.xls,.docx,.doc,.ppt,.pptx,.png,.jpg,.jpeg,.gif,.webp,.bmp"
        multiple
        style="display: none"
      />

      <input 
        type="file" 
        ref="folderInput"
        @change="handleFolderSelect"
        accept=".pdf,.xlsx,.xls,.docx,.doc,.ppt,.pptx,.png,.jpg,.jpeg,.gif,.webp,.bmp"
        multiple
        webkitdirectory
        mozdirectory
        style="display: none"
      />

      <div class="files-list" v-if="files.length > 0">
        <div v-for="file in files" :key="file.id" class="file-item">
          <div class="file-icon" :class="file.file_type.toLowerCase()">
            <svg v-if="file.file_type === 'PDF'" viewBox="0 0 24 24">
              <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M10.92,12.31C10.68,11.54 10.15,9.08 11.55,9.04C12.95,9 12.03,12.16 12.03,12.16C12.42,13.65 14.05,14.72 14.05,14.72C14.55,14.57 17.4,14.24 17,15.72C16.57,17.2 13.5,15.81 13.5,15.81C11.55,15.95 10.09,16.47 10.09,16.47C8.96,18.58 7.64,19.5 7.1,18.61C6.43,17.5 9.23,16.07 9.23,16.07C10.68,13.72 10.9,12.35 10.92,12.31Z"/>
            </svg>
            <svg v-else-if="file.file_type === 'Excel'" viewBox="0 0 24 24">
              <path fill="currentColor" d="M21.17 3.25Q21.5 3.25 21.76 3.5 22 3.74 22 4.08V19.92Q22 20.26 21.76 20.5 21.5 20.75 21.17 20.75H7.83Q7.5 20.75 7.24 20.5 7 20.26 7 19.92V17H2.83Q2.5 17 2.24 16.76 2 16.5 2 16.17V7.83Q2 7.5 2.24 7.24 2.5 7 2.83 7H7V4.08Q7 3.74 7.24 3.5 7.5 3.25 7.83 3.25M7 13.06L8.18 15.28H9.97L8 12.06L9.93 8.89H8.22L7.13 10.9L7.09 10.96L7.06 11.03Q6.8 10.5 6.5 9.96 6.25 9.43 5.97 8.89H4.16L6.05 12.08L4 15.28H5.78M13.88 19.5V17H8.25V19.5M13.88 15.75V12.63H12V15.75M13.88 11.38V8.25H12V11.38M13.88 7V4.5H8.25V7M20.75 19.5V17H15.13V19.5M20.75 15.75V12.63H15.13V15.75M20.75 11.38V8.25H15.13V11.38M20.75 7V4.5H15.13V7Z"/>
            </svg>
            <svg v-else viewBox="0 0 24 24">
              <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
          </div>
          <div class="file-info">
            <div class="file-name">{{ file.filename }}</div>
            <div class="file-meta">
              <span class="file-type">{{ file.file_type }}</span>
              <span class="file-size">{{ file.file_size }}</span>
              <span class="file-date">{{ formatDate(file.created_at) }}</span>
              <span class="file-embedding" :class="{
                'has-embedding': file.embedding_status === 'completed',
                'processing': file.embedding_status === 'processing',
                'failed': file.embedding_status === 'failed'
              }">
                <span v-if="file.embedding_status === 'processing'" class="loading-spinner"></span>
                <span v-else-if="file.embedding_status === 'completed'">{{ file.chunk_count }} 个向量</span>
                <span v-else-if="file.embedding_status === 'failed'" :title="file.embedding_error">生成失败</span>
                <span v-else>无向量</span>
              </span>
              <span v-if="file.image_extraction_status === 'processing' || file.image_count > 0 || file.image_extraction_status === 'failed'" class="file-images-status" :class="{
                'has-images': (file.image_extraction_status === 'completed' || file.image_count > 0),
                'processing': file.image_extraction_status === 'processing',
                'failed': file.image_extraction_status === 'failed'
              }">
                <span v-if="file.image_extraction_status === 'processing'" class="loading-spinner"></span>
                <span v-else-if="file.image_count > 0" @click="openImagesModal(file)" title="点击查看图片" style="cursor: pointer;">
                  {{ file.image_count }} 张图片
                </span>
                <span v-else-if="file.image_extraction_status === 'failed'" :title="file.image_extraction_error">提取失败</span>
              </span>
            </div>
          </div>
          <div class="file-actions">
            <button class="btn-icon embedding" @click="openEmbeddingModal(file)" title="Embedding设置">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M12,6A6,6 0 0,1 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6M12,8A4,4 0 0,0 8,12A4,4 0 0,0 12,16A4,4 0 0,0 16,12A4,4 0 0,0 12,8Z"/>
              </svg>
            </button>
            <button class="btn-icon reindex" @click="reEmbedFile(file)" title="重新Embedding" :disabled="file.reindexing">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
              </svg>
            </button>
            <button class="btn-icon extract-images" @click="extractImages(file)" title="提取图片" :disabled="file.image_extraction_status === 'processing'">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M21 3H3C2 3 1 4 1 5V19C1 20 2 21 3 21H21C22 21 23 20 23 19V5C23 4 22 3 21 3M5 17L8.5 12.5L11 15.5L14.5 11L19 17H5Z"/>
              </svg>
            </button>
            <button v-if="file.image_count > 0" class="btn-icon view-images" @click="openImagesModal(file)" title="查看图片">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z"/>
              </svg>
            </button>
            <button class="btn-icon" @click="downloadFile(file)" title="下载">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
              </svg>
            </button>
            <button class="btn-icon delete" @click="deleteFile(file)" title="删除">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div class="empty-state small" v-else>
        <p>暂无文件，点击"上传文件"添加资源</p>
      </div>
    </div>

    <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingKB ? '编辑知识库' : '新建知识库' }}</h3>
          <button class="btn-close" @click="closeModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveKB" class="modal-body">
          <div class="form-group">
            <label>知识库名称</label>
            <input 
              type="text" 
              v-model="formData.name" 
              placeholder="知识库名称不可重复"
              required
            />
          </div>
          <div class="form-group">
            <label>描述（可选）</label>
            <textarea 
              v-model="formData.description" 
              placeholder="知识库用途描述"
              rows="3"
            ></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeModal">取消</button>
            <button type="submit" class="btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>

    <div class="modal-overlay" v-if="showEmbeddingModal" @click.self="closeEmbeddingModal">
      <div class="modal">
        <div class="modal-header">
          <h3>Embedding 设置</h3>
          <button class="btn-close" @click="closeEmbeddingModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveEmbeddingSettings" class="modal-body">
          <div class="form-group">
            <label>文件名</label>
            <input type="text" :value="embeddingFile?.filename" disabled />
          </div>
          <div class="embedding-status">
            <span class="status-label">当前状态：</span>
            <span class="status-value" :class="{ 'has-data': embeddingFile?.chunk_count > 0 }">
              {{ embeddingFile?.chunk_count > 0 ? `${embeddingFile.chunk_count} 个向量块` : '暂无向量数据' }}
            </span>
          </div>
          <div class="form-group">
            <label>分块大小 (tokens)</label>
            <input 
              type="number" 
              v-model.number="embeddingFormData.chunk_size" 
              min="100"
              max="8000"
              placeholder="默认: 1000"
            />
            <small class="form-hint">每个文本块的 token 数量，建议 500-2000</small>
          </div>
          <div class="form-group">
            <label>重叠大小 (tokens)</label>
            <input 
              type="number" 
              v-model.number="embeddingFormData.chunk_overlap" 
              min="0"
              max="1000"
              placeholder="默认: 200"
            />
            <small class="form-hint">相邻块之间的重叠 token 数，建议 100-500</small>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeEmbeddingModal">取消</button>
            <button type="submit" class="btn-primary">保存并重新生成</button>
          </div>
        </form>
      </div>
    </div>

    <div class="modal-overlay images-modal-overlay" v-if="showImagesModal" @click.self="closeImagesModal">
      <div class="modal images-modal">
        <div class="modal-header">
          <h3>{{ imagesFile?.filename }} - 提取的图片</h3>
          <button class="btn-close" @click="closeImagesModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <div class="modal-body images-body">
          <div class="images-toolbar">
            <span class="images-count">共 {{ images.length }} 张图片</span>
            <button class="btn-secondary btn-sm" @click="deleteAllImages" :disabled="deletingAll">
              {{ deletingAll ? '删除中...' : '删除全部' }}
            </button>
          </div>
          <div class="images-grid" v-if="images.length > 0">
            <div v-for="(img, index) in images" :key="img.id" class="image-item" :ref="el => setImageRef(el, img.id)">
              <div class="image-preview" @click="previewImage(img)">
                <div v-if="isImageLoading(img.id)" class="image-loading">
                  <div class="loading-spinner"></div>
                </div>
                <img v-else-if="isImageLoaded(img.id)" :src="getCachedImageUrl(img)" :alt="`图片 ${index + 1}`" />
                <div v-else class="image-placeholder">
                  <svg viewBox="0 0 24 24">
                    <path fill="currentColor" d="M21 3H3C2 3 1 4 1 5V19C1 20 2 21 3 21H21C22 21 23 20 23 19V5C23 4 22 3 21 3M5 17L8.5 12.5L11 15.5L14.5 11L19 17H5Z"/>
                  </svg>
                </div>
              </div>
              <div class="image-info">
                <span class="image-meta">第 {{ img.page_number }} 页 / 第 {{ img.image_index }} 张</span>
                <span class="image-size" v-if="img.width && img.height">{{ img.width }} x {{ img.height }}</span>
              </div>
              <div class="image-actions">
                <button class="btn-icon-sm" @click="downloadImage(img)" title="下载">
                  <svg viewBox="0 0 24 24">
                    <path fill="currentColor" d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
                  </svg>
                </button>
                <button class="btn-icon-sm delete" @click="deleteImage(img)" title="删除">
                  <svg viewBox="0 0 24 24">
                    <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div class="empty-state small" v-else>
            <p>暂无提取的图片</p>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-overlay image-preview-overlay" v-if="showImagePreview" @click="closeImagePreview">
      <div class="image-preview-modal" @click.stop>
        <img :src="previewImageUrl" alt="预览图片" />
        <button class="btn-close-preview" @click="closeImagePreview">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="toast" v-if="toast.show" :class="toast.type">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, inject, watch } from 'vue'
import axios from 'axios'

const addKBTrigger = inject('addKBTrigger', ref(0))
const selectedKBName = inject('selectedKBName', ref(null))
const backToKBList = inject('backToKBList', ref(0))

watch(addKBTrigger, (newVal) => {
  if (newVal > 0) {
    openCreateModal()
  }
})

watch(backToKBList, (newVal) => {
  if (newVal > 0) {
    selectedKB.value = null
    selectedKBName.value = null
    files.value = []
  }
})

watch(selectedKBName, (newVal) => {
  if (newVal === null) {
    selectedKB.value = null
    files.value = []
  }
})

const knowledgeBases = ref([])
const selectedKB = ref(null)
const files = ref([])
const loading = ref(true)
const fileInput = ref(null)
const folderInput = ref(null)
const isUploading = ref(false)
const showModal = ref(false)
const editingKB = ref(null)
const showEmbeddingModal = ref(false)
const embeddingFile = ref(null)
const embeddingFormData = ref({
  chunk_size: 1000,
  chunk_overlap: 200
})
const formData = ref({
  name: '',
  description: ''
})
const toast = ref({ show: false, message: '', type: 'success' })

const showImagesModal = ref(false)
const imagesFile = ref(null)
const images = ref([])
const deletingAll = ref(false)
const showImagePreview = ref(false)
const previewImageUrl = ref('')

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const loadKnowledgeBases = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/knowledge-bases')
    knowledgeBases.value = response.data
  } catch (error) {
    console.error('Failed to load knowledge bases:', error)
  } finally {
    loading.value = false
  }
}

const selectKB = (kb) => {
  selectedKB.value = kb
  selectedKBName.value = kb.name
  loadFiles()
}

const loadFiles = async () => {
  if (!selectedKB.value) {
    files.value = []
    return
  }
  try {
    const response = await axios.get('/api/test-case-files', {
      params: { knowledge_base_id: selectedKB.value.id }
    })
    files.value = response.data
    
    const hasProcessing = files.value.some(f => 
      f.embedding_status === 'processing' || f.image_extraction_status === 'processing'
    )
    if (hasProcessing) {
      startPolling()
    } else {
      stopPolling()
    }
  } catch (error) {
    console.error('Failed to load files:', error)
  }
}

const openCreateModal = () => {
  editingKB.value = null
  formData.value = { name: '', description: '' }
  showModal.value = true
}

const openEditModal = (kb) => {
  editingKB.value = kb
  formData.value = {
    name: kb.name,
    description: kb.description || ''
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingKB.value = null
}

const saveKB = async () => {
  if (!formData.value.name.trim()) {
    showToast('请输入知识库名称', 'error')
    return
  }
  
  try {
    if (editingKB.value) {
      await axios.put(`/api/knowledge-bases/${editingKB.value.id}`, formData.value)
      showToast('知识库更新成功')
    } else {
      await axios.post('/api/knowledge-bases', formData.value)
      showToast('知识库创建成功')
    }
    closeModal()
    loadKnowledgeBases()
  } catch (error) {
    showToast(error.response?.data?.detail || '操作失败', 'error')
  }
}

const deleteKB = async (kb) => {
  if (!confirm(`确定要删除知识库 "${kb.name}" 吗？\n这将同时删除该知识库下的所有文件。`)) {
    return
  }
  
  try {
    const response = await axios.delete(`/api/knowledge-bases/${kb.id}`)
    showToast(`删除成功，共删除 ${response.data.deleted_files} 个文件`)
    if (selectedKB.value?.id === kb.id) {
      selectedKB.value = null
      selectedKBName.value = null
      files.value = []
    }
    loadKnowledgeBases()
  } catch (error) {
    showToast('删除失败', 'error')
  }
}

const triggerFileInput = () => {
  if (!fileInput.value) {
    showToast('文件输入组件未初始化', 'error')
    return
  }
  if (!selectedKB.value) {
    showToast('请先选择知识库', 'error')
    return
  }
  fileInput.value.click()
}

const triggerFolderInput = () => {
  if (!folderInput.value) {
    showToast('文件夹输入组件未初始化', 'error')
    return
  }
  if (!selectedKB.value) {
    showToast('请先选择知识库', 'error')
    return
  }
  folderInput.value.click()
}

const handleFileSelect = (event) => {
  const files = event.target.files
  if (files && files.length > 0) {
    uploadFiles(Array.from(files))
  }
  event.target.value = ''
}

const handleFolderSelect = (event) => {
  const files = event.target.files
  if (files && files.length > 0) {
    const allowedExtensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.ppt', '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
    const filteredFiles = Array.from(files).filter(file => {
      const ext = '.' + file.name.split('.').pop().toLowerCase()
      return allowedExtensions.includes(ext)
    })
    
    if (filteredFiles.length === 0) {
      showToast('文件夹中没有支持的文件类型', 'error')
      return
    }
    
    showToast(`文件夹中包含 ${filteredFiles.length} 个支持的文件，开始上传...`, 'info')
    uploadFiles(filteredFiles)
  }
  event.target.value = ''
}

const uploadFiles = async (files) => {
  if (isUploading.value) {
    showToast('正在上传中，请稍候...', 'warning')
    return
  }
  
  isUploading.value = true
  let successCount = 0
  let failCount = 0
  
  for (const file of files) {
    const result = await uploadSingleFile(file)
    if (result) {
      successCount++
    } else {
      failCount++
    }
  }
  
  isUploading.value = false
  
  if (successCount > 0 && failCount === 0) {
    showToast(`成功上传 ${successCount} 个文件`, 'success')
  } else if (successCount > 0 && failCount > 0) {
    showToast(`上传完成：${successCount} 个成功，${failCount} 个失败`, 'warning')
  } else if (failCount > 0) {
    showToast(`全部上传失败，共 ${failCount} 个文件`, 'error')
  }
  
  loadFiles()
}

const uploadSingleFile = async (file) => {
  const allowedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/webp',
    'image/bmp'
  ]
  
  const allowedExtensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.ppt', '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
  const fileExt = '.' + file.name.split('.').pop().toLowerCase()
  
  if (!allowedExtensions.includes(fileExt)) {
    return false
  }
  
  if (file.size > 50 * 1024 * 1024) {
    return false
  }
  
  if (!selectedKB.value) {
    return false
  }
  
  const formDataObj = new FormData()
  formDataObj.append('file', file)
  formDataObj.append('knowledge_base_id', selectedKB.value.id)
  
  try {
    await axios.post('/api/test-case-files', formDataObj, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return true
  } catch (error) {
    console.error(`上传文件 ${file.name} 失败:`, error)
    return false
  }
}

const downloadFile = async (file) => {
  try {
    const response = await axios.get(`/api/test-case-files/${file.id}`, {
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', file.filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    showToast('下载成功')
  } catch (error) {
    showToast('下载失败', 'error')
  }
}

const deleteFile = async (file) => {
  if (!confirm(`确定要删除文件 "${file.filename}" 吗？`)) {
    return
  }
  
  try {
    await axios.delete(`/api/test-case-files/${file.id}`)
    showToast('删除成功')
    loadFiles()
    loadKnowledgeBases()
  } catch (error) {
    showToast('删除失败', 'error')
  }
}

const openEmbeddingModal = (file) => {
  embeddingFile.value = file
  embeddingFormData.value = {
    chunk_size: file.chunk_size || 1000,
    chunk_overlap: file.chunk_overlap || 200
  }
  showEmbeddingModal.value = true
}

const closeEmbeddingModal = () => {
  showEmbeddingModal.value = false
  embeddingFile.value = null
}

const saveEmbeddingSettings = async () => {
  if (!embeddingFile.value) return
  
  const fileId = embeddingFile.value.id
  
  try {
    await axios.put(`/api/test-case-files/${fileId}/embedding-settings`, embeddingFormData.value)
    showToast('Embedding设置已保存')
    closeEmbeddingModal()
    
    await axios.post(`/api/test-case-files/${fileId}/re-embed`, {})
    showToast('Embedding重新生成任务已启动，请稍后查看结果')
    await loadFiles()
    startPolling()
  } catch (error) {
    showToast(error.response?.data?.detail || '操作失败', 'error')
  }
}

const reEmbedFile = async (file) => {
  if (file.reindexing) return
  
  file.reindexing = true
  showToast('正在启动重新生成Embedding任务...', 'success')
  
  try {
    await axios.post(`/api/test-case-files/${file.id}/re-embed`, {})
    showToast('Embedding重新生成任务已启动，请稍后查看结果')
    await loadFiles()
    startPolling()
  } catch (error) {
    showToast(error.response?.data?.detail || '重新生成失败', 'error')
  } finally {
    file.reindexing = false
  }
}

const extractImages = async (file) => {
  if (file.image_extraction_status === 'processing') return
  
  if (file.image_count > 0) {
    if (!confirm(`该文件已提取 ${file.image_count} 张图片，重新提取将删除现有图片。是否继续？`)) {
      return
    }
    file.image_count = 0
  }
  
  file.image_extraction_status = 'processing'
  showToast('正在启动图片提取任务...', 'success')
  
  try {
    const response = await axios.post(`/api/test-case-files/${file.id}/extract-images`, {})
    showToast(response.data.message || '图片提取任务已启动')
    startPolling()
  } catch (error) {
    file.image_extraction_status = 'failed'
    showToast(error.response?.data?.detail || '图片提取失败', 'error')
  }
}

const openImagesModal = async (file) => {
  imagesFile.value = file
  images.value = []
  showImagesModal.value = true
  await loadImages(file.id)
}

const closeImagesModal = () => {
  showImagesModal.value = false
  imagesFile.value = null
  images.value = []
  loadedImages.value = new Set()
  imageElements.clear()
  if (imageObserver) {
    imageObserver.disconnect()
    imageObserver = null
  }
  imageCache.forEach((url) => {
    window.URL.revokeObjectURL(url)
  })
  imageCache.clear()
}

const loadingImages = ref(new Set())
const loadedImages = ref(new Set())
const imageElements = new Map()
let imageObserver = null

const isImageLoading = (imgId) => loadingImages.value.has(imgId)
const isImageLoaded = (imgId) => loadedImages.value.has(imgId)

const setImageRef = (el, imgId) => {
  if (el) {
    imageElements.set(imgId, el)
    setupLazyLoad(imgId)
  }
}

const setupLazyLoad = (imgId) => {
  if (!imageObserver) {
    imageObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const imgId = entry.target.dataset.imgId
            if (imgId && !loadedImages.value.has(imgId) && !loadingImages.value.has(imgId)) {
              const img = images.value.find(i => i.id === imgId)
              if (img) {
                loadImage(img)
              }
            }
          }
        })
      },
      {
        root: document.querySelector('.images-body'),
        rootMargin: '100px',
        threshold: 0.1
      }
    )
  }
  
  const el = imageElements.get(imgId)
  if (el && !el.dataset.observed) {
    el.dataset.imgId = imgId
    el.dataset.observed = 'true'
    imageObserver.observe(el)
  }
}

const loadImages = async (fileId) => {
  try {
    const response = await axios.get(`/api/test-case-files/${fileId}/images`)
    images.value = response.data
  } catch (error) {
    showToast(error.response?.data?.detail || '加载图片失败', 'error')
  }
}

const loadImage = async (img) => {
  if (imageCache.has(img.id)) {
    loadedImages.value = new Set(loadedImages.value).add(img.id)
    return
  }
  
  loadingImages.value = new Set(loadingImages.value).add(img.id)
  try {
    const response = await axios.get(`/api/test-case-files/${img.file_id}/images/${img.id}`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    imageCache.set(img.id, url)
    loadedImages.value = new Set(loadedImages.value).add(img.id)
  } catch (error) {
    console.error('Failed to load image:', error)
  } finally {
    const newSet = new Set(loadingImages.value)
    newSet.delete(img.id)
    loadingImages.value = newSet
  }
}

const imageCache = new Map()

const getCachedImageUrl = (img) => {
  return imageCache.get(img.id) || ''
}

const getImageUrl = async (img) => {
  if (imageCache.has(img.id)) {
    return imageCache.get(img.id)
  }
  
  try {
    const response = await axios.get(`/api/test-case-files/${img.file_id}/images/${img.id}`, {
        responseType: 'blob'
      })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    imageCache.set(img.id, url)
    return url
  } catch (error) {
    showToast(error.response?.data?.detail || '加载图片失败', 'error')
    return ''
  }
}

const previewImage = async (img) => {
  const url = await getImageUrl(img)
  if (url) {
    previewImageUrl.value = url
    showImagePreview.value = true
  }
}

const closeImagePreview = () => {
  showImagePreview.value = false
  previewImageUrl.value = ''
}

const downloadImage = async (img) => {
  try {
    const response = await axios.get(`/api/test-case-files/${img.file_id}/images/${img.id}`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `image_${img.page_number}_${img.image_index}.${img.image_format || 'png'}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    showToast(error.response?.data?.detail || '下载失败', 'error')
  }
}

const deleteImage = async (img) => {
  if (!confirm('确定要删除这张图片吗？')) return
  
  try {
    await axios.delete(`/api/test-case-files/${img.file_id}/images/${img.id}`)
    images.value = images.value.filter(i => i.id !== img.id)
    showToast('图片已删除')
    await loadFiles()
  } catch (error) {
    showToast(error.response?.data?.detail || '删除失败', 'error')
  }
}

const deleteAllImages = async () => {
  if (!confirm(`确定要删除全部 ${images.value.length} 张图片吗？`)) return
  
  deletingAll.value = true
  try {
    await axios.delete(`/api/test-case-files/${imagesFile.value.id}/images`)
    images.value = []
    showToast('全部图片已删除')
    await loadFiles()
  } catch (error) {
    showToast(error.response?.data?.detail || '删除失败', 'error')
  } finally {
    deletingAll.value = false
  }
}

let pollingInterval = null

const startPolling = () => {
  if (pollingInterval) return
  
  pollingInterval = setInterval(async () => {
    const hasProcessing = files.value.some(f => 
      f.embedding_status === 'processing' || f.image_extraction_status === 'processing'
    )
    
    if (!hasProcessing) {
      stopPolling()
      return
    }
    
    if (selectedKB.value) {
      await loadFiles()
    }
  }, 3000)
}

const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

onMounted(() => {
  loadKnowledgeBases()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.knowledge-base-page {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.kb-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.btn-secondary {
  padding: 10px 20px;
  background: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #e5e5e5;
}

.kb-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.kb-card {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.kb-card:hover {
  background: #f0f2ff;
  border-color: #667eea;
}

.kb-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
}

.kb-icon svg {
  width: 24px;
  height: 24px;
  color: #fff;
}

.kb-info {
  flex: 1;
  min-width: 0;
}

.kb-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.kb-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.kb-desc {
  font-size: 13px;
  color: #888;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kb-actions {
  display: flex;
  gap: 8px;
  margin-left: 12px;
}

.btn-icon {
  width: 36px;
  height: 36px;
  border: none;
  background: #fff;
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

.btn-icon.embedding:hover {
  background: #8b5cf6;
}

.btn-icon.reindex:hover {
  background: #f59e0b;
}

.btn-icon.reindex:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #e5e7eb;
}

.btn-icon.extract-images:hover {
  background: #10b981;
}

.btn-icon.extract-images:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #e5e7eb;
}

.btn-icon svg {
  width: 20px;
  height: 20px;
}

.files-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.files-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.files-header h3 {
  font-size: 18px;
  color: #1a1a2e;
}

.upload-buttons {
  display: flex;
  gap: 10px;
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #fff;
  color: #667eea;
  border: 1px solid #667eea;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #f0f4ff;
}

.btn-secondary svg {
  width: 16px;
  height: 16px;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.2s;
}

.file-item:hover {
  background: #f0f2ff;
}

.file-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
}

.file-icon svg {
  width: 28px;
  height: 28px;
}

.file-icon.pdf {
  background: #fee2e2;
  color: #dc2626;
}

.file-icon.excel {
  background: #d1fae5;
  color: #059669;
}

.file-icon.word {
  background: #dbeafe;
  color: #2563eb;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 15px;
  font-weight: 500;
  color: #1a1a2e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.file-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #666;
}

.file-type {
  background: #e5e7eb;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.file-embedding {
  background: #fee2e2;
  color: #dc2626;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.file-embedding.has-embedding {
  background: #d1fae5;
  color: #059669;
}

.file-embedding.processing {
  background: #fef3c7;
  color: #d97706;
}

.file-embedding.failed {
  background: #fee2e2;
  color: #dc2626;
}

.file-images-status {
  background: #f3f4f6;
  color: #6b7280;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.file-images-status.has-images {
  background: #dbeafe;
  color: #2563eb;
}

.file-images-status.has-images:hover {
  background: #bfdbfe;
}

.file-images-status.processing {
  background: #fef3c7;
  color: #d97706;
}

.file-images-status.failed {
  background: #fee2e2;
  color: #dc2626;
}

.loading-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #d97706;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.file-actions {
  display: flex;
  gap: 8px;
  margin-left: 16px;
}

.loading-state {
  text-align: center;
  padding: 48px 24px;
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
  padding: 48px 24px;
}

.empty-state.small {
  padding: 24px;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: #ddd;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 8px;
}

.empty-state p {
  color: #666;
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
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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
  color: #666;
  border-radius: 8px;
}

.btn-close:hover {
  background: #f5f5f5;
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
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input:disabled {
  background: #f5f5f5;
  color: #666;
  cursor: not-allowed;
}

.form-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #888;
}

.embedding-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.status-label {
  font-size: 14px;
  color: #666;
}

.status-value {
  font-size: 14px;
  font-weight: 500;
  color: #dc2626;
}

.status-value.has-data {
  color: #059669;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  z-index: 1001;
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
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.file-images {
  background: #dbeafe;
  color: #2563eb;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.file-images:hover {
  background: #2563eb;
  color: #fff;
}

.btn-icon.view-images:hover {
  background: #2563eb;
}

.btn-icon.extract-images:hover {
  background: #10b981;
}

.images-modal-overlay {
  z-index: 1002;
}

.image-preview-overlay {
  z-index: 1003;
}

.images-modal {
  width: 90%;
  max-width: 900px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.images-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.images-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.images-count {
  font-size: 14px;
  color: #666;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.image-item {
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #eee;
}

.image-preview {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  cursor: pointer;
  overflow: hidden;
}

.image-loading {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.image-loading .loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e0e0e0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  color: #ccc;
}

.image-placeholder svg {
  width: 40px;
  height: 40px;
}

.image-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.image-preview:hover {
  background: #f0f0f0;
}

.image-info {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.image-meta {
  font-size: 12px;
  color: #666;
}

.image-size {
  font-size: 11px;
  color: #999;
}

.image-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  padding: 4px 8px 8px;
}

.btn-icon-sm {
  width: 28px;
  height: 28px;
  border: none;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: all 0.2s;
}

.btn-icon-sm:hover {
  background: #667eea;
  color: #fff;
}

.btn-icon-sm.delete:hover {
  background: #ef4444;
}

.btn-icon-sm svg {
  width: 16px;
  height: 16px;
}

.image-preview-modal {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

.image-preview-modal img {
  max-width: 100%;
  max-height: 90vh;
  display: block;
}

.btn-close-preview {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: all 0.2s;
}

.btn-close-preview:hover {
  background: rgba(0, 0, 0, 0.7);
}

.btn-close-preview svg {
  width: 18px;
  height: 18px;
}
</style>
