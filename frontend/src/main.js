import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import axios from 'axios'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'
import ApiConfig from './views/ApiConfig.vue'
import Chat from './views/Chat.vue'
import Agents from './views/Agents.vue'
import KnowledgeBase from './views/KnowledgeBase.vue'
import TestCases from './views/TestCases.vue'
import TestResults from './views/TestResults.vue'
import WorkflowEditor from './views/WorkflowEditor.vue'
import CodeTools from './views/CodeTools.vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''
axios.defaults.baseURL = apiBaseUrl

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/workflow-editor/:id',
    name: 'WorkflowEditor',
    component: WorkflowEditor
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    redirect: '/dashboard',
    children: [
      {
        path: '',
        name: 'Chat',
        component: Chat
      },
      {
        path: 'home',
        redirect: '/dashboard'
      },
      {
        path: 'api-config',
        name: 'ApiConfig',
        component: ApiConfig
      },
      {
        path: 'agents',
        name: 'Agents',
        component: Agents
      },
      {
        path: 'knowledge-base',
        name: 'KnowledgeBase',
        component: KnowledgeBase
      },
      {
        path: 'test-cases',
        name: 'TestCases',
        component: TestCases
      },
      {
        path: 'test-results',
        name: 'TestResults',
        component: TestResults
      },
      {
        path: 'code-tools',
        name: 'CodeTools',
        component: CodeTools
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('userId')
      localStorage.removeItem('is_superuser')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path.startsWith('/dashboard') && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

const app = createApp(App)
app.use(router)
app.mount('#app')
