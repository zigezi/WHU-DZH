<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import BuildPanel from './BuildPanel.vue'

const props = defineProps({
  user: { type: Object, required: true },
  token: { type: String, required: true },
})
const emit = defineEmits(['logout'])

const apiBase = import.meta.env.DEV ? 'http://127.0.0.1:3000/api' : '/api'

const sessions = ref([])
const current = ref(null)
const loading = ref(false)
const sending = ref(false)
const archiving = ref(false)
const downloading = ref(false)
const earsConverting = ref(false)
const archivedFile = ref('')
const input = ref('')
const listRef = ref(null)
const buildPanelOpen = ref(false)
const buildInfo = ref(null)
const building = ref(false)
const buildError = ref('')
const deployState = ref(null)
const deploying = ref(false)

function api(path, options = {}) {
  return fetch(`${apiBase}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${props.token}`,
      ...(options.headers || {}),
    },
  })
}

function scrollDown() {
  nextTick(() => listRef.value && (listRef.value.scrollTop = listRef.value.scrollHeight))
}

function renderMd(text) {
  return marked.parse(text || '')
}

async function loadSessions() {
  const res = await api('/sessions')
  if (res.status === 401) return emit('logout')
  const data = await res.json()
  sessions.value = data.sessions
}

async function openSession(id) {
  const res = await api(`/sessions/${id}/messages`)
  if (res.status === 401) return emit('logout')
  const data = await res.json()
  current.value = sessions.value.find((s) => s.id === id) || current.value
  current.value.messages = data.messages
  current.value.archivedFile = ''
  buildInfo.value = null
  buildError.value = ''
  deployState.value = null
  const bres = await api(`/sessions/${id}/build`)
  if (bres.ok) buildInfo.value = (await bres.json())
  await loadDeployState()
  scrollDown()
}

async function selectSession(id) {
  if (current.value && current.value.id === id) return
  await openSession(id)
}

async function newSession() {
  loading.value = true
  try {
    const res = await api('/sessions', { method: 'POST', body: JSON.stringify({}) })
    if (res.status === 401) return emit('logout')
    const data = await res.json()
    await loadSessions()
    current.value = data.session
    current.value.messages = data.opening ? [data.opening] : []
    current.value.archivedFile = ''
    input.value = ''
    scrollDown()
  } finally {
    loading.value = false
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value || !current.value) return
  sending.value = true
  try {
    current.value.messages.push({ id: 'tmp', role: 'user', content: text })
    input.value = ''
    scrollDown()
    const res = await api(`/sessions/${current.value.id}/messages`, { method: 'POST', body: JSON.stringify({ content: text }) })
    if (res.status === 401) return emit('logout')
    const data = await res.json()
    current.value.messages = current.value.messages.filter((m) => m.id !== 'tmp')
    current.value.messages.push(data.user, data.assistant)
    scrollDown()
  } catch (e) {
    current.value.messages.push({ id: 'err', role: 'assistant', content: '⚠️ 发送失败，请稍后重试' })
    scrollDown()
  } finally {
    sending.value = false
  }
}

async function archive() {
  if (!current.value || archiving.value) return
  archiving.value = true
  try {
    const res = await api(`/sessions/${current.value.id}/archive`, { method: 'POST' })
    if (res.status === 401) return emit('logout')
    const data = await res.json()
    if (res.ok) {
      archivedFile.value = data.file
      current.value.status = 'archived'
      await loadSessions()
      sessions.value = sessions.value.map((s) => (s.id === current.value.id ? { ...s, status: 'archived' } : s))
      current.value.messages.push({ id: 'done', role: 'assistant', content: `✅ 需求分析文档已生成：\`${data.file}\`` })
      scrollDown()
    } else {
      alert(data.message || '归档失败')
    }
  } finally {
    archiving.value = false
  }
}

