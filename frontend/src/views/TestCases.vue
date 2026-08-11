<template>
  <div class="test-cases-page">
    <div class="folders-section" v-if="!selectedFolder">
      <div class="folders-list" v-if="folders.length > 0">
        <div 
          v-for="folder in folders" 
          :key="folder.id" 
          class="folder-card"
          @click="selectFolder(folder)"
        >
          <div class="folder-icon">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M10 4H4C2.9 4 2 4.9 2 6V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V8C22 6.9 21.1 6 20 6H12L10 4Z"/>
            </svg>
          </div>
          <div class="folder-info">
            <div class="folder-name">{{ folder.name }}</div>
            <div class="folder-meta">
              <span class="folder-count">{{ folder.case_count || 0 }} 条用例</span>
              <span class="folder-date">{{ formatDate(folder.created_at) }}</span>
            </div>
            <div class="folder-desc" v-if="folder.description">{{ folder.description }}</div>
          </div>
          <div class="folder-actions">
            <button class="btn-icon" @click.stop="openFolderModal(folder)" title="编辑">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
              </svg>
            </button>
            <button class="btn-icon delete" @click.stop="deleteFolder(folder)" title="删除">
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
          <path fill="currentColor" d="M10 4H4C2.9 4 2 4.9 2 6V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V8C22 6.9 21.1 6 20 6H12L10 4Z"/>
        </svg>
        <h3>暂无测试用例文件夹</h3>
        <p>点击上方"新建文件夹"按钮创建您的第一个测试用例文件夹</p>
      </div>
    </div>

    <div class="batch-actions" v-if="selectedFolder && selectedCaseIds.length > 0">
      <span class="selected-count">已选择 {{ selectedCaseIds.length }} 条用例</span>
      <button class="btn-danger" @click="batchDeleteCases">
        <svg viewBox="0 0 24 24">
          <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
        批量删除
      </button>
      <button class="btn-secondary" @click="clearSelection">取消选择</button>
    </div>

    <div class="cases-section" v-if="selectedFolder">
      <div class="table-container" v-if="cases.length > 0">
        <table class="cases-table">
          <thead>
            <tr>
              <th class="col-checkbox">
                <input 
                  type="checkbox" 
                  :checked="isAllSelected"
                  @change="toggleSelectAll"
                  class="checkbox-input"
                >
              </th>
              <th class="col-id">ID</th>
              <th class="col-question">问题</th>
              <th class="col-image">图片</th>
              <th class="col-file">文件</th>
              <th class="col-answer">样例回答</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(caseItem, index) in cases" :key="caseItem.id" :class="{ 'selected-row': selectedCaseIds.includes(caseItem.id) }">
              <td class="col-checkbox">
                <input 
                  type="checkbox" 
                  :value="caseItem.id" 
                  v-model="selectedCaseIds"
                  class="checkbox-input"
                >
              </td>
              <td class="col-id">
                <span class="row-number">{{ caseItem.row_order }}</span>
              </td>
              <td class="col-question">
                <textarea 
                  v-model="caseItem.question" 
                  @blur="updateCase(caseItem)"
                  class="inline-textarea"
                  placeholder="输入问题"
                  rows="2"
                ></textarea>
              </td>
              <td class="col-image">
                <div class="image-cell">
                  <div v-if="caseItem.images && caseItem.images.length > 0" class="images-preview-container">
                    <div v-for="(img, imgIdx) in caseItem.images" :key="img.id" class="image-preview-wrapper">
                      <img 
                        :src="img.preview_url" 
                        class="image-thumbnail"
                        @click="previewImage(img.url)"
                        title="点击预览"
                      />
                      <button class="btn-remove-image" @click="removeImage(caseItem, img.id)" title="移除图片">
                        <svg viewBox="0 0 24 24">
                          <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                      </button>
                    </div>
                    <button class="btn-add-image" @click="openImageSelectModal(caseItem)" title="添加更多图片">
                      <svg viewBox="0 0 24 24">
                        <path fill="currentColor" d="M19 13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
                      </svg>
                    </button>
                  </div>
                  <button v-else class="btn-select-image" @click="openImageSelectModal(caseItem)">
                    <svg viewBox="0 0 24 24">
                      <path fill="currentColor" d="M21 3H3C2 3 1 4 1 5V19C1 20 2 21 3 21H21C22 21 23 20 23 19V5C23 4 22 3 21 3M5 17L8.5 12.5L11 15.5L14.5 11L19 17H5Z"/>
                    </svg>
                    选择图片
                  </button>
                </div>
              </td>
              <td class="col-file">
                <div class="file-cell">
                  <span v-if="caseItem.file_name" class="file-name" :title="caseItem.file_name">
                    {{ truncateFileName(caseItem.file_name) }}
                  </span>
                  <div class="file-actions">
                    <button 
                      :class="['btn-select-file', { 'has-file': caseItem.file_name }]" 
                      @click="openFileSelectModal(caseItem)"
                    >
                      {{ caseItem.file_name ? '更换' : '选择' }}
                    </button>
                    <button 
                      v-if="caseItem.file_name" 
                      class="btn-clear-file"
                      @click="clearCaseFile(caseItem)"
                      title="清除文件"
                    >
                      <svg viewBox="0 0 24 24">
                        <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </td>
              <td class="col-answer">
                <textarea 
                  v-model="caseItem.sample_answer" 
                  @blur="updateCase(caseItem)"
                  class="inline-textarea"
                  placeholder="输入样例回答"
                  rows="2"
                ></textarea>
              </td>
              <td class="col-actions">
                <button class="btn-icon delete" @click="deleteCase(caseItem, index)" title="删除">
                  <svg viewBox="0 0 24 24">
                    <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="empty-state small" v-else>
        <p>暂无测试用例，点击"添加用例"或"从知识库导入"开始</p>
      </div>
    </div>

    <div class="modal-overlay" v-if="showFolderModal" @click.self="closeFolderModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingFolder ? '编辑文件夹' : '新建文件夹' }}</h3>
          <button class="btn-close" @click="closeFolderModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveFolder" class="modal-body">
          <div class="form-group">
            <label>文件夹名称</label>
            <input 
              type="text" 
              v-model="folderForm.name" 
              placeholder="名称不可重复"
              required
            />
          </div>
          <div class="form-group">
            <label>描述（可选）</label>
            <textarea 
              v-model="folderForm.description" 
              placeholder="文件夹用途描述"
              rows="3"
            ></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeFolderModal">取消</button>
            <button type="submit" class="btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>

    <div class="modal-overlay" v-if="showImportModal" @click.self="closeImportModal">
      <div class="modal import-modal">
        <div class="modal-header">
          <h3>从知识库导入</h3>
          <button class="btn-close" @click="closeImportModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>选择知识库</label>
            <select v-model="selectedKBId" @change="loadKBFiles" class="form-select">
              <option value="">请选择知识库</option>
              <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">
                {{ kb.name }}
              </option>
            </select>
          </div>
          
          <div class="form-group" v-if="selectedKBId">
            <label>选择Excel文件</label>
            <div class="files-select-list">
              <div 
                v-for="file in excelFiles" 
                :key="file.id" 
                :class="['file-select-item', { selected: importFileId === file.id }]"
                @click="selectImportFile(file)"
              >
                <div class="file-checkbox">
                  <svg v-if="importFileId === file.id" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M10 17L5 12L6.41 10.58L10 14.17L17.59 6.58L19 8M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2Z"/>
                  </svg>
                </div>
                <span class="file-name">{{ file.filename }}</span>
                <span class="file-type">{{ file.file_type }}</span>
              </div>
            </div>
            <p class="form-hint" v-if="kbFiles.length > 0 && excelFiles.length === 0">
              该知识库中没有Excel文件，请先上传Excel文件到知识库
            </p>
          </div>

          <div v-if="importPreview.loading" class="preview-loading">
            <div class="loading-spinner"></div>
            <span>正在读取文件内容...</span>
          </div>

          <div v-else-if="importPreview.columns.length > 0" class="import-preview-section">
            <h4>数据预览 (共 {{ importPreview.totalRows }} 行)</h4>
            
            <div class="column-mapping">
              <div class="mapping-header">
                <h5>列映射设置（可选择多列拼接）</h5>
                <label class="checkbox-item header-checkbox">
                  <input type="checkbox" v-model="includeColumnHeaders">
                  <span>拼接时添加列名作为表头</span>
                </label>
              </div>
              <div class="mapping-row">
                <label>问题列:</label>
                <div class="multi-select-columns">
                  <label v-for="col in importPreview.columns" :key="'q-'+col" class="checkbox-item">
                    <input type="checkbox" :value="col" v-model="columnMapping.question">
                    <span>{{ col }}</span>
                  </label>
                </div>
              </div>
              <div class="mapping-row">
                <label>样例回答列:</label>
                <div class="multi-select-columns">
                  <label v-for="col in importPreview.columns" :key="'a-'+col" class="checkbox-item">
                    <input type="checkbox" :value="col" v-model="columnMapping.sample_answer">
                    <span>{{ col }}</span>
                  </label>
                </div>
              </div>
              <div class="mapping-row image-file-option">
                <label>图片文件:</label>
                <div class="image-file-select">
                  <select v-model="importImageFileId" @change="loadImportImageFileImages" class="file-select-dropdown">
                    <option value="">不导入图片</option>
                    <option v-for="file in kbFiles" :key="file.id" :value="file.id">
                      {{ file.file_name }}
                    </option>
                  </select>
                  <span v-if="importImageFileImages.length > 0" class="image-count-hint">
                    (共 {{ importImageFileImages.length }} 张图片)
                  </span>
                </div>
              </div>
              <div class="mapping-row start-row-option">
                <label>起始行号:</label>
                <div class="start-row-input">
                  <input 
                    type="number" 
                    v-model.number="importStartRow" 
                    min="1" 
                    class="row-number-input"
                  >
                  <span class="row-hint">从 id = {{ importStartRow }} 开始导入/更新数据</span>
                </div>
              </div>
            </div>

            <div class="preview-table-wrapper">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th v-for="col in importPreview.columns" :key="col">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in importPreview.rows.slice(0, 5)" :key="idx">
                    <td v-for="col in importPreview.columns" :key="col">{{ row[col] || '-' }}</td>
                  </tr>
                </tbody>
              </table>
              <p class="preview-hint" v-if="importPreview.totalRows > 5">
                仅显示前5行，共 {{ importPreview.totalRows }} 行数据
              </p>
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeImportModal">取消</button>
            <button 
              type="button" 
              class="btn-primary" 
              @click="importFromExcel" 
              :disabled="columnMapping.question.length === 0 && columnMapping.sample_answer.length === 0"
            >
              导入数据
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showImageSelectModal" @click.self="closeImageSelectModal">
      <div class="modal image-select-modal">
        <div class="modal-header">
          <h3>选择图片</h3>
          <button class="btn-close" @click="closeImageSelectModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>选择知识库</label>
            <select v-model="imageSelectKBId" @change="loadKBFilesForImage" class="form-select">
              <option value="">请选择知识库</option>
              <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">
                {{ kb.name }}
              </option>
            </select>
          </div>

          <div class="form-group" v-if="imageSelectKBId">
            <label>选择文件</label>
            <select v-model="imageSelectFileId" @change="loadFileImages" class="form-select">
              <option value="">请选择文件</option>
              <option v-for="file in imageSelectFiles" :key="file.id" :value="file.id">
                {{ file.filename }}
              </option>
            </select>
          </div>

          <div class="images-select-grid" v-if="availableImages.length > 0">
            <p class="multi-select-hint">可多选图片</p>
            <div 
              v-for="img in availableImages" 
              :key="img.id"
              :class="['image-select-item', { selected: selectedImageIds.includes(img.id) }]"
              @click="toggleImageSelection(img)"
            >
              <img :src="img.preview_url" :alt="`图片 ${img.image_index}`" />
              <div class="image-select-info">
                第 {{ img.page_number }} 页 / 第 {{ img.image_index }} 张
              </div>
              <div class="image-select-check" v-if="selectedImageIds.includes(img.id)">
                <svg viewBox="0 0 24 24">
                  <path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
              </div>
            </div>
          </div>

          <div class="empty-state small" v-else-if="imageSelectFileId">
            <p>该文件没有提取到图片</p>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeImageSelectModal">取消</button>
            <button type="button" class="btn-primary" @click="confirmImageSelection" :disabled="selectedImageIds.length === 0">
              确认选择 ({{ selectedImageIds.length }}张)
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showFileSelectModal" @click.self="closeFileSelectModal">
      <div class="modal">
        <div class="modal-header">
          <h3>选择文件</h3>
          <button class="btn-close" @click="closeFileSelectModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>选择知识库</label>
            <select v-model="fileSelectKBId" @change="loadKBFilesForFileSelect" class="form-select">
              <option value="">请选择知识库</option>
              <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">
                {{ kb.name }}
              </option>
            </select>
          </div>

          <div class="form-group" v-if="fileSelectKBId">
            <label>选择文件</label>
            <div class="files-select-list">
              <div 
                v-for="file in fileSelectFiles" 
                :key="file.id" 
                :class="['file-select-item', { selected: selectedFileId === file.id }]"
                @click="selectedFileId = file.id"
              >
                <div class="file-checkbox">
                  <svg v-if="selectedFileId === file.id" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M10 17L5 12L6.41 10.58L10 14.17L17.59 6.58L19 8M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2Z"/>
                  </svg>
                </div>
                <span class="file-name">{{ file.filename }}</span>
                <span class="file-type">{{ file.file_type }}</span>
              </div>
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeFileSelectModal">取消</button>
            <button type="button" class="btn-primary" @click="confirmFileSelection">
              确认
            </button>
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
import { ref, onMounted, computed, inject, watch } from 'vue'
import axios from 'axios'

