<template>
  <div v-if="error" class="error-boundary">
    <div class="error-content">
      <div class="error-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <h2 class="error-title">页面出现了一些问题</h2>
      <p class="error-message">{{ error.message }}</p>
      <div class="error-actions">
        <button class="btn-retry" @click="retry">重新加载</button>
        <button class="btn-home" @click="goHome">返回首页</button>
      </div>
    </div>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const error = ref(null)

onErrorCaptured((err, instance, info) => {
  console.error('Error captured:', err, info)
  error.value = err
  return false
})

const retry = () => {
  error.value = null
}

const goHome = () => {
  error.value = null
  router.push('/')
}
</script>

<style scoped>
.error-boundary {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  z-index: 9999;
}

.error-content {
  text-align: center;
  padding: 48px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
  max-width: 480px;
  width: 90%;
}

.error-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-icon svg {
  width: 40px;
  height: 40px;
  color: #fff;
}

.error-title {
  font-size: 24px;
  color: #1a1a2e;
  margin-bottom: 12px;
}

.error-message {
  font-size: 14px;
  color: #666;
  margin-bottom: 32px;
  word-break: break-word;
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.error-actions button {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-retry {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-retry:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-home {
  background: #f0f0f0;
  color: #333;
}

.btn-home:hover {
  background: #e0e0e0;
}
</style>