async function earsConvert() {
  if (!current.value || earsConverting.value) return
  earsConverting.value = true
  try {
    const res = await api(`/sessions/${current.value.id}/ears`, { method: 'POST' })
    if (res.status === 401) return emit('logout')
    const data = await res.json()
    if (!res.ok) {
      alert(data.message || 'EARS 转换失败')
      return
    }
    alert(`✅ 低歧义 EARS 需求已生成：\n${data.file}\n\n正在下载整个会话文件夹…`)
    const bres = await api(`/sessions/${current.value.id}/build`)
    if (bres.ok) buildInfo.value = (await bres.json())
    current.value.messages.push({
      id: `ears-${Date.now()}`,
      role: 'assistant',
      content: `✅ 低歧义 EARS 规格已生成：\`${data.file}\``,
    })
    scrollDown()
    await download()
  } catch {
    alert('EARS 转换失败，请稍后重试')
  } finally {
    earsConverting.value = false
  }
}

async function download() {
  if (!current.value || downloading.value) return
  downloading.value = true
  try {
    const res = await api(`/sessions/${current.value.id}/download`)
    if (res.status === 401) return emit('logout')
    if (!res.ok) {
      alert((await res.json()).message || '下载失败')
      return
    }
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${current.value.folder}.zip`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(a.href)
  } catch {
    alert('下载失败，请稍后重试')
  } finally {
    downloading.value = false
  }
}

async function triggerBuild() {
  if (!current.value || building.value) return
  building.value = true
  buildError.value = ''
  try {
    const res = await api(`/sessions/${current.value.id}/build`, { method: 'POST' })
    if (res.status === 401) return emit('logout')
    const data = await res.json()
    if (!res.ok) {
      buildError.value = data.message || '触发构建失败'
      alert(buildError.value)
      return
    }
    buildInfo.value = { ...(buildInfo.value || {}), build: { id: data.buildId, status: 'queued', iterations: 0 } }
    buildPanelOpen.value = true
  } catch {
    buildError.value = '触发构建失败，请稍后重试'
    alert(buildError.value)
  } finally {
    building.value = false
  }
}

async function loadDeployState() {
  if (!current.value) return
  const res = await api(`/sessions/${current.value.id}/container`)
  if (res.status === 401) return emit('logout')
  if (res.ok) deployState.value = (await res.json()).deploy
}

// 拉起测试容器：若已有运行中容器，后端返回 409，弹窗确认「是否注销旧测试容器并拉起新测试容器」后再替换。
async function deployContainer() {
  if (!current.value || deploying.value) return
  deploying.value = true
  try {
    let replace = false
    for (;;) {
      const res = await api(`/sessions/${current.value.id}/container`, {
        method: 'POST',
        body: JSON.stringify({ replace }),
      })
      if (res.status === 401) return emit('logout')
      const data = await res.json()
      if (res.status === 409 && data.needConfirm && !replace) {
        const ok = window.confirm(
          `是否注销旧测试容器并拉起新测试容器？\n（当前旧容器：端口 ${data.existing?.hostPort ?? '-'}）`,
        )
        if (!ok) return
        replace = true
        continue
      }
      if (!res.ok) {
        alert(data.message || '拉起测试容器失败')
        return
      }
      deployState.value = { ...data, status: 'running' }
      alert(`✅ 测试容器已拉起：${data.url}`)
      await loadDeployState()
      return
    }
  } catch {
    alert('拉起测试容器失败，请稍后重试')
  } finally {
    deploying.value = false
  }
}

onMounted(async () => {
  await loadSessions()
  if (sessions.value.length === 0) {
    await newSession()
  } else {
    await openSession(sessions.value[0].id)
  }
})
</script>

<template>
  <div class="chat-page">
    <aside class="sidebar">
      <button class="btn-new" :disabled="loading" @click="newSession">＋ 新建对话</button>
      <button class="btn-deploy" :disabled="deploying" @click="deployContainer">
        {{ deploying ? '拉起中…' : '🚀 拉起测试容器' }}
      </button>
      <div v-if="deployState" class="deploy-box">
        <div class="deploy-row">
          <span class="dot" :class="deployState.status"></span>
          <span>{{ deployState.status === 'running' ? '测试容器运行中' : deployState.status }}</span>
        </div>
        <a v-if="deployState.url" class="deploy-link" :href="deployState.url" target="_blank" rel="noopener">
          端口 {{ deployState.host_port }} → 打开 ↗
        </a>
      </div>
      <h3 class="user">{{ user.username }}</h3>
      <ul class="sess-list">
        <li
          v-for="s in sessions"
          :key="s.id"
          :class="['sess-item', { active: current && current.id === s.id }]"
          @click="selectSession(s.id)"
        >
          <div class="sess-name">{{ s.name || s.folder }}</div>
          <div class="sess-meta">
            <span class="tag" :class="s.status">{{ s.status === 'archived' ? '已归档' : '对话中' }}</span>
            <span class="time">{{ new Date(s.created_at).toLocaleString() }}</span>
          </div>
        </li>
      </ul>
      <button class="btn-logout" @click="emit('logout')">退出登录</button>
    </aside>

    <main class="chat-main">
      <template v-if="current">
        <header class="chat-header">
          <div>
            <div class="who">{{ current.name || current.folder }}</div>
            <div class="hint">
              {{
                current.status === 'archived'
                  ? '会话已归档'
                  : 'OpenSpec 正在逐轮反问你，帮你澄清需求…'
              }}
            </div>
          </div>
          <div class="actions">
          <button
            v-if="current.status === 'active'"
            class="btn-archive"
            :disabled="archiving || sending"
            @click="archive"
          >
            {{ archiving ? '生成中…' : '完成 / 归档' }}
          </button>
          <button
            class="btn-download"
            :disabled="downloading"
            @click="download"
          >
            {{ downloading ? '打包中…' : '⬇ 下载产物' }}
          </button>
          <button
            class="btn-ears"
            :disabled="earsConverting || downloading"
            @click="earsConvert"
          >
            {{ earsConverting ? 'EARS转换中…' : '⬇ 下载低歧义EARS需求' }}
          </button>
          <button
            v-if="buildInfo && buildInfo.ears && !(buildInfo.build && ['passed','failed'].includes(buildInfo.build.status))"
            class="btn-build"
            :disabled="building"
            @click="triggerBuild"
          >
            {{ building ? '构建中…' : '⚙ 生成应用' }}
          </button>
          </div>
        </header>

        <div ref="listRef" class="chat-list">
          <p v-if="!current.messages || current.messages.length === 0" class="empty">
            点击下方输入框，回答 AI 的问题开始吧
          </p>
          <div v-for="m in current.messages" :key="m.id" class="msg-row" :class="m.role">
            <div v-if="m.role !== 'user'" class="avatar">OS</div>
            <div class="bubble" v-html="renderMd(m.content)"></div>
          </div>
        </div>

        <div class="build-area" v-if="buildInfo && buildInfo.ears">
          <button class="build-toggle" @click="buildPanelOpen = !buildPanelOpen">
            {{ buildPanelOpen ? '▾ 收起构建面板' : '▸ 展开构建面板（生成应用 / 修改 / 预览 / 版本）' }}
          </button>
          <BuildPanel v-if="buildPanelOpen" :session-id="current.id" :token="props.token" />
        </div>

        <footer class="chat-input" v-if="current.status !== 'archived'">
          <textarea
            v-model="input"
            placeholder="回答 AI 的追问，或告诉我你的想法（Ctrl+Enter 发送）…"
            rows="2"
            @keydown.ctrl.enter.prevent="send"
          ></textarea>
          <button class="send" :disabled="sending || !input.trim()" @click="send">
            {{ sending ? '思考中…' : '发送' }}
          </button>
        </footer>
      </template>

      <div v-else class="empty-wrap">
        <button class="btn-new big" :disabled="loading" @click="newSession">＋ 开始第一段对话</button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #4b4e6d 0%, #764ba2 100%);
  font-size: 14px;
}
.sidebar {
  width: 280px;
  background: rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 10px;
}
.btn-new {
  padding: 10px;
  border: none;
  border-radius: 8px;
  background: #fff;
  color: #667eea;
  font-weight: 600;
  cursor: pointer;
}
.btn-new:disabled {
  opacity: 0.6;
}
.btn-deploy {
  padding: 10px;
  border: none;
  border-radius: 8px;
  background: #e67e22;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.btn-deploy:hover {
  opacity: 0.9;
}
.btn-deploy:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.deploy-box {
  background: rgba(255, 255, 255, 0.14);
  border-radius: 8px;
  padding: 10px 12px;
  color: #fff;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}
.deploy-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.deploy-box .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #bbb;
}
.deploy-box .dot.running {
  background: #2ecc71;
}
.deploy-box .dot.failed,
.deploy-box .dot.error {
  background: #e74c3c;
}
.deploy-link {
  color: #fff;
  text-decoration: underline;
  word-break: break-all;
}
.user {
  color: #fff;
  opacity: 0.9;
  margin: 4px 0;
  font-size: 14px;
}
.sess-list {
  flex: 1;
  list-style: none;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sess-item {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  color: #fff;
}
.sess-item:hover {
  background: rgba(255, 255, 255, 0.2);
}
.sess-item.active {
  background: #fff;
  color: #333;
}
.sess-name {
  font-weight: 600;
  word-break: break-all;
  margin-bottom: 4px;
}
.sess-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  opacity: 0.8;
}
.tag {
  background: #27ae60;
  border-radius: 4px;
  padding: 1px 6px;
}
.tag.archived {
  background: #95a5a6;
}
.btn-logout {
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 8px;
  background: transparent;
  color: #fff;
  cursor: pointer;
}

.chat-box {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  margin: 0;
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  min-height: 0;
}
.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.build-area {
  border-top: 1px solid #eee;
  display: flex;
  flex-direction: column;
}
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}
.build-toggle {
  padding: 8px 16px;
  border: none;
  background: #f6f7fb;
  color: #667eea;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
}
.build-toggle:hover {
  background: #eef1ff;
}
.btn-build {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #667eea;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.btn-build:hover {
  opacity: 0.9;
}
.btn-build:disabled {
  opacity: 0.5;
}
.who {
  font-weight: 700;
  color: #333;
  font-size: 15px;
}
.hint {
  color: #999;
  font-size: 12px;
  margin-top: 2px;
}
.btn-archive {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #27ae60;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.btn-archive:hover {
  opacity: 0.9;
}
.btn-archive:disabled {
  opacity: 0.5;
}
.actions {
  display: flex;
  gap: 8px;
}
.btn-download {
  padding: 8px 16px;
  border: 1px solid #667eea;
  border-radius: 8px;
  background: #fff;
  color: #667eea;
  font-weight: 600;
  cursor: pointer;
}
.btn-download:hover {
  background: #f0f2ff;
}
.btn-download:disabled {
  opacity: 0.5;
}
.btn-ears {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #8e44ad;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.btn-ears:hover {
  opacity: 0.9;
}
.btn-ears:disabled {
  opacity: 0.5;
}
.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.empty {
  color: #aaa;
  text-align: center;
  margin: auto;
}
.msg-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.msg-row.user {
  flex-direction: row-reverse;
}
.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #667eea;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
}
.msg-row:not(.user) .bubble {
  background: #f1f3f9;
  color: #333;
  border-top-left-radius: 4px;
}
.msg-row.user .bubble {
  background: #667eea;
  color: #fff;
  border-top-right-radius: 4px;
  white-space: pre-wrap;
}
.bubble :deep(p) {
  margin: 0 0 8px;
}
.bubble :deep(p:last-child) {
  margin-bottom: 0;
}
.bubble :deep(code) {
  background: rgba(0, 0, 0, 0.08);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 13px;
}
.bubble :deep(pre) {
  background: #282c34;
  color: #eee;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}
.chat-input {
  display: flex;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #eee;
  background: #fafafa;
}
.chat-input textarea {
  flex: 1;
  resize: none;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}
.chat-input textarea:focus {
  outline: none;
  border-color: #667eea;
}
.send {
  align-self: flex-end;
  padding: 10px 22px;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>