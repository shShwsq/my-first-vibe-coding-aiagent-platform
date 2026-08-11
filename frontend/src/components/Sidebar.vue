<template>
  <div class="sidebar" :class="{ collapsed: !isOpen }">
    <div class="sidebar-header">
      <div class="logo" @click="$emit('toggle')">
        <svg viewBox="0 0 24 24" class="logo-icon">
          <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
        </svg>
        <span class="logo-text">shwsq's aiagent</span>
      </div>
    </div>
    
    <nav class="sidebar-nav">
      <router-link to="/dashboard" class="nav-item" @click="$emit('navigate')">
        <svg viewBox="0 0 24 24" class="nav-icon">
          <path fill="currentColor" d="M12 3C17.5 3 22 6.58 22 11C22 15.42 17.5 19 12 19C10.76 19 9.57 18.82 8.47 18.5C5.55 21 2 21 2 21C4.33 18.67 4.7 17.1 4.75 16.5C3.05 15.07 2 13.13 2 11C2 6.58 6.5 3 12 3Z"/>
        </svg>
        <span class="nav-text">对话</span>
      </router-link>
      
      <router-link to="/dashboard/api-config" class="nav-item" @click="$emit('navigate')">
        <svg viewBox="0 0 24 24" class="nav-icon">
          <path fill="currentColor" d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z"/>
        </svg>
        <span class="nav-text">模型 API</span>
      </router-link>
      
      <router-link to="/dashboard/agents" class="nav-item" @click="$emit('navigate')">
        <svg viewBox="0 0 24 24" class="nav-icon">
          <path fill="currentColor" d="M12,2A2,2 0 0,1 14,4A2,2 0 0,1 12,6A2,2 0 0,1 10,4A2,2 0 0,1 12,2M21,9H15V22H13V16H11V22H9V9H3V7H21V9Z"/>
        </svg>
        <span class="nav-text">智能体管理</span>
      </router-link>
      
      <router-link to="/dashboard/knowledge-base" class="nav-item" @click="$emit('navigate')">
        <svg viewBox="0 0 24 24" class="nav-icon">
          <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M10,19L12,15H9V10H15V15L13,19H10Z"/>
        </svg>
        <span class="nav-text">知识库</span>
      </router-link>
      
      <router-link to="/dashboard/code-tools" class="nav-item" @click="$emit('navigate')">
        <svg viewBox="0 0 24 24" class="nav-icon">
          <path fill="currentColor" d="M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z"/>
        </svg>
        <span class="nav-text">代码工具</span>
      </router-link>

      <router-link to="/dashboard/test-cases" class="nav-item" @click="handleTestCasesClick">
        <svg viewBox="0 0 24 24" class="nav-icon">
          <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M12,9L8,13H10.5V17H13.5V13H16L12,9Z"/>
        </svg>
        <span class="nav-text">测试用例</span>
      </router-link>
      
      <router-link to="/dashboard/test-results" class="nav-item" @click="$emit('navigate')">
        <svg viewBox="0 0 24 24" class="nav-icon">
          <path fill="currentColor" d="M9,5A3.5,3.5 0 0,1 12.5,8.5A3.5,3.5 0 0,1 9,12A3.5,3.5 0 0,1 5.5,8.5A3.5,3.5 0 0,1 9,5M9,14C12.46,14 19,15.81 19,19.5V22H-1V19.5C-1,15.81 5.54,14 9,14M19,5A1,1 0 0,0 18,6A1,1 0 0,0 19,7A1,1 0 0,0 20,6A1,1 0 0,0 19,5M19,8A1,1 0 0,0 18,9A1,1 0 0,0 19,10A1,1 0 0,0 20,9A1,1 0 0,0 19,8M16,5A1,1 0 0,0 15,6A1,1 0 0,0 16,7A1,1 0 0,0 17,6A1,1 0 0,0 16,5M16,8A1,1 0 0,0 15,9A1,1 0 0,0 16,10A1,1 0 0,0 17,9A1,1 0 0,0 16,8M22,5A1,1 0 0,0 21,6A1,1 0 0,0 22,7A1,1 0 0,0 23,6A1,1 0 0,0 22,5M22,8A1,1 0 0,0 21,9A1,1 0 0,0 22,10A1,1 0 0,0 23,9A1,1 0 0,0 22,8M13,5A1,1 0 0,0 12,6A1,1 0 0,0 13,7A1,1 0 0,0 14,6A1,1 0 0,0 13,5M13,8A1,1 0 0,0 12,9A1,1 0 0,0 13,10A1,1 0 0,0 14,9A1,1 0 0,0 13,8M9,11A2.5,2.5 0 0,0 11.5,8.5A2.5,2.5 0 0,0 9,6A2.5,2.5 0 0,0 6.5,8.5A2.5,2.5 0 0,0 9,11Z"/>
        </svg>
        <span class="nav-text">测试结果</span>
      </router-link>
    </nav>
    
    <div class="sidebar-footer">
      <div class="user-info">
        <div class="user-avatar">{{ username?.charAt(0).toUpperCase() }}</div>
        <span class="username">{{ username }}</span>
      </div>
      <button class="logout-btn" @click="handleLogout">
        <svg viewBox="0 0 24 24" class="logout-icon">
          <path fill="currentColor" d="M17,17.25V14H10V10H17V6.75L22.25,12L17,17.25M13,2A2,2 0 0,1 15,4V8H13V4H4V20H13V16H15V20A2,2 0 0,1 13,22H4A2,2 0 0,1 2,20V4A2,2 0 0,1 4,2H13Z"/>
        </svg>
        <span class="logout-text">退出登录</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

defineProps({
  isOpen: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['toggle', 'navigate'])
const router = useRouter()
const route = useRoute()

const username = computed(() => localStorage.getItem('username') || 'User')

const handleTestCasesClick = () => {
  if (route.path === '/dashboard/test-cases') {
    emit('navigate')
  }
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 1000;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 70px;
  background: transparent;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.sidebar.collapsed .sidebar-header {
  border-bottom-color: transparent;
  padding: 8px 19px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.logo:hover {
  background: rgba(255, 255, 255, 0.1);
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: #667eea;
  flex-shrink: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.2s ease;
}

.sidebar.collapsed .logo-text {
  opacity: 0;
  pointer-events: none;
}

.sidebar-nav {
  flex: 1;
  padding: 10px 12px;
  overflow-y: auto;
  overflow-x: hidden;
  opacity: 1;
  transition: opacity 0.2s ease;
}

.sidebar-nav::-webkit-scrollbar {
  width: 6px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.35);
}

.sidebar.collapsed .sidebar-nav {
  opacity: 0;
  pointer-events: none;
  overflow: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: rgba(102, 126, 234, 0.2);
  color: #fff;
}

.nav-item.router-link-exact-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.nav-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.nav-text {
  white-space: nowrap;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  opacity: 1;
  transition: all 0.2s ease;
}

.sidebar.collapsed .sidebar-footer {
  opacity: 0;
  pointer-events: none;
  border-top-color: transparent;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.username {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #fff;
}

.logout-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.logout-text {
  white-space: nowrap;
}
</style>
