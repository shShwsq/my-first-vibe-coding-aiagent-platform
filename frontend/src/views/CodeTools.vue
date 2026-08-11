<template>
  <div class="code-tools-page">
    <div class="tools-list" v-if="!showEditor && !showTestPanel">

      <div class="tools-grid" v-if="filteredTools.length > 0">
        <div class="tool-card" v-for="tool in filteredTools" :key="tool.id">
          <div class="tool-card-header">
            <div class="tool-icon">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z"/>
              </svg>
            </div>
            <div class="tool-info">
              <h3>{{ tool.display_name || tool.name }}</h3>
              <span class="tool-name">{{ tool.name }}()</span>
            </div>
            <div class="tool-status" :class="{ active: tool.is_active }">
              {{ tool.is_active ? '启用' : '禁用' }}
            </div>
          </div>
          <p class="tool-description">{{ tool.description || '暂无描述' }}</p>
          <div class="tool-meta">
            <span class="param-count" v-if="tool.parameters">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z"/>
              </svg>
              {{ tool.parameters.length }} 个参数
            </span>
            <span class="return-type">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M17.41,13.41C17.77,13.41 18.12,13.36 18.5,13.3L15.35,16.44C14.32,17.47 12.77,17.68 11.5,17.04C9.77,16.16 8.5,14.61 8.5,12.5C8.5,11.13 9.63,10 11,10H13C14.1,10 15,9.1 15,8C15,6.9 14.1,6 13,6H10.5C9.63,6 8.84,6.37 8.26,6.97L5.5,9.77C5.19,10.08 5,10.5 5,11V16C5,16.55 5.45,17 6,17H8C8.55,17 9,16.55 9,16V14.5L12,11.5V14C12,14.55 12.45,15 13,15H14C14.55,15 15,14.55 15,14V11.5C15.83,11.81 16.66,12.09 17.41,13.41M21,7V9C21,11.07 19.07,13 17,13H16V11H17C17.97,11 19,10.03 19,9V7C19,6.03 17.97,5 17,5H14V3H17C19.07,3 21,4.93 21,7Z"/>
              </svg>
              返回: {{ tool.return_type || 'dict' }}
            </span>
          </div>
          <div class="tool-actions">
            <button class="btn-icon" @click="testTool(tool)" title="测试运行">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
              </svg>
            </button>
            <button class="btn-icon" @click="editTool(tool)" title="编辑">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
              </svg>
            </button>
            <button class="btn-icon danger" @click="deleteTool(tool)" title="删除">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div class="empty-state" v-else>
        <svg viewBox="0 0 24 24" class="empty-icon">
          <path fill="currentColor" d="M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z"/>
        </svg>
        <h3>暂无代码工具</h3>
        <p>点击上方"新建工具"按钮创建您的第一个代码工具</p>
      </div>
    </div>

    <div class="tool-editor" v-if="showEditor">
      <div class="editor-content">
        <div class="form-section">
          <div class="form-group">
            <label>函数名称 <span class="required">*</span></label>
            <input 
              type="text" 
              v-model="formData.name" 
              placeholder="例如: calculate_sum"
              :disabled="!!editingTool"
              @blur="validateName"
            />
            <span class="hint">只能包含字母、数字和下划线，以字母或下划线开头</span>
            <span class="error" v-if="nameError">{{ nameError }}</span>
          </div>

          <div class="form-group">
            <label>显示名称</label>
            <input type="text" v-model="formData.display_name" placeholder="例如: 计算求和" />
          </div>

          <div class="form-group">
            <label>功能描述</label>
            <textarea v-model="formData.description" placeholder="描述这个工具的功能..." rows="3"></textarea>
          </div>

          <div class="form-group">
            <label>返回类型</label>
            <select v-model="formData.return_type">
              <option value="str">字符串 (str)</option>
              <option value="int">整数 (int)</option>
              <option value="float">浮点数 (float)</option>
              <option value="bool">布尔值 (bool)</option>
              <option value="list">列表 (list)</option>
              <option value="dict">字典 (dict)</option>
              <option value="df">DataFrame (df)</option>
            </select>
          </div>
        </div>

        <div class="form-section">
          <div class="section-header">
            <label>参数定义</label>
            <button class="btn-secondary btn-sm" @click="addParameter">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
              </svg>
              添加参数
            </button>
          </div>

          <div class="parameters-list" v-if="formData.parameters && formData.parameters.length > 0">
            <div class="parameter-item" v-for="(param, index) in formData.parameters" :key="index">
              <input type="text" v-model="param.name" placeholder="参数名" class="param-name" />
              <select v-model="param.type" class="param-type">
                <option value="str">str</option>
                <option value="int">int</option>
                <option value="float">float</option>
                <option value="bool">bool</option>
                <option value="list">list</option>
                <option value="dict">dict</option>
                <option value="df">df</option>
              </select>
              <input type="text" v-model="param.default" placeholder="默认值" class="param-default" />
              <label class="param-required">
                <input type="checkbox" v-model="param.required" />
                必填
              </label>
              <input type="text" v-model="param.description" placeholder="描述" class="param-desc" />
              <button class="btn-icon danger" @click="removeParameter(index)">
                <svg viewBox="0 0 24 24">
                  <path fill="currentColor" d="M19,13H5V11H19V13Z"/>
                </svg>
              </button>
            </div>
          </div>
          <p class="no-params" v-else>暂无参数，点击上方按钮添加</p>
        </div>

        <div class="form-section code-section">
          <div class="section-header">
            <label>Python 代码 <span class="required">*</span></label>
            <button class="btn-secondary btn-sm" @click="insertTemplate">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M19,14H13V20H11V14H5V12H11V6H13V12H19V14Z"/>
              </svg>
              插入模板
            </button>
          </div>
          <div class="code-editor-wrapper">
            <textarea 
              ref="codeEditor"
              v-model="formData.code" 
              class="code-editor"
              placeholder="# 在此编写Python函数代码..."
              spellcheck="false"
            ></textarea>
          </div>
          <span class="hint">函数名必须与上方"函数名称"一致</span>
        </div>

        <div class="form-actions">
          <button class="btn-secondary" @click="closeEditor">取消</button>
          <button class="btn-primary" @click="saveTool" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div class="test-panel" v-if="showTestPanel">
      <div class="test-content">
        <div class="test-info">
          <p class="test-description">{{ testingTool?.description || '暂无描述' }}</p>
          <div class="test-code-preview">
            <pre><code>{{ testingTool?.code }}</code></pre>
          </div>
        </div>

        <div class="test-args" v-if="testingTool?.parameters && testingTool.parameters.length > 0">
          <h4>参数输入</h4>
          <div class="arg-item" v-for="param in testingTool.parameters" :key="param.name">
            <label>
              {{ param.name }}
              <span class="arg-type">({{ param.type }})</span>
              <span class="arg-required" v-if="param.required">*</span>
            </label>
            <div class="password-input-wrapper" v-if="['str', 'int', 'float'].includes(param.type) && param.name.toLowerCase().includes('password')">
              <input 
                :type="hiddenPasswordFields[param.name] ? 'password' : 'text'"
                v-model="testArgs[param.name]"
                :placeholder="param.description || param.default"
                :step="param.type === 'float' ? 'any' : undefined"
              />
              <button 
                class="toggle-password-btn" 
                @click="hiddenPasswordFields[param.name] = !hiddenPasswordFields[param.name]"
                type="button"
                :title="hiddenPasswordFields[param.name] ? '显示密码' : '隐藏密码'"
              >
                <svg v-if="hiddenPasswordFields[param.name]" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z"/>
                </svg>
                <svg v-else viewBox="0 0 24 24">
                  <path fill="currentColor" d="M11.83,9L15,12.16C15,12.11 15,12.05 15,12A3,3 0 0,0 12,9C11.94,9 11.89,9 11.83,9M7.53,9.8L9.08,11.35C9.03,11.56 9,11.77 9,12A3,3 0 0,0 12,15C12.22,15 12.44,14.97 12.65,14.92L14.2,16.47C13.53,16.8 12.79,17 12,17A5,5 0 0,1 7,12C7,11.21 7.2,10.47 7.53,9.8M2,4.27L4.28,6.55L4.73,7C3.08,8.3 1.78,10 1,12C2.73,16.39 7,19.5 12,19.5C13.55,19.5 15.03,19.2 16.38,18.66L16.81,19.08L19.73,22L21,20.73L3.27,3M12,7A5,5 0 0,1 17,12C17,12.64 16.87,13.26 16.64,13.82L19.57,16.75C21.07,15.5 22.27,13.86 23,12C21.27,7.61 17,4.5 12,4.5C10.6,4.5 9.26,4.75 8,5.2L10.17,7.35C10.74,7.13 11.35,7 12,7Z"/>
                </svg>
              </button>
            </div>
            <input 
              v-else-if="['str', 'int', 'float'].includes(param.type)"
              :type="param.type === 'str' ? 'text' : 'number'"
              v-model="testArgs[param.name]"
              :placeholder="param.description || param.default"
              :step="param.type === 'float' ? 'any' : undefined"
            />
            <select v-else-if="param.type === 'bool'" v-model="testArgs[param.name]">
              <option :value="true">true</option>
              <option :value="false">false</option>
            </select>
            <textarea 
              v-else
              v-model="testArgs[param.name]"
              :placeholder="'JSON格式 ' + (param.description || '')"
              rows="3"
            ></textarea>
          </div>
        </div>

        <div class="test-actions">
          <button class="btn-primary" @click="runTest" :disabled="testing">
            <svg viewBox="0 0 24 24" v-if="!testing">
              <path fill="currentColor" d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
            </svg>
            {{ testing ? '运行中...' : '运行测试' }}
          </button>
        </div>

        <div class="test-result" v-if="testResult">
          <h4>运行结果</h4>
          <div class="result-meta">
            <span class="result-status" :class="{ success: testResult.success, error: !testResult.success }">
              {{ testResult.success ? '成功' : '失败' }}
            </span>
            <span class="result-time" v-if="testResult.execution_time">
              耗时: {{ testResult.execution_time.toFixed(3) }}s
            </span>
          </div>
          <div class="result-content" v-if="testResult.success">
            <div v-if="isDataFrame(testResult.result)" class="dataframe-result">
              <div class="df-header">
                <span class="df-type">DataFrame</span>
                <span class="df-shape">{{ testResult.result.shape[0] }} 行 × {{ testResult.result.shape[1] }} 列</span>
              </div>
              <div class="df-columns">
                <span v-for="col in testResult.result.columns" :key="col" class="df-col-tag">
                  {{ col }} <small>({{ testResult.result.dtypes[col] }})</small>
                </span>
              </div>
              <div class="df-table-wrapper">
                <table class="df-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th v-for="col in testResult.result.columns" :key="col">{{ col }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, idx) in testResult.result.head" :key="idx">
                      <td class="row-index">{{ idx }}</td>
                      <td v-for="col in testResult.result.columns" :key="col">{{ formatCellValue(row[col]) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="df-note" v-if="testResult.result.shape[0] > 5">仅显示前 5 行，共 {{ testResult.result.shape[0] }} 行</p>
            </div>
            <pre v-else><code>{{ formatResult(testResult.result) }}</code></pre>
          </div>
          <div class="result-error" v-else>
            <pre><code>{{ testResult.error }}</code></pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import axios from 'axios'

const tools = ref([])
const codeToolsSearchQuery = inject('codeToolsSearchQuery')
const addCodeToolTrigger = inject('addCodeToolTrigger')
const codeToolEditorState = inject('codeToolEditorState')
const showEditor = computed({
  get: () => codeToolEditorState.value.show && codeToolEditorState.value.mode === 'editor',
  set: (val) => {
    codeToolEditorState.value.show = val
    codeToolEditorState.value.mode = 'editor'
  }
})
const showTestPanel = computed({
  get: () => codeToolEditorState.value.show && codeToolEditorState.value.mode === 'test',
  set: (val) => {
    codeToolEditorState.value.show = val
    codeToolEditorState.value.mode = 'test'
  }
})
const editingTool = computed({
  get: () => codeToolEditorState.value.editingTool,
  set: (val) => {
    codeToolEditorState.value.editingTool = val
  }
})
const testingTool = computed({
  get: () => codeToolEditorState.value.testingTool,
  set: (val) => {
    codeToolEditorState.value.testingTool = val
  }
})
const saving = ref(false)
const testing = ref(false)
const nameError = ref('')
const testResult = ref(null)
const testArgs = ref({})
const hiddenPasswordFields = ref({})
const codeEditor = ref(null)

const formData = ref({
  name: '',
  display_name: '',
  description: '',
  code: '',
  parameters: [],
  return_type: 'dict'
})

const filteredTools = computed(() => {
  if (!codeToolsSearchQuery.value) return tools.value
  const query = codeToolsSearchQuery.value.toLowerCase()
  return tools.value.filter(tool => 
    tool.name.toLowerCase().includes(query) ||
    (tool.display_name && tool.display_name.toLowerCase().includes(query)) ||
    (tool.description && tool.description.toLowerCase().includes(query))
  )
})

const loadTools = async () => {
  try {
    const response = await axios.get('/api/code-tools')
    tools.value = response.data
  } catch (error) {
    console.error('加载工具列表失败:', error)
  }
}

const createNewTool = () => {
  codeToolEditorState.value.editingTool = null
  formData.value = {
    name: '',
    display_name: '',
    description: '',
    code: '',
    parameters: [],
    return_type: 'dict'
  }
  nameError.value = ''
  codeToolEditorState.value.show = true
  codeToolEditorState.value.mode = 'editor'
}

const editTool = (tool) => {
  codeToolEditorState.value.editingTool = tool
  formData.value = {
    name: tool.name,
    display_name: tool.display_name || '',
    description: tool.description || '',
    code: tool.code,
    parameters: tool.parameters ? JSON.parse(JSON.stringify(tool.parameters)) : [],
    return_type: tool.return_type || 'dict'
  }
  nameError.value = ''
  codeToolEditorState.value.show = true
  codeToolEditorState.value.mode = 'editor'
}

const closeEditor = () => {
  codeToolEditorState.value.show = false
  codeToolEditorState.value.mode = 'editor'
  codeToolEditorState.value.editingTool = null
}

const validateName = async () => {
  if (!formData.value.name) {
    nameError.value = '函数名称不能为空'
    return false
  }
  
  const pattern = /^[a-zA-Z_][a-zA-Z0-9_]*$/
  if (!pattern.test(formData.value.name)) {
    nameError.value = '函数名格式不正确'
    return false
  }
  
  if (!codeToolEditorState.value.editingTool) {
    try {
      const response = await axios.get(`/api/code-tools/check-name/${formData.value.name}`)
      if (!response.data.available) {
        nameError.value = '该函数名已存在'
        return false
      }
    } catch (error) {
      console.error('检查名称失败:', error)
    }
  }
  
  nameError.value = ''
  return true
}

const addParameter = () => {
  if (!formData.value.parameters) {
    formData.value.parameters = []
  }
  formData.value.parameters.push({
    name: '',
    type: 'str',
    default: '',
    required: true,
    description: ''
  })
}

const removeParameter = (index) => {
  formData.value.parameters.splice(index, 1)
}

const insertTemplate = () => {
  const params = formData.value.parameters || []
  const paramStr = params.map(p => {
    if (p.default) {
      return `${p.name}: ${p.type} = ${p.default}`
    }
    return `${p.name}: ${p.type}`
  }).join(', ')
  
  const template = `def ${formData.value.name || 'my_function'}(${paramStr}):
    """
    ${formData.value.description || '工具功能描述'}
    
    参数:
${params.map(p => `        ${p.name}: ${p.description || '参数描述'}`).join('\n')}
    
    返回:
        ${formData.value.return_type || 'dict'}: 返回值描述
    """
    result = {}
    
    return result`
  
  formData.value.code = template
}

const saveTool = async () => {
  const isValid = await validateName()
  if (!isValid) return
  
  if (!formData.value.code) {
    alert('请输入代码')
    return
  }
  
  saving.value = true
  try {
    const data = {
      name: formData.value.name,
      display_name: formData.value.display_name,
      description: formData.value.description,
      code: formData.value.code,
      parameters: formData.value.parameters.filter(p => p.name),
      return_type: formData.value.return_type
    }
    
    if (codeToolEditorState.value.editingTool) {
      await axios.put(`/api/code-tools/${codeToolEditorState.value.editingTool.id}`, data)
    } else {
      await axios.post('/api/code-tools', data)
    }
    
    await loadTools()
    closeEditor()
  } catch (error) {
    console.error('保存失败:', error)
    alert(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const deleteTool = async (tool) => {
  if (!confirm(`确定要删除工具 "${tool.display_name || tool.name}" 吗？`)) {
    return
  }
  
  try {
    await axios.delete(`/api/code-tools/${tool.id}`)
    await loadTools()
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败')
  }
}

const testTool = (tool) => {
  codeToolEditorState.value.testingTool = tool
  testResult.value = null
  testArgs.value = {}
  hiddenPasswordFields.value = {}
  
  if (tool.parameters) {
    tool.parameters.forEach(param => {
      if (param.default !== undefined && param.default !== '') {
        testArgs.value[param.name] = param.default
      }
    })
  }
  
  codeToolEditorState.value.show = true
  codeToolEditorState.value.mode = 'test'
}

const closeTestPanel = () => {
  codeToolEditorState.value.show = false
  codeToolEditorState.value.mode = 'test'
  codeToolEditorState.value.testingTool = null
  testResult.value = null
  testArgs.value = {}
}

const runTest = async () => {
  testing.value = true
  testResult.value = null
  
  try {
    const processedArgs = {}
    for (const [key, value] of Object.entries(testArgs.value)) {
      if (value !== undefined && value !== '') {
        const param = codeToolEditorState.value.testingTool.parameters?.find(p => p.name === key)
        if (param && ['list', 'dict'].includes(param.type)) {
          try {
            processedArgs[key] = JSON.parse(value)
          } catch {
            processedArgs[key] = value
          }
        } else if (param && param.type === 'int') {
          processedArgs[key] = parseInt(value)
        } else if (param && param.type === 'float') {
          processedArgs[key] = parseFloat(value)
        } else if (param && param.type === 'bool') {
          processedArgs[key] = value === true || value === 'true'
        } else {
          processedArgs[key] = value
        }
      }
    }
    
    const response = await axios.post(`/api/code-tools/${codeToolEditorState.value.testingTool.id}/execute`, {
      arguments: processedArgs
    })
    testResult.value = response.data
  } catch (error) {
    console.error('测试失败:', error)
    testResult.value = {
      success: false,
      error: error.response?.data?.detail || error.message
    }
  } finally {
    testing.value = false
  }
}

const formatResult = (result) => {
  if (typeof result === 'object') {
    return JSON.stringify(result, null, 2)
  }
  return String(result)
}

const isDataFrame = (result) => {
  return result && result.__type__ === 'DataFrame'
}

const formatCellValue = (value) => {
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

watch(addCodeToolTrigger, () => {
  createNewTool()
})

onMounted(() => {
  loadTools()
})
</script>

<style scoped>
.code-tools-page {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
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
  gap: 6px;
  padding: 8px 16px;
  background: #f5f5f5;
  color: #333;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #eee;
}

.btn-secondary svg {
  width: 16px;
  height: 16px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.tool-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.tool-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.tool-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.tool-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.tool-info {
  flex: 1;
}

.tool-info h3 {
  font-size: 16px;
  color: #1a1a2e;
  margin-bottom: 2px;
}

.tool-name {
  font-size: 12px;
  color: #888;
  font-family: 'Consolas', 'Monaco', monospace;
}

.tool-status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: #f5f5f5;
  color: #999;
}

.tool-status.active {
  background: #e8f5e9;
  color: #4caf50;
}

.tool-description {
  color: #666;
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  display: -moz-box;
  -moz-line-clamp: 2;
  -moz-box-orient: vertical;
  display: box;
  line-clamp: 2;
  box-orient: vertical;
  overflow: hidden;
}

.tool-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.tool-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #888;
}

.tool-meta svg {
  width: 14px;
  height: 14px;
}

.tool-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.btn-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-icon svg {
  width: 18px;
  height: 18px;
  color: #666;
}

.btn-icon:hover {
  background: #e0e0e0;
}

.btn-icon.danger:hover {
  background: #ffebee;
}

.btn-icon.danger:hover svg {
  color: #f44336;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: #ddd;
  margin-bottom: 20px;
}

.empty-state h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 8px;
}

.empty-state p {
  color: #999;
  font-size: 14px;
}

.tool-editor, .test-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.editor-content, .test-content {
  padding: 24px;
}

.form-section {
  margin-bottom: 24px;
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

.required {
  color: #f44336;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 12px;
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

.form-group input:disabled {
  background: #f5f5f5;
  color: #999;
}

.hint {
  display: block;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.error {
  display: block;
  font-size: 12px;
  color: #f44336;
  margin-top: 4px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.parameters-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.parameter-item {
  display: grid;
  grid-template-columns: 1fr 80px 100px 60px 1fr 36px;
  gap: 8px;
  align-items: center;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
}

.parameter-item input,
.parameter-item select {
  padding: 8px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 13px;
}

.param-required {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

.param-required input {
  width: auto;
}

.no-params {
  color: #999;
  font-size: 13px;
  text-align: center;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
}

.code-section {
  margin-bottom: 24px;
}

.code-editor-wrapper {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.code-editor {
  width: 100%;
  min-height: 300px;
  padding: 16px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  border: none;
  resize: vertical;
  background: #fafafa;
}

.code-editor:focus {
  outline: none;
  background: #fff;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.test-info {
  margin-bottom: 24px;
}

.test-description {
  color: #666;
  font-size: 14px;
  margin-bottom: 16px;
}

.test-code-preview {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}

.test-code-preview pre {
  margin: 0;
}

.test-code-preview code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #333;
}

.test-args {
  margin-bottom: 24px;
}

.test-args h4 {
  font-size: 14px;
  color: #333;
  margin-bottom: 12px;
}

.arg-item {
  margin-bottom: 12px;
}

.arg-item label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}

.arg-type {
  color: #999;
}

.arg-required {
  color: #f44336;
}

.arg-item input,
.arg-item textarea,
.arg-item select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
}

.password-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input-wrapper input {
  flex: 1;
  padding-right: 40px;
}

.password-input-wrapper input::-ms-reveal,
.password-input-wrapper input::-ms-clear,
.password-input-wrapper input::-webkit-credentials-auto-fill-button,
.password-input-wrapper input::-webkit-caps-lock-indicator {
  display: none;
}

.toggle-password-btn {
  position: absolute;
  right: 8px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  transition: color 0.2s;
}

.toggle-password-btn:hover {
  color: #667eea;
}

.toggle-password-btn svg {
  width: 18px;
  height: 18px;
}

.test-actions {
  margin-bottom: 24px;
}

.test-actions .btn-primary {
  min-width: 140px;
  justify-content: center;
}

.test-result {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
}

.test-result h4 {
  font-size: 14px;
  color: #333;
  margin-bottom: 12px;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.result-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.result-status.success {
  background: #e8f5e9;
  color: #4caf50;
}

.result-status.error {
  background: #ffebee;
  color: #f44336;
}

.result-time {
  font-size: 12px;
  color: #999;
}

.result-content, .result-error {
  background: #fff;
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
}

.result-content pre, .result-error pre {
  margin: 0;
}

.result-content code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #333;
}

.result-error code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #f44336;
}

.dataframe-result {
  font-family: 'Consolas', 'Monaco', monospace;
}

.df-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.df-type {
  font-size: 14px;
  font-weight: 600;
  color: #667eea;
}

.df-shape {
  font-size: 12px;
  color: #666;
}

.df-columns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.df-col-tag {
  display: inline-block;
  background: #f0f0f0;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
  color: #333;
}

.df-col-tag small {
  color: #888;
  margin-left: 4px;
}

.df-table-wrapper {
  overflow-x: auto;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.df-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.df-table th {
  background: #f5f5f5;
  padding: 6px 10px;
  text-align: left;
  border-bottom: 2px solid #ddd;
  position: sticky;
  top: 0;
  white-space: nowrap;
}

.df-table td {
  padding: 4px 10px;
  border-bottom: 1px solid #eee;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.df-table tbody tr:hover {
  background: #fafafa;
}

.row-index {
  color: #999;
  text-align: right;
  width: 40px;
}

.df-note {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
  font-style: italic;
}
</style>