const addTestCaseFolderTrigger = inject('addTestCaseFolderTrigger', ref(0))
const selectedTestCaseFolder = inject('selectedTestCaseFolder', ref(null))
const backToTestCaseFolderList = inject('backToTestCaseFolderList', ref(0))
const importFromKBTrigger = inject('importFromKBTrigger', ref(0))
const addTestCaseTrigger = inject('addTestCaseTrigger', ref(0))
const refreshTestCasesTrigger = inject('refreshTestCasesTrigger', ref(0))

const folders = ref([])
const selectedFolder = ref(null)
const cases = ref([])
const loading = ref(true)
const knowledgeBases = ref([])
const kbFiles = ref([])

const showFolderModal = ref(false)
const editingFolder = ref(null)
const folderForm = ref({
  name: '',
  description: ''
})

const showImportModal = ref(false)
const selectedKBId = ref('')
const importFileId = ref('')
const excelFiles = computed(() => kbFiles.value.filter(f => ['xlsx', 'xls'].includes(f.file_type.toLowerCase())))
const importPreview = ref({
  loading: false,
  columns: [],
  rows: [],
  totalRows: 0
})
const columnMapping = ref({
  question: [],
  sample_answer: []
})
const includeColumnHeaders = ref(false)
const importImageFileId = ref('')
const importImageFileImages = ref([])
const importStartRow = ref(1)
const selectedCaseIds = ref([])

const showImageSelectModal = ref(false)
const imageSelectKBId = ref('')
const imageSelectFileId = ref('')
const imageSelectFiles = ref([])
const availableImages = ref([])
const selectedImageIds = ref([])
const currentEditingCase = ref(null)

const showFileSelectModal = ref(false)
const fileSelectKBId = ref('')
const fileSelectFiles = ref([])
const selectedFileId = ref(null)

const showImagePreview = ref(false)
const previewImageUrl = ref('')

const toast = ref({ show: false, message: '', type: 'success' })

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

const truncateFileName = (name) => {
  if (!name) return ''
  if (name.length > 15) {
    return name.substring(0, 12) + '...'
  }
  return name
}

const loadFolders = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/test-cases/folders')
    folders.value = response.data
  } catch (error) {
    console.error('Failed to load folders:', error)
  } finally {
    loading.value = false
  }
}

const selectFolder = (folder) => {
  selectedFolder.value = folder
  selectedTestCaseFolder.value = folder
  loadCases()
}

const backToFolders = () => {
  selectedFolder.value = null
  selectedTestCaseFolder.value = null
  cases.value = []
}

const loadCases = async () => {
  if (!selectedFolder.value) return
  
  try {
    const response = await axios.get(`/api/test-cases/folders/${selectedFolder.value.id}/cases`)
    cases.value = response.data
    selectedCaseIds.value = []
  } catch (error) {
    console.error('Failed to load cases:', error)
  }
}

