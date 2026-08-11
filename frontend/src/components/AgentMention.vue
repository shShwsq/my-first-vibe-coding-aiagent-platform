<template>
  <div class="agent-mention-wrapper" ref="wrapperRef">
    <div class="input-container">
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="handleInput"
        @keydown="handleKeydown"
        @blur="handleBlur"
        @focus="handleFocus"
        :placeholder="placeholder"
        :rows="rows"
        class="mention-textarea"
      ></textarea>
    </div>
    
    <div ref="mirrorRef" class="textarea-mirror"></div>
    
    <Teleport to="body">
      <div
        v-if="showDropdown && filteredAgents.length > 0"
        class="agent-dropdown"
        :style="dropdownStyle"
        ref="dropdownRef"
      >
        <div class="dropdown-list">
          <div
            v-for="(agent, index) in filteredAgents"
            :key="(agent.type || 'agent') + '-' + (agent.id || agent.name)"
            class="dropdown-item"
            :class="{ active: selectedIndex === index }"
            @mousedown.prevent="selectAgent(agent)"
            @mouseover="selectedIndex = index"
          >
            <span class="agent-name">{{ agent.name }}</span>
            <span v-if="agent.type === 'workflow_agent'" class="agent-type-badge">工作流</span>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  agents: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: '输入消息...'
  },
  rows: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'resize'])

const textareaRef = ref(null)
const wrapperRef = ref(null)
const dropdownRef = ref(null)
const mirrorRef = ref(null)
const showDropdown = ref(false)
const selectedIndex = ref(0)
const mentionStartIndex = ref(-1)
const searchText = ref('')
const dropdownStyle = ref({})

const filteredAgents = computed(() => {
  console.log('props.agents:', props.agents)
  if (!searchText.value) {
    return props.agents
  }
  return props.agents.filter(agent =>
    agent.name.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

const handleInput = (event) => {
  const value = event.target.value
  emit('update:modelValue', value)
  
  autoResizeTextarea()
  checkForMention(value, event.target.selectionStart)
}

const autoResizeTextarea = () => {
  const textarea = textareaRef.value
  if (!textarea) return
  
  textarea.style.height = 'auto'
  const newHeight = Math.min(textarea.scrollHeight, 120)
  textarea.style.height = newHeight + 'px'
  emit('resize', newHeight)
}

const checkForMention = (value, cursorPos) => {
  const textBeforeCursor = value.substring(0, cursorPos)
  const lastAtIndex = textBeforeCursor.lastIndexOf('@')
  
  console.log('checkForMention:', { value, cursorPos, lastAtIndex, agentsCount: props.agents.length })
  
  if (lastAtIndex !== -1) {
    const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1)
    const hasSpaceAfterAt = textAfterAt.includes(' ')
    
    console.log('Found @:', { textAfterAt, hasSpaceAfterAt })
    
    if (!hasSpaceAfterAt) {
      mentionStartIndex.value = lastAtIndex
      searchText.value = textAfterAt
      showDropdown.value = true
      selectedIndex.value = 0
      updateDropdownPosition()
      console.log('showDropdown set to true, filteredAgents:', filteredAgents.value.length)
      return
    }
  }
  
  showDropdown.value = false
  mentionStartIndex.value = -1
  searchText.value = ''
}

const updateDropdownPosition = async () => {
  await nextTick()
  
  const textarea = textareaRef.value
  const mirror = mirrorRef.value
  if (!textarea || !mirror || mentionStartIndex.value === -1) return
  
  const textareaStyle = window.getComputedStyle(textarea)
  mirror.style.width = textarea.clientWidth + 'px'
  mirror.style.font = textareaStyle.font
  mirror.style.lineHeight = textareaStyle.lineHeight
  mirror.style.padding = textareaStyle.padding
  mirror.style.border = textareaStyle.border
  mirror.style.boxSizing = textareaStyle.boxSizing
  mirror.style.wordWrap = 'break-word'
  mirror.style.whiteSpace = 'pre-wrap'
  
  const textBeforeAt = props.modelValue.substring(0, mentionStartIndex.value)
  const textAfterAt = props.modelValue.substring(mentionStartIndex.value)
  
  mirror.innerHTML = ''
  
  const textSpan = document.createElement('span')
  textSpan.textContent = textBeforeAt
  mirror.appendChild(textSpan)
  
  const atSpan = document.createElement('span')
  atSpan.textContent = '@'
  atSpan.id = 'at-marker'
  mirror.appendChild(atSpan)
  
  const remainingSpan = document.createElement('span')
  remainingSpan.textContent = textAfterAt.substring(1)
  mirror.appendChild(remainingSpan)
  
  const atRect = atSpan.getBoundingClientRect()
  const textareaRect = textarea.getBoundingClientRect()
  
  dropdownStyle.value = {
    position: 'fixed',
    left: atRect.left + 'px',
    bottom: (window.innerHeight - atRect.top + 4) + 'px',
    minWidth: '150px',
    maxHeight: '200px',
    zIndex: 9999
  }
}

const handleKeydown = (event) => {
  if (showDropdown.value && filteredAgents.value.length > 0) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      selectedIndex.value = Math.min(
        selectedIndex.value + 1,
        filteredAgents.value.length - 1
      )
      scrollToSelected()
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
      scrollToSelected()
    } else if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      selectAgent(filteredAgents.value[selectedIndex.value])
    } else if (event.key === 'Escape') {
      showDropdown.value = false
    } else if (event.key === 'Enter' && event.shiftKey) {
      event.preventDefault()
      const value = props.modelValue
      const cursorPos = textareaRef.value.selectionStart
      const newValue = value.substring(0, cursorPos) + '\n' + value.substring(cursorPos)
      emit('update:modelValue', newValue)
      nextTick(() => {
        textareaRef.value.selectionStart = textareaRef.value.selectionEnd = cursorPos + 1
        autoResizeTextarea()
      })
    }
  } else {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      emit('submit')
    }
  }
}

