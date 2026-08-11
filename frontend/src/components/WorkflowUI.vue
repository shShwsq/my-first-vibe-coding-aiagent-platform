<template>
  <div>
    <Teleport to="body">
      <div
        v-if="showInModal && mainModalVisible"
        class="modal-overlay"
        @click="closeMainModal"
      >
        <div
          class="modal-container main-ui-modal"
          @click.stop
        >
          <div class="modal-header">
            <h3>{{ uiConfig.name || '结果' }}</h3>
            <button class="modal-close" @click="closeMainModal">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="workflow-ui-container" :style="containerStyle">
              <div 
                class="ui-buttons" 
                v-if="uiConfig.buttons && uiConfig.buttons.length > 0"
                :style="buttonsStyle"
              >
                <button
                  v-for="btn in uiConfig.buttons"
                  :key="btn.id"
                  class="ui-button"
                  :style="getButtonStyle(btn.style)"
                  @click="handleButtonClick(btn)"
                >
                  {{ btn.label }}
                </button>
              </div>
              
              <div 
                class="ui-charts" 
                v-if="visibleCharts.length > 0"
                :style="chartsStyle"
              >
                <div
                  v-for="chart in visibleCharts"
                  :key="chart.id"
                  class="ui-chart"
                  :style="getChartStyle(chart)"
                >
                  <h4 v-if="chart.options?.title?.text" class="chart-title">
                    {{ chart.options.title.text }}
                  </h4>
                  <img
                    v-if="chart.image_url"
                    :src="getChartSrc(chart.image_url)"
                    :alt="chart.options?.title?.text || 'Chart'"
                    class="chart-image"
                  />
                  <div v-else class="chart-placeholder">
                    <p>图表: {{ chart.type }}</p>
                    <p class="chart-data">{{ JSON.stringify(chart.data, null, 2) }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
    
    <div v-if="!showInModal" class="workflow-ui-container" :style="containerStyle">
      <div 
        class="ui-buttons" 
        v-if="uiConfig.buttons && uiConfig.buttons.length > 0"
        :style="buttonsStyle"
      >
        <button
          v-for="btn in uiConfig.buttons"
          :key="btn.id"
          class="ui-button"
          :style="getButtonStyle(btn.style)"
          @click="handleButtonClick(btn)"
        >
          {{ btn.label }}
        </button>
      </div>
      
      <div 
        class="ui-charts" 
        v-if="visibleCharts.length > 0"
        :style="chartsStyle"
      >
        <div
          v-for="chart in visibleCharts"
          :key="chart.id"
          class="ui-chart"
          :style="getChartStyle(chart)"
        >
          <h4 v-if="chart.options?.title?.text" class="chart-title">
            {{ chart.options.title.text }}
          </h4>
          <img
            v-if="chart.image_url"
            :src="getChartSrc(chart.image_url)"
            :alt="chart.options?.title?.text || 'Chart'"
            class="chart-image"
          />
          <div v-else class="chart-placeholder">
            <p>图表: {{ chart.type }}</p>
            <p class="chart-data">{{ JSON.stringify(chart.data, null, 2) }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <Teleport to="body">
      <div
        v-for="modal in activeModals"
        :key="modal._uid"
        class="modal-overlay"
        @click="handleOverlayClick(modal)"
      >
        <div
          class="modal-container"
          :style="getModalStyle(modal)"
          @click.stop
        >
          <div class="modal-header">
            <h3>{{ modal.title }}</h3>
            <button class="modal-close" @click="closeModal(modal.id)">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <div :class="modal._scopeClass">
              <MarkdownRenderer :content="processModalContent(modal.content)" />
            </div>
          </div>
        </div>
      </div>
    </Teleport>
    
    <component :is="'style'" v-for="modal in activeModals" :key="'style-' + modal._uid">
      {{ modal._scopedCss }}
    </component>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import MarkdownRenderer from './MarkdownRenderer.vue'

const props = defineProps({
  uiConfig: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['button-click', 'close', 'send-text'])

const layout = computed(() => props.uiConfig.layout || {})

const showInModal = computed(() => props.uiConfig.show_in_modal === true)

const mainModalVisible = ref(true)

const closeMainModal = () => {
  mainModalVisible.value = false
  emit('close')
}

watch(() => props.uiConfig, () => {
  mainModalVisible.value = true
}, { deep: true })

const containerStyle = computed(() => ({
  flexDirection: layout.value.direction || 'column',
  gap: layout.value.gap || '16px',
  padding: layout.value.padding || '12px',
  alignItems: layout.value.align || 'stretch',
  justifyContent: layout.value.justify || 'flex-start'
}))

const buttonsStyle = computed(() => {
  const btnGroup = layout.value.button_group || {}
  return {
    justifyContent: btnGroup.align || 'flex-start',
    marginBottom: layout.value.direction === 'column' ? '0' : '0'
  }
})

const chartsStyle = computed(() => ({
  flexDirection: layout.value.chart_direction || 'row',
  gap: layout.value.chart_gap || layout.value.gap || '16px'
}))

const getChartStyle = (chart) => ({
  width: chart.width || layout.value.chart_width || 'auto',
  height: chart.height || layout.value.chart_height || 'auto',
  minWidth: layout.value.chart_min_width || '200px'
})

const activeModals = ref([])
const modalData = ref({})
let modalIdCounter = 0

const visibleCharts = computed(() => {
  if (!props.uiConfig.charts) return []
  return props.uiConfig.charts.filter(chart => chart.visible !== false)
})

const getChartSrc = (image_url) => {
  if (!image_url) return ''
  if (image_url.startsWith('data:')) {
    return image_url
  }
  if (image_url.startsWith('http://') || image_url.startsWith('https://') || image_url.startsWith('/')) {
    const separator = image_url.includes('?') ? '&' : '?'
    return `${image_url}${separator}_t=${Date.now()}`
  }
  if (/^[A-Za-z0-9+/=]+$/.test(image_url) && image_url.length > 100) {
    return `data:image/png;base64,${image_url}`
  }
  return image_url
}

const getButtonStyle = (style) => {
  if (!style) return {}
  return {
    background: style.background || '#4CAF50',
    color: style.color || '#ffffff',
    borderRadius: style.border_radius || '6px',
    padding: style.padding || '8px 16px',
    fontSize: style.font_size || '14px',
    fontWeight: style.font_weight || '500',
    border: style.border || 'none',
    cursor: 'pointer',
    transition: 'all 0.2s ease'
  }
}

const getModalStyle = (modal) => {
  return {
    width: modal.width || '600px',
    height: modal.height || 'auto',
    maxHeight: modal.height === 'auto' ? '80vh' : modal.height
  }
}

const scopeCss = (css, scope) => {
  if (!css) return ''
  return css.replace(/([^\r\n,{}]+)(,(?=[^}]*{)|\s*{)/g, (match, selector, separator) => {
    const trimmedSelector = selector.trim()
    if (trimmedSelector.startsWith('@') || trimmedSelector === '') {
      return match
    }
    const selectors = trimmedSelector.split(/\s+/).filter(s => s)
    const scopedSelector = selectors.map(s => {
      if (s.startsWith(':')) {
        return `${scope}${s}`
      }
      return `${scope} ${s}`
    }).join(' ')
    return `${scopedSelector}${separator}`
  })
}

const handleButtonClick = (btn) => {
  if (btn.action) {
    if (btn.action.type === 'show_modal') {
      modalData.value = btn.action.data || {}
      const modal = props.uiConfig.modals?.find(m => m.id === btn.action.modal_id)
      if (modal) {
        modalIdCounter++
        const scopeClass = `modal-scope-${modalIdCounter}`
        const scopedCss = scopeCss(modal.css, `.${scopeClass}`)
        
        activeModals.value.push({ 
          ...modal, 
          _uid: Date.now() + modalIdCounter,
          _scopeClass: scopeClass,
          _scopedCss: scopedCss
        })
        
        if (modal.script) {
          setTimeout(() => {
            try {
              const script = new Function('modalData', modal.script)
              script(modalData.value)
            } catch (e) {
              console.error('Modal script error:', e)
            }
          }, 100)
        }
      }
    } else if (btn.action.type === 'close_modal') {
      closeModal(btn.action.modal_id)
    } else if (btn.action.type === 'download') {
      handleDownload(btn.action)
    } else if (btn.action.type === 'send_text') {
      emit('send-text', btn.action.text || '')
    }
  }
  
  emit('button-click', btn)
}

const handleDownload = (action) => {
  let url = action.url
  if (!url) return
  
  if (!url.startsWith('http://') && !url.startsWith('https://') && !url.startsWith('/')) {
    url = `/api/workflow-files/${url.replace(/\\/g, '/')}`
  }
  
  const filename = action.filename || url.split('/').pop() || 'download'
  
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const closeModal = (modalId) => {
  const index = activeModals.value.findIndex(m => m.id === modalId)
  if (index > -1) {
    activeModals.value.splice(index, 1)
  }
}

const handleOverlayClick = (modal) => {
  if (modal.close_on_overlay !== false) {
    closeModal(modal.id)
  }
}

const resolveNestedTemplate = (text) => {
  let result = text
  let maxIterations = 10
  let iteration = 0
  
  while ((result.includes('{{ctx:') || result.includes('{{image:')) && iteration < maxIterations) {
    const oldResult = result
    
    result = result.replace(/\{\{ctx:([^{}]+)\}\}/g, (match, varName) => {
      const value = props.uiConfig.context?.[varName.trim()]
      if (value !== undefined && value !== null) {
        if (typeof value === 'object') {
          return JSON.stringify(value, null, 2)
        }
        return String(value)
      }
      return match
    })
    
    if (result === oldResult) break
    iteration++
  }
  
  return result
}

const processModalContent = (content) => {
  if (!content) return ''
  
  let processed = resolveNestedTemplate(content)
  
  const chartPattern = /\{\{chart:([^}]+)\}\}/g
  processed = processed.replace(chartPattern, (match, chartId) => {
    const chart = props.uiConfig.charts?.find(c => c.id === chartId)
    if (chart) {
      if (chart.image_url) {
        const src = getChartSrc(chart.image_url)
        return `<img src="${src}" alt="Chart" style="max-width: 100%; height: auto;" />`
      } else {
        return `<div class="chart-placeholder" style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
          <p>图表: ${chart.type}</p>
        </div>`
      }
    }
    return match
  })
  
  const imagePattern = /\{\{image:([^}]+)\}\}/g
  processed = processed.replace(imagePattern, (match, path) => {
    const resolvedPath = resolveNestedTemplate(path.trim())
    const src = getImageSrc(resolvedPath)
    return `<img src="${src}" alt="Image" style="max-width: 100%; height: auto;" />`
  })
  
  return processed
}

const getImageSrc = (path) => {
  if (!path) return ''
  if (path.startsWith('data:')) {
    return path
  }
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  let url = path.startsWith('/') ? path : `/api/workflow-files/${path.replace(/\\/g, '/')}`
  const separator = url.includes('?') ? '&' : '?'
  return `${url}${separator}_t=${Date.now()}`
}

const handleKeyDown = (e) => {
  if (e.key === 'Escape' && activeModals.value.length > 0) {
    const lastModal = activeModals.value[activeModals.value.length - 1]
    closeModal(lastModal.id)
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})

defineExpose({
  showModal: (modalId) => {
    const modal = props.uiConfig.modals?.find(m => m.id === modalId)
    if (modal) {
      modalIdCounter++
      const scopeClass = `modal-scope-${modalIdCounter}`
      const scopedCss = scopeCss(modal.css, `.${scopeClass}`)
      
      activeModals.value.push({ 
        ...modal, 
        _uid: Date.now() + modalIdCounter,
        _scopeClass: scopeClass,
        _scopedCss: scopedCss
      })
    }
  },
  closeModal
})
</script>

<style scoped>
.workflow-ui-container {
  display: flex;
  margin-top: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  backface-visibility: visible;
  transform: translateZ(0);
}

.ui-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.ui-buttons:last-child {
  margin-bottom: 0;
}

.ui-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: opacity 0.2s ease;
  backface-visibility: visible;
}

.ui-button:hover {
  opacity: 0.9;
}

.ui-charts {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.ui-chart {
  flex: 1;
  min-width: 200px;
  max-width: 100%;
}

.chart-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.chart-image {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-placeholder {
  padding: 20px;
  background: #fff;
  border: 1px dashed #ddd;
  border-radius: 8px;
  text-align: center;
}

.chart-placeholder p {
  margin: 0;
  color: #666;
}

.chart-data {
  margin-top: 8px !important;
  font-size: 12px;
  font-family: monospace;
  text-align: left;
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
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
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-container {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideIn 0.2s ease;
}

.main-ui-modal {
  width: 90%;
  max-width: 900px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #666;
  transition: color 0.2s;
}

.modal-close:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}
</style>