const isAllSelected = computed(() => {
  return cases.value.length > 0 && selectedCaseIds.value.length === cases.value.length
})

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedCaseIds.value = []
  } else {
    selectedCaseIds.value = cases.value.map(c => c.id)
  }
}

const clearSelection = () => {
  selectedCaseIds.value = []
}

const batchDeleteCases = async () => {
  if (selectedCaseIds.value.length === 0) return
  
  if (!confirm(`确定要删除选中的 ${selectedCaseIds.value.length} 条用例吗？`)) {
    return
  }
  
  try {
    const response = await axios.post('/api/test-cases/cases/batch-delete', selectedCaseIds.value)
    showToast(`成功删除 ${response.data.deleted_count} 条用例`)
    await loadCases()
  } catch (error) {
    showToast(error.response?.data?.detail || '删除失败', 'error')
  }
}

const openFolderModal = (folder = null) => {
  editingFolder.value = folder
  folderForm.value = {
    name: folder?.name || '',
    description: folder?.description || ''
  }
  showFolderModal.value = true
}

const closeFolderModal = () => {
  showFolderModal.value = false
  editingFolder.value = null
}

const saveFolder = async () => {
  if (!folderForm.value.name.trim()) {
    showToast('请输入文件夹名称', 'error')
    return
  }
  
  try {
    if (editingFolder.value) {
      await axios.put(`/api/test-cases/folders/${editingFolder.value.id}`, folderForm.value)
      showToast('文件夹更新成功')
    } else {
      await axios.post('/api/test-cases/folders', folderForm.value)
      showToast('文件夹创建成功')
    }
    closeFolderModal()
    loadFolders()
  } catch (error) {
    showToast(error.response?.data?.detail || '操作失败', 'error')
  }
}

const deleteFolder = async (folder) => {
  if (!confirm(`确定要删除文件夹 "${folder.name}" 吗？\n这将同时删除该文件夹下的所有测试用例。`)) {
    return
  }
  
  try {
    const response = await axios.delete(`/api/test-cases/folders/${folder.id}`)
    showToast(`删除成功，共删除 ${response.data.deleted_cases} 条用例`)
    loadFolders()
  } catch (error) {
    showToast(error.response?.data?.detail || '删除失败', 'error')
  }
}

const addNewCase = async () => {
  try {
    const response = await axios.post('/api/test-cases/cases', {
      folder_id: selectedFolder.value.id,
      question: '',
      sample_answer: ''
    })
    cases.value.push(response.data)
    showToast('用例添加成功')
  } catch (error) {
    showToast(error.response?.data?.detail || '添加失败', 'error')
  }
}

const updateCase = async (caseItem) => {
  try {
    await axios.put(`/api/test-cases/cases/${caseItem.id}`, {
      question: caseItem.question,
      sample_answer: caseItem.sample_answer
    })
  } catch (error) {
    showToast(error.response?.data?.detail || '更新失败', 'error')
  }
}

const deleteCase = async (caseItem, index) => {
  if (!confirm('确定要删除这条测试用例吗？')) {
    return
  }
  
  try {
    await axios.delete(`/api/test-cases/cases/${caseItem.id}`)
    await loadCases()
    showToast('删除成功')
  } catch (error) {
    showToast(error.response?.data?.detail || '删除失败', 'error')
  }
}

