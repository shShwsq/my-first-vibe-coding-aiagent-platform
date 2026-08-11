<template>
  <div class="test-progress-sidebar" :class="{ open: isOpen }">
    <div class="sidebar-header">
      <h3>进度</h3>
      <button class="close-btn" @click="$emit('close')" title="关闭">
        <svg viewBox="0 0 24 24">
          <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
        </svg>
      </button>
    </div>
    
    <div class="progress-list">
      <div v-if="Object.keys(testProgress).length === 0" class="empty-state">
        <p>暂无任务</p>
      </div>
      
      <div 
        v-for="(progress, agentId) in testProgress" 
        :key="agentId" 
        class="progress-item"
        :class="progress.status"
      >
        <div class="agent-name">
          <span class="status-icon">
            <svg v-if="progress.status === 'completed'" viewBox="0 0 24 24">
              <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
            <svg v-else-if="progress.status === 'error'" viewBox="0 0 24 24">
              <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
            <div v-else-if="progress.status === 'testing'" class="spinner-small"></div>
            <svg v-else viewBox="0 0 24 24">
              <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/>
            </svg>
          </span>
          {{ progress.agent_name }}
        </div>
        
        <div class="progress-bar-container">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: getProgressWidth(progress) + '%' }"
              :class="progress.status"
            ></div>
          </div>
          <span class="progress-text" v-if="progress.total > 0">{{ progress.current }}/{{ progress.total }}</span>
        </div>
        
        <div class="progress-message">{{ progress.message }}</div>
        
        <div v-if="progress.status === 'completed'" class="result-summary">
          <span class="success" v-if="progress.success_count > 0">成功: {{ progress.success_count }}</span>
          <span class="error" v-else-if="progress.error_count > 0">失败: {{ progress.error_count }}</span>
        </div>
      </div>
    </div>
    
    <div v-if="allCompleted" class="completion-message">
      <p>所有任务已完成</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  testProgress: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['close'])

const allCompleted = computed(() => {
  const progressValues = Object.values(props.testProgress)
  if (progressValues.length === 0) return false
  return progressValues.every(p => p.status === 'completed' || p.status === 'error')
})

const getProgressWidth = (progress) => {
  if (progress.total === 0) return 0
  return Math.round((progress.current / progress.total) * 100)
}
</script>

<style scoped>
.test-progress-sidebar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 320px;
  background: #fff;
  border-right: 1px solid #eee;
  transform: translateX(-100%);
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;
  z-index: 50;
}

.test-progress-sidebar.open {
  transform: translateX(0);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.sidebar-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: #f5f5f5;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e0e0e0;
  color: #333;
}

.close-btn svg {
  width: 18px;
  height: 18px;
}

.progress-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #999;
}

.progress-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border-left: 3px solid #667eea;
}

.progress-item.completed {
  border-left-color: #4caf50;
}

.progress-item.error {
  border-left-color: #f44336;
}

.progress-item.testing {
  border-left-color: #ff9800;
}

.agent-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.status-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon svg {
  width: 18px;
  height: 18px;
}

.status-icon .completed {
  color: #4caf50;
}

.status-icon .error {
  color: #f44336;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid #ff9800;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-fill.completed {
  background: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%);
}

.progress-fill.error {
  background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
}

.progress-text {
  font-size: 12px;
  color: #666;
  min-width: 40px;
  text-align: right;
}

.progress-message {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.result-summary {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  font-size: 12px;
}

.result-summary .success {
  color: #4caf50;
}

.result-summary .error {
  color: #f44336;
}

.completion-message {
  padding: 16px;
  text-align: center;
  background: #e8f5e9;
  color: #4caf50;
  font-weight: 500;
}
</style>
