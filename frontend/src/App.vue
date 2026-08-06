<script setup>
import { ref, reactive, onMounted } from 'vue'
import Chat from './Chat.vue'

const apiBase = import.meta.env.DEV ? 'http://127.0.0.1:3000/api' : '/api'

const mode = ref('login')
const captcha = reactive({ id: '', svg: '', loading: false })
const error = ref('')
const success = ref('')
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
const token = ref(localStorage.getItem('token') || '')

const loginForm = reactive({ username: '', password: '', captcha: '' })
const regForm = reactive({ username: '', email: '', password: '', confirm: '', captcha: '' })

async function loadCaptcha() {
  captcha.loading = true
  try {
    const res = await fetch(`${apiBase}/captcha`)
    const data = await res.json()
    captcha.id = data.id
    captcha.svg = data.svg
  } catch {
    error.value = '获取验证码失败，请检查后端服务'
  } finally {
    captcha.loading = false
  }
}

async function request(path, body) {
  const res = await fetch(`${apiBase}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.message || '请求失败')
  return data
}

function handleAuth(data) {
  localStorage.setItem('token', data.token)
  localStorage.setItem('user', JSON.stringify(data.user))
  user.value = data.user
}

function switchMode(m) {
  mode.value = m
  error.value = ''
  success.value = ''
  loadCaptcha()
}

async function submit() {
  error.value = ''
  success.value = ''
  try {
    if (mode.value === 'login') {
      const data = await request('/auth/login', {
        username: loginForm.username,
        password: loginForm.password,
        captchaId: captcha.id,
        captcha: loginForm.captcha,
      })
      handleAuth(data)
      success.value = data.message
    } else {
      if (regForm.password !== regForm.confirm) {
        error.value = '两次输入的密码不一致'
        loadCaptcha()
        return
      }
      const data = await request('/auth/register', {
        username: regForm.username,
        email: regForm.email,
        password: regForm.password,
        captchaId: captcha.id,
        captcha: regForm.captcha,
      })
      handleAuth(data)
      success.value = data.message
    }
  } catch (e) {
    error.value = e.message
    loadCaptcha()
  }
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  token.value = ''
  user.value = null
}

onMounted(loadCaptcha)
</script>

<template>
  <div v-if="user && token" class="chat-full">
    <Chat :user="user" :token="token" @logout="logout" />
  </div>

  <div v-else class="page">
    <div class="card">
      <h1 class="title">用户中心</h1>

      <div class="tabs">
        <button :class="['tab', { active: mode === 'login' }]" @click="switchMode('login')">登录</button>
        <button :class="['tab', { active: mode === 'register' }]" @click="switchMode('register')">注册</button>
      </div>

      <form v-if="mode === 'login'" class="form" @submit.prevent="submit">
          <input v-model="loginForm.username" placeholder="用户名 / 邮箱" required />
          <input v-model="loginForm.password" type="password" placeholder="密码" required />
          <div class="captcha-row">
            <input v-model="loginForm.captcha" placeholder="验证码" maxlength="4" required />
            <div class="captcha-img" @click="loadCaptcha" v-html="captcha.svg" :title="'点击刷新'"></div>
          </div>
          <p v-if="error" class="err">{{ error }}</p>
          <button class="btn primary" type="submit" :disabled="captcha.loading">登 录</button>
        </form>

        <form v-else class="form" @submit.prevent="submit">
          <input v-model="regForm.username" placeholder="用户名（3-20位字母/数字/下划线）" required />
          <input v-model="regForm.email" type="email" placeholder="邮箱" required />
          <input v-model="regForm.password" type="password" placeholder="密码（至少6位）" required />
          <input v-model="regForm.confirm" type="password" placeholder="确认密码" required />
          <div class="captcha-row">
            <input v-model="regForm.captcha" placeholder="验证码" maxlength="4" required />
            <div class="captcha-img" @click="loadCaptcha" v-html="captcha.svg" :title="'点击刷新'"></div>
          </div>
          <p v-if="error" class="err">{{ error }}</p>
          <button class="btn primary" type="submit" :disabled="captcha.loading">注 册</button>
        </form>
    </div>
  </div>
</template>

<style scoped>
.chat-full {
  min-height: 100vh;
}
.page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.card {
  width: 380px;
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}
.title {
  text-align: center;
  margin: 0 0 24px;
  color: #333;
}
.tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 2px solid #eee;
}
.tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: none;
  font-size: 15px;
  color: #888;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}
.tab.active {
  color: #667eea;
  border-bottom-color: #667eea;
  font-weight: 600;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
input {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}
input:focus {
  outline: none;
  border-color: #667eea;
}
.captcha-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.captcha-row input {
  flex: 1;
}
.captcha-img {
  cursor: pointer;
  border: 1px solid #ddd;
  border-radius: 6px;
  overflow: hidden;
  line-height: 0;
  height: 40px;
}
.captcha-img :deep(svg) {
  height: 40px;
  width: auto;
  display: block;
}
.err {
  color: #e74c3c;
  font-size: 13px;
  margin: 0;
}
.ok {
  color: #27ae60;
  font-size: 13px;
  margin: 0;
}
.btn {
  padding: 11px;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn.primary {
  background: #667eea;
  color: #fff;
}
.btn.primary:hover {
  opacity: 0.9;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.dashboard {
  text-align: center;
  color: #333;
}
.dashboard .btn {
  margin-top: 16px;
  width: 100%;
}
</style>