const openImportModal = async () => {
  showImportModal.value = true
  selectedKBId.value = ''
  importFileId.value = ''
  kbFiles.value = []
  importPreview.value = { loading: false, columns: [], rows: [], totalRows: 0 }
  columnMapping.value = { question: [], sample_answer: [] }
  includeColumnHeaders.value = false
  importImageFileId.value = ''
  importImageFileImages.value = []
  
  const maxRowOrder = cases.value.length > 0 
    ? Math.max(...cases.value.map(c => c.row_order)) 
    : 0
  importStartRow.value = maxRowOrder + 1
  
  try {
    const response = await axios.get('/api/test-cases/knowledge-bases')
    knowledgeBases.value = response.data
  } catch (error) {
    console.error('Failed to load knowledge bases:', error)
  }
}

const closeImportModal = () => {
  showImportModal.value = false
}

const loadKBFiles = async () => {
  if (!selectedKBId.value) {
    kbFiles.value = []
    return
  }
  
  try {
    const response = await axios.get(`/api/test-cases/knowledge-bases/${selectedKBId.value}/files`)
    kbFiles.value = response.data
    importFileId.value = ''
  importPreview.value = { loading: false, columns: [], rows: [], totalRows: 0 }
    columnMapping.value = { question: [], sample_answer: [] }
    includeColumnHeaders.value = false
    importImageFileId.value = ''
    importImageFileImages.value = []
    const maxRowOrder = cases.value.length > 0 
      ? Math.max(...cases.value.map(c => c.row_order)) 
      : 0
    importStartRow.value = maxRowOrder + 1
  } catch (error) {
    console.error('Failed to load files:', error)
  }
}

const selectImportFile = async (file) => {
  importFileId.value = file.id
  importPreview.value = { loading: true, columns: [], rows: [], totalRows: 0 }
  
  try {
    const response = await axios.get(`/api/test-cases/files/${file.id}/preview`)
    
    if (response.data.file_type === 'excel') {
      importPreview.value = {
        loading: false,
        columns: response.data.columns,
        rows: response.data.rows,
        totalRows: response.data.total_rows
      }
      
      autoMapColumns(response.data.columns)
    } else {
      showToast('请选择Excel文件进行导入', 'error')
      importPreview.value.loading = false
    }
  } catch (error) {
    showToast(error.response?.data?.detail || '读取文件失败', 'error')
    importPreview.value.loading = false
  }
}

const autoMapColumns = (columns) => {
  const lowerCols = columns.map(c => c.toLowerCase())
  
  const questionKeywords = ['问题', 'question', '提问', 'query', '测试问题']
  const answerKeywords = ['回答', 'answer', '样例回答', '预期回答', 'expected', 'sample_answer']
  
  for (let i = 0; i < columns.length; i++) {
    const col = lowerCols[i]
    if (questionKeywords.some(k => col.includes(k))) {
      columnMapping.value.question.push(columns[i])
    }
    if (answerKeywords.some(k => col.includes(k))) {
      columnMapping.value.sample_answer.push(columns[i])
    }
  }
}

const loadImportImageFileImages = async () => {
  if (!importImageFileId.value) {
    importImageFileImages.value = []
    return
  }
  
  try {
    const response = await axios.get(`/api/test-cases/files/${importImageFileId.value}/images`)
    importImageFileImages.value = response.data
  } catch (error) {
    console.error('Failed to load images:', error)
    importImageFileImages.value = []
  }
}

const importFromExcel = async () => {
  if (!importFileId.value) return
  if (columnMapping.value.question.length === 0 && columnMapping.value.sample_answer.length === 0) {
    showToast('请至少选择一列进行导入', 'error')
    return
  }
  
  const startRowOrder = Math.max(1, importStartRow.value)
  const rowsToImport = importPreview.value.rows
  
  if (rowsToImport.length === 0) {
    showToast('没有可导入的数据', 'error')
    return
  }
  
  try {
    const imageIds = importImageFileImages.value.map(img => img.id)
    
    const casesToCreate = rowsToImport.map((row, idx) => {
      const questionCols = columnMapping.value.question
      const answerCols = columnMapping.value.sample_answer
      
      const formatValue = (col, value) => {
        const strValue = String(value || '').trim()
        if (!strValue) return ''
        return includeColumnHeaders.value ? `${col}：${strValue}` : strValue
      }
      
      const question = questionCols.length > 0
        ? questionCols.map(col => formatValue(col, row[col])).filter(v => v).join('\n')
        : ''
      
      const sampleAnswer = answerCols.length > 0
        ? answerCols.map(col => formatValue(col, row[col])).filter(v => v).join('\n')
        : ''
      
      const caseData = {
        row_order: startRowOrder + idx,
        question: question,
        sample_answer: sampleAnswer
      }
      
      if (imageIds.length > 0) {
        caseData.image_ids = imageIds
      }
      
      return caseData
    })
    
    const response = await axios.post('/api/test-cases/cases/batch', {
      folder_id: selectedFolder.value.id,
      start_row_order: startRowOrder,
      cases: casesToCreate
    })
    
    await loadCases()
    closeImportModal()
    showToast(`成功导入/更新 ${response.data.length} 条用例`)
  } catch (error) {
    showToast(error.response?.data?.detail || '导入失败', 'error')
  }
}

