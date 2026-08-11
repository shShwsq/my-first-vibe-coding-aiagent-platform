<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>shwsq's aiagent</h1>
        <p>AI Agent Platform</p>
      </div>
      
      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input 
            type="text" 
            id="username" 
            v-model="form.username" 
            placeholder="请输入用户名"
            required
          />
        </div>
        
        <div v-if="!isLogin" class="form-group">
          <label for="email">邮箱（可选）</label>
          <input 
            type="email" 
            id="email" 
            v-model="form.email" 
            placeholder="请输入邮箱"
          />
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <input 
            type="password" 
            id="password" 
            v-model="form.password" 
            placeholder="请输入密码"
            required
          />
        </div>
        
        <div v-if="!isLogin" class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input 
            type="password" 
            id="confirmPassword" 
            v-model="form.confirmPassword" 
            placeholder="请再次输入密码"
            required
          />
        </div>
        
        <div v-if="isLogin" class="form-options">
          <label class="remember-me">
            <input type="checkbox" v-model="form.remember" />
            <span>记住我</span>
          </label>
          <a href="#" class="forgot-password" @click.prevent="handleForgotPassword">忘记密码？</a>
        </div>
        
        <button type="submit" class="login-btn" :disabled="loading" @click="handleButtonClick">
          {{ loading ? (isLogin ? '登录中...' : '注册中...') : (isLogin ? '登录' : '注册') }}
        </button>
        
        <div class="register-link">
          {{ isLogin ? '还没有账号？' : '已有账号？' }}
          <a href="#" @click.prevent="toggleMode">{{ isLogin ? '立即注册' : '立即登录' }}</a>
        </div>
      </form>
      
      <div v-if="errorMessage" :class="['message', messageType]">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const isLogin = ref(true)
const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  remember: false
})

const loading = ref(false)
const errorMessage = ref('')
const messageType = ref('error')

const toggleMode = () => {
  isLogin.value = !isLogin.value
  console.log('toggleMode called, isLogin is now:', isLogin.value)
  errorMessage.value = ''
  form.value = {
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    remember: false
  }
}

const handleForgotPassword = () => {
  alert('忘记密码功能开发中...')
}

const handleButtonClick = () => {
  console.log('Button clicked! loading:', loading.value, 'isLogin:', isLogin.value)
}

const handleSubmit = async () => {
  console.log('handleSubmit called, isLogin:', isLogin.value)
  console.log('form data:', form.value)
  
  loading.value = true
  errorMessage.value = ''
  
  if (!isLogin.value) {
    console.log('Register mode - validating...')
    if (form.value.password !== form.value.confirmPassword) {
      errorMessage.value = '两次输入的密码不一致'
      messageType.value = 'error'
      loading.value = false
      return
    }
    
    if (form.value.password.length < 6) {
      errorMessage.value = '密码长度至少6位'
      messageType.value = 'error'
      loading.value = false
      return
    }
    console.log('Validation passed, sending request...')
  }
  
  try {
    if (isLogin.value) {
      const response = await axios.post('/api/auth/login', {
        username: form.value.username,
        password: form.value.password
      })
      
      if (response.data.success) {
        localStorage.setItem('token', response.data.token)
        localStorage.setItem('username', form.value.username)
        if (response.data.user) {
          localStorage.setItem('userId', response.data.user.id)
          localStorage.setItem('is_superuser', response.data.user.is_superuser ? 'true' : 'false')
        }
        router.push('/dashboard')
      } else {
        errorMessage.value = response.data.message || '登录失败，请检查用户名和密码'
        messageType.value = 'error'
      }
    } else {
      const response = await axios.post('/api/auth/register', {
        username: form.value.username,
        email: form.value.email || null,
        password: form.value.password
      })
      
      errorMessage.value = '注册成功！请登录'
      messageType.value = 'success'
      isLogin.value = true
      form.value.username = form.value.username
      form.value.password = ''
      form.value.confirmPassword = ''
    }
  } catch (error) {
    console.error('Error:', error)
    const errorDetail = error.response?.data?.detail || error.response?.data?.message || '操作失败，请稍后重试'
    errorMessage.value = errorDetail
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #4b54a2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  color: #333;
  font-size: 28px;
  margin-bottom: 8px;
}

.login-header p {
  color: #666;
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

.form-group input {
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #666;
}

.remember-me input {
  cursor: pointer;
}

.forgot-password {
  color: #667eea;
  text-decoration: none;
}

.forgot-password:hover {
  text-decoration: underline;
}

.login-btn {
  background: linear-gradient(135deg, #667eea 0%, #4b54a2 100%);
  color: white;
  border: none;
  padding: 14px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.register-link {
  text-align: center;
  color: #666;
  font-size: 14px;
}

.register-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.register-link a:hover {
  text-decoration: underline;
}

.message {
  padding: 12px;
  border-radius: 8px;
  text-align: center;
  font-size: 14px;
  margin-top: 16px;
}

.message.error {
  background: #fee;
  color: #c00;
}

.message.success {
  background: #efe;
  color: #060;
}
</style>