const scrollToSelected = () => {
  nextTick(() => {
    const dropdown = dropdownRef.value
    if (!dropdown) return
    
    const selectedItem = dropdown.querySelector('.dropdown-item.active')
    if (selectedItem) {
      selectedItem.scrollIntoView({ block: 'nearest' })
    }
  })
}

const selectAgent = (agent) => {
  if (!agent || mentionStartIndex.value === -1) return
  
  const value = props.modelValue
  const cursorPos = textareaRef.value.selectionStart
  
  const beforeMention = value.substring(0, mentionStartIndex.value)
  const afterCursor = value.substring(cursorPos)
  
  const newValue = beforeMention + '@' + agent.name + ' ' + afterCursor
  emit('update:modelValue', newValue)
  
  showDropdown.value = false
  mentionStartIndex.value = -1
  searchText.value = ''
  
  nextTick(() => {
    const newCursorPos = beforeMention.length + agent.name.length + 2
    textareaRef.value.focus()
    textareaRef.value.selectionStart = textareaRef.value.selectionEnd = newCursorPos
    autoResizeTextarea()
  })
}

const handleBlur = () => {
  setTimeout(() => {
    showDropdown.value = false
  }, 200)
}

const handleFocus = () => {
  const value = props.modelValue
  const cursorPos = textareaRef.value?.selectionStart || 0
  checkForMention(value, cursorPos)
}

const focus = () => {
  textareaRef.value?.focus()
}

const getCursorPos = () => {
  return textareaRef.value?.selectionStart || 0
}

defineExpose({
  focus,
  getCursorPos
})

onMounted(() => {
  window.addEventListener('resize', updateDropdownPosition)
  window.addEventListener('scroll', updateDropdownPosition, true)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateDropdownPosition)
  window.removeEventListener('scroll', updateDropdownPosition, true)
})
</script>

<style scoped>
.agent-mention-wrapper {
  position: relative;
  width: 100%;
  flex: 1;
}

.input-container {
  position: relative;
  width: 100%;
}

.mention-textarea {
  width: 100%;
  border: none;
  background: transparent;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  min-height: 24px;
  max-height: 120px;
  overflow-y: auto;
  outline: none;
  font-family: inherit;
}

.mention-textarea::placeholder {
  color: #999;
}

.textarea-mirror {
  position: absolute;
  visibility: hidden;
  pointer-events: none;
  top: 0;
  left: 0;
  overflow: hidden;
}

.agent-dropdown {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.dropdown-list {
  max-height: 200px;
  overflow-y: auto;
  max-width: 150px;
}

.dropdown-item {
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.15s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-item:hover,
.dropdown-item.active {
  background: #f0f7ff;
}

.agent-name {
  font-size: 14px;
  color: #333;
}

.agent-type-badge {
  font-size: 10px;
  color: #1890ff;
  background: #e6f7ff;
  padding: 1px 4px;
  border-radius: 3px;
  margin-left: 6px;
}
</style>