const openImageSelectModal = async (caseItem) => {
  currentEditingCase.value = caseItem
  showImageSelectModal.value = true
  imageSelectKBId.value = ''
  imageSelectFileId.value = ''
  imageSelectFiles.value = []
  availableImages.value = []
  selectedImageIds.value = caseItem.images ? caseItem.images.map(img => img.id) : []
  
  if (knowledgeBases.value.length === 0) {
    try {
      const response = await axios.get('/api/test-cases/knowledge-bases')
      knowledgeBases.value = response.data
    } catch (error) {
      console.error('Failed to load knowledge bases:', error)
    }
  }
}

const closeImageSelectModal = () => {
  showImageSelectModal.value = false
  currentEditingCase.value = null
}

const loadKBFilesForImage = async () => {
  if (!imageSelectKBId.value) {
    imageSelectFiles.value = []
    return
  }
  
  try {
    const response = await axios.get(`/api/test-cases/knowledge-bases/${imageSelectKBId.value}/files`)
    imageSelectFiles.value = response.data
    imageSelectFileId.value = ''
    availableImages.value = []
  } catch (error) {
    console.error('Failed to load files:', error)
  }
}

const loadFileImages = async () => {
  if (!imageSelectFileId.value) {
    availableImages.value = []
    return
  }
  
  try {
    const response = await axios.get(`/api/test-cases/files/${imageSelectFileId.value}/images`)
    availableImages.value = response.data
  } catch (error) {
    console.error('Failed to load images:', error)
  }
}

const toggleImageSelection = (img) => {
  const index = selectedImageIds.value.indexOf(img.id)
  if (index > -1) {
    selectedImageIds.value.splice(index, 1)
  } else {
    selectedImageIds.value.push(img.id)
  }
}

const confirmImageSelection = async () => {
  if (!currentEditingCase.value) return
  
  try {
    const response = await axios.put(`/api/test-cases/cases/${currentEditingCase.value.id}`, {
      image_ids: selectedImageIds.value
    })
    
    const index = cases.value.findIndex(c => c.id === currentEditingCase.value.id)
    if (index > -1) {
      cases.value[index] = response.data
    }
    
    closeImageSelectModal()
    showToast('图片选择成功')
  } catch (error) {
    showToast(error.response?.data?.detail || '选择失败', 'error')
  }
}

const removeImage = async (caseItem, imageId) => {
  try {
    const newImageIds = caseItem.images
      .filter(img => img.id !== imageId)
      .map(img => img.id)
    
    const response = await axios.put(`/api/test-cases/cases/${caseItem.id}`, {
      image_ids: newImageIds
    })
    
    const index = cases.value.findIndex(c => c.id === caseItem.id)
    if (index > -1) {
      cases.value[index] = response.data
    }
    
    showToast('图片已移除')
  } catch (error) {
    showToast(error.response?.data?.detail || '操作失败', 'error')
  }
}

const openFileSelectModal = async (caseItem) => {
  currentEditingCase.value = caseItem
  showFileSelectModal.value = true
  fileSelectKBId.value = ''
  fileSelectFiles.value = []
  selectedFileId.value = null
  
  if (knowledgeBases.value.length === 0) {
    try {
      const response = await axios.get('/api/test-cases/knowledge-bases')
      knowledgeBases.value = response.data
    } catch (error) {
      console.error('Failed to load knowledge bases:', error)
    }
  }
}

const closeFileSelectModal = () => {
  showFileSelectModal.value = false
  currentEditingCase.value = null
}

const loadKBFilesForFileSelect = async () => {
  if (!fileSelectKBId.value) {
    fileSelectFiles.value = []
    return
  }
  
  try {
    const response = await axios.get(`/api/test-cases/knowledge-bases/${fileSelectKBId.value}/files`)
    fileSelectFiles.value = response.data
  } catch (error) {
    console.error('Failed to load files:', error)
  }
}

const confirmFileSelection = async () => {
  if (!currentEditingCase.value) return
  
  if (!selectedFileId.value) {
    showToast('请选择文件', 'error')
    return
  }
  
  try {
    const response = await axios.put(`/api/test-cases/cases/${currentEditingCase.value.id}`, {
      file_id: selectedFileId.value
    })
    
    const index = cases.value.findIndex(c => c.id === currentEditingCase.value.id)
    if (index > -1) {
      cases.value[index] = response.data
    }
    
    closeFileSelectModal()
    showToast('文件选择成功')
  } catch (error) {
    showToast(error.response?.data?.detail || '选择失败', 'error')
  }
}

const clearCaseFile = async (caseItem) => {
  try {
    const response = await axios.put(`/api/test-cases/cases/${caseItem.id}`, {
      file_id: ''
    })
    
    const index = cases.value.findIndex(c => c.id === caseItem.id)
    if (index > -1) {
      cases.value[index] = response.data
    }
    
    showToast('文件已清除')
  } catch (error) {
    showToast(error.response?.data?.detail || '清除失败', 'error')
  }
}

const previewImage = (imageUrl) => {
  if (imageUrl) {
    previewImageUrl.value = imageUrl
    showImagePreview.value = true
  }
}

const closeImagePreview = () => {
  showImagePreview.value = false
  previewImageUrl.value = ''
}

watch(addTestCaseFolderTrigger, (newVal) => {
  if (newVal > 0) {
    openFolderModal()
  }
})

watch(backToTestCaseFolderList, (newVal) => {
  if (newVal > 0) {
    backToFolders()
  }
})

watch(importFromKBTrigger, (newVal) => {
  if (newVal > 0 && selectedFolder.value) {
    openImportModal()
  }
})

watch(addTestCaseTrigger, (newVal) => {
  if (newVal > 0 && selectedFolder.value) {
    addNewCase()
  }
})

watch(selectedTestCaseFolder, (newVal) => {
  if (newVal && !selectedFolder.value) {
    selectedFolder.value = newVal
    loadCases()
  }
  if (newVal === null && selectedFolder.value) {
    selectedFolder.value = null
    cases.value = []
    selectedCaseIds.value = []
    loadFolders()
  }
})

watch(refreshTestCasesTrigger, (newVal) => {
  if (newVal > 0 && selectedFolder.value) {
    loadCases()
    showToast('测试用例已更新', 'success')
  }
})

onMounted(() => {
  loadFolders()
})
</script>

<style scoped>
.test-cases-page {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.folders-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.folder-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.2s;
}

.folder-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.folder-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.folder-icon svg {
  width: 24px;
  height: 24px;
  color: #fff;
}

.folder-info {
  flex: 1;
  min-width: 0;
}

.folder-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.folder-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #666;
}

.folder-desc {
  font-size: 13px;
  color: #888;
  margin-top: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.folder-actions {
  display: flex;
  gap: 4px;
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
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: #ccc;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  color: #666;
  margin-bottom: 8px;
}

.empty-state p {
  color: #999;
  font-size: 14px;
}

.empty-state.small {
  padding: 40px 20px;
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
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #fff;
  color: #666;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #f5f5f5;
  border-color: #ccc;
}

.btn-secondary svg {
  width: 18px;
  height: 18px;
}

.btn-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: #f0f0f0;
  color: #333;
}

.btn-icon.delete:hover {
  background: #fee2e2;
  color: #ef4444;
}

.btn-icon svg {
  width: 18px;
  height: 18px;
}

.cases-section {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.table-container {
  overflow-x: auto;
}

.batch-actions {
  position: sticky;
  top: -24px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
  margin-bottom: 16px;
}

.selected-count {
  font-weight: 500;
  color: #856404;
}

.btn-danger {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-danger svg {
  width: 16px;
  height: 16px;
}

.col-checkbox {
  width: 40px;
  text-align: center;
}

.checkbox-input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.selected-row {
  background: #f0f7ff !important;
}

.cases-table {
  width: 100%;
  border-collapse: collapse;
}

.cases-table th {
  text-align: left;
  padding: 12px 16px;
  background: #f8f9fa;
  font-weight: 600;
  font-size: 13px;
  color: #666;
  border-bottom: 1px solid #eee;
}

.cases-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: top;
}

.col-id {
  width: 60px;
  text-align: center;
}

.row-number {
  font-weight: 600;
  color: #667eea;
  font-size: 14px;
}

.col-question {
  min-width: 200px;
}

.col-image {
  min-width: 120px;
  max-width: 250px;
}

.col-file {
  width: 150px;
}

.col-answer {
  min-width: 200px;
}

.col-actions {
  width: 60px;
}

.inline-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.2s;
}

.inline-input:hover {
  border-color: #e0e0e0;
}

.inline-input:focus {
  outline: none;
  border-color: #667eea;
  background: #fff;
}

.inline-textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 60px;
  transition: all 0.2s;
}

.inline-textarea:hover {
  border-color: #e0e0e0;
}

.inline-textarea:focus {
  outline: none;
  border-color: #667eea;
  background: #fff;
}

.image-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.images-preview-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: flex-start;
  max-height: 204px;
  overflow-y: auto;
  padding: 2px;
}

.image-preview-wrapper {
  position: relative;
}

.image-thumbnail {
  width: 80px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid #e0e0e0;
}

.image-thumbnail:hover {
  border-color: #667eea;
}

.btn-remove-image {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ef4444;
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-preview-wrapper:hover .btn-remove-image {
  opacity: 1;
}

.btn-remove-image svg {
  width: 12px;
  height: 12px;
}

.btn-add-image {
  width: 40px;
  height: 60px;
  border-radius: 6px;
  background: #f8f9fa;
  border: 1px dashed #ddd;
  color: #999;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-add-image:hover {
  background: #f0f0f0;
  border-color: #4a90d9;
  color: #4a90d9;
}

.btn-add-image svg {
  width: 20px;
  height: 20px;
}

.btn-select-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px;
  background: #f8f9fa;
  border: 1px dashed #ddd;
  border-radius: 6px;
  color: #999;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-select-image:hover {
  background: #f0f0f0;
  border-color: #ccc;
  color: #666;
}

.btn-select-image svg {
  width: 24px;
  height: 24px;
}

.file-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-size: 13px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-select-file {
  padding: 6px 10px;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-select-file:hover {
  background: #f0f0f0;
}

.btn-select-file.has-file {
  background: #e8f4f8;
  border-color: #667eea;
  color: #667eea;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-clear-file {
  width: 24px;
  height: 24px;
  padding: 0;
  background: #ffebee;
  border: 1px solid #ffcdd2;
  border-radius: 4px;
  color: #c62828;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-clear-file:hover {
  background: #ffcdd2;
}

.btn-clear-file svg {
  width: 14px;
  height: 14px;
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
  border-radius: 12px;
  width: 90%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal.import-modal,
.modal.image-select-modal {
  max-width: 600px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  font-size: 18px;
  color: #1a1a2e;
}

.btn-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #f0f0f0;
  color: #333;
}

.btn-close svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.form-group input,
.form-group textarea,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
}

.files-select-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.file-select-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
}

.file-select-item:last-child {
  border-bottom: none;
}

.file-select-item:hover {
  background: #f8f9fa;
}

.file-select-item.selected {
  background: #e8f4f8;
}

.file-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #ddd;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-select-item.selected .file-checkbox {
  background: #667eea;
  border-color: #667eea;
}

.file-checkbox svg {
  width: 14px;
  height: 14px;
  color: #fff;
}

.file-select-item .file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-select-item .file-type {
  font-size: 12px;
  color: #999;
  background: #f0f0f0;
  padding: 2px 8px;
  border-radius: 4px;
}

.images-select-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
  padding: 4px;
}

.multi-select-hint {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
  text-align: center;
}

.image-select-item {
  position: relative;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.image-select-item:hover {
  border-color: #ccc;
}

.image-select-item.selected {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.image-select-item img {
  width: 100%;
  height: 80px;
  object-fit: cover;
}

.image-select-info {
  padding: 6px;
  font-size: 11px;
  color: #666;
  text-align: center;
  background: #f8f9fa;
}

.image-select-check {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #667eea;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-select-check svg {
  width: 16px;
  height: 16px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.image-preview-overlay {
  background: rgba(0, 0, 0, 0.8);
}

.image-preview-modal {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
}

.image-preview-modal img {
  max-width: 100%;
  max-height: 90vh;
  border-radius: 8px;
}

.btn-close-preview {
  position: absolute;
  top: -40px;
  right: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #fff;
  transition: all 0.2s;
}

.btn-close-preview:hover {
  background: rgba(255, 255, 255, 0.3);
}

.btn-close-preview svg {
  width: 20px;
  height: 20px;
}

.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  background: #333;
  color: #fff;
  border-radius: 8px;
  font-size: 14px;
  z-index: 2000;
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

.preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  color: #666;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e0e0e0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.import-preview-section {
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 20px;
}

.import-preview-section h4 {
  font-size: 15px;
  color: #333;
  margin-bottom: 16px;
}

.column-mapping {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.column-mapping h5 {
  font-size: 14px;
  color: #333;
  margin-bottom: 12px;
}

.mapping-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.mapping-row:last-child {
  margin-bottom: 0;
}

.mapping-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #e0e0e0;
}

.mapping-header h5 {
  margin: 0;
}

.header-checkbox {
  background: #f0f7ff;
  border-color: #4a90d9;
  width: auto;
}

.header-checkbox span {
  color: #4a90d9;
}

.mapping-row.image-file-option {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed #e0e0e0;
}

.image-file-select {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-select-dropdown {
  flex: 1;
  max-width: 300px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
  cursor: pointer;
}

.file-select-dropdown:focus {
  outline: none;
  border-color: #4a90d9;
}

.image-count-hint {
  font-size: 12px;
  color: #667eea;
  font-weight: 500;
}

.mapping-row.start-row-option {
  margin-top: 12px;
}

.start-row-input {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.row-number-input {
  width: 80px;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  text-align: center;
}

.row-number-input:focus {
  outline: none;
  border-color: #4a90d9;
}

.row-hint {
  font-size: 12px;
  color: #888;
}

.mapping-row label {
  width: 100px;
  font-size: 13px;
  color: #666;
  flex-shrink: 0;
  padding-top: 6px;
}

.multi-select-columns {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.checkbox-item:hover {
  border-color: #4a90d9;
  background: #f0f7ff;
}

.checkbox-item input[type="checkbox"] {
  margin: 0;
  accent-color: #4a90d9;
}

.checkbox-item input[type="checkbox"]:checked + span {
  color: #4a90d9;
  font-weight: 500;
}

.form-select-sm {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
}

.form-select-sm:focus {
  outline: none;
  border-color: #667eea;
}

.preview-table-wrapper {
  overflow-x: auto;
  border: 1px solid #eee;
  border-radius: 8px;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.preview-table th {
  background: #f8f9fa;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #eee;
  white-space: nowrap;
}

.preview-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-table tr:last-child td {
  border-bottom: none;
}

.preview-hint {
  font-size: 12px;
  color: #999;
  text-align: center;
  padding: 8px;
  background: #f8f9fa;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}
</style>
