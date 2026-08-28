<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import FileTree from './FileTree.vue'

const props = defineProps({
  sessionId: { type: [String, Number], required: true },
  token: { type: String, required: true },
})

const apiBase = import.meta.env.DEV ? 'http://127.0.0.1:3000/api' : '/api'
const rootUrl = apiBase.replace(/\/api$/, '')

const tab = ref('log')
const build = ref(null)
const ears = ref(false)
const status = ref('queued')
const iterations = ref(0)
const events = ref([])
const files = ref([])
const selected = ref(null)
const fileContent = ref('')
const versions = ref([])
const busy = ref(false)
const modifyInput = ref('')
const es = ref(null)

const statusLabel = { queued: '排队中', coding: '代码生成', validating: '验证中', debugging: '修复中', modifying: '修改中', passed: '已通过', failed: '失败' }

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

async function loadState(openEvents = false) {
  const res = await api(`/sessions/${props.sessionId}/build`)
  if (!res.ok) return
  const data = await res.json()
  build.value = data.build
  ears.value = !!data.ears
  if (data.build) {
    status.value = data.build.status
    iterations.value = data.build.iterations || 0
    if (openEvents && !['passed', 'failed'].includes(data.build.status)) connectEvents(data.build.id)
  }
}

function connectEvents(buildId) {
  closeEvents()
  const source = new EventSource(`${apiBase}/builds/${buildId}/events?token=${encodeURIComponent(props.token)}`)
  source.addEventListener('status', (e) => {
    const d = JSON.parse(e.data)
    status.value = d.status
    if (typeof d.iterations === 'number') iterations.value = d.iterations
  })
  source.addEventListener('event', (e) => {
    const d = JSON.parse(e.data)
    events.value.push({ id: d.id, agent: d.agent, event_type: d.event_type, content: d.content, created_at: d.created_at })
  })
  source.addEventListener('done', (e) => {
    const d = JSON.parse(e.data)
    status.value = d.status
    source.close()
    refreshFilesAndVersions()
  })
  source.onerror = () => {
    /* EventSource 自动重连 */
  }
  es.value = source
}

function closeEvents() {
  if (es.value) {
    es.value.close()
    es.value = null
  }
}

async function startBuild() {
  busy.value = true
  try {
    const res = await api(`/sessions/${props.sessionId}/build`, { method: 'POST' })
    const data = await res.json()
    if (!res.ok) { alert(data.message || '触发构建失败'); return }
    events.value = []
    build.value = { id: data.buildId, status: 'queued' }
    status.value = 'queued'
    iterations.value = 0
    connectEvents(data.buildId)
  } finally {
    busy.value = false
  }
}

async function modify() {
  const instruction = modifyInput.value.trim()
  if (!instruction || !build.value) return
  busy.value = true
  try {
    const res = await api(`/builds/${build.value.id}/modify`, { method: 'POST', body: JSON.stringify({ instruction }) })
    const data = await res.json()
    if (!res.ok) { alert(data.message || '修改失败'); return }
    events.value = []
    status.value = 'modifying'
    connectEvents(build.value.id)
  } finally {
    busy.value = false
  }
}

async function revalidate() {
  if (!build.value) return
  busy.value = true
  try {
    const res = await api(`/builds/${build.value.id}/revalidate`, { method: 'POST' })
    const data = await res.json()
    if (!res.ok) { alert(data.message || '重新验证失败'); return }
    events.value = []
    status.value = 'validating'
    connectEvents(build.value.id)
  } finally {
    busy.value = false
  }
}

async function loadFiles() {
  const res = await api(`/sessions/${props.sessionId}/build/files`)
  if (res.ok) files.value = (await res.json()).files
}

async function viewFile(node) {
  selected.value = node
  const res = await api(`/sessions/${props.sessionId}/build/file?path=${encodeURIComponent(node.path)}`)
  if (res.ok) fileContent.value = (await res.json()).content
  else fileContent.value = `加载失败: ${(await res.json()).message || ''}`
}

async function loadVersions() {
  const res = await api(`/sessions/${props.sessionId}/build/versions`)
  if (res.ok) versions.value = (await res.json()).versions
}

async function refreshFilesAndVersions() {
  await loadFiles()
  await loadVersions()
}

async function restore(hash) {
  if (!confirm(`确认恢复到版本 ${hash}？工作区将与该版本完全一致。`)) return
  busy.value = true
  try {
    const res = await api(`/sessions/${props.sessionId}/build/restore`, { method: 'POST', body: JSON.stringify({ hash }) })
    const data = await res.json()
    if (!res.ok) { alert(data.message || '回滚失败'); return }
    status.value = 'validating'
    connectEvents(build.value.id)
  } finally {
    busy.value = false
  }
}

async function downloadZip() {
  const res = await api(`/sessions/${props.sessionId}/build/download`)
  if (!res.ok) { alert('下载失败'); return }
  const blob = await res.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${props.sessionId}-build.zip`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(a.href)
}

function fmtTime(iso) {
  return iso ? new Date(iso).toLocaleString() : ''
}

// 远程部署（node-service 在 8G 服务器）时预览直连其 URL；本地静态应用走 /preview 注入通道
const remoteUrl = ref('')

async function loadDeployUrl() {
  try {
    const res = await api(`/sessions/${props.sessionId}/container`)
    if (!res.ok) return
    const data = await res.json()
    const url = data.deploy && data.deploy.status === 'running' ? data.deploy.url : ''
    // 仅当 url 为绝对地址且非本机回环时视为远程部署
    remoteUrl.value = url && /^https?:\/\//.test(url) && !url.includes('127.0.0.1') ? url : ''
  } catch { /* 忽略，保持本地预览 */ }
}

function previewSrc() {
  return remoteUrl.value || `${rootUrl}/preview/${props.sessionId}/?token=${encodeURIComponent(props.token)}`
}

function newWindowHref() {
  return remoteUrl.value || `${rootUrl}/preview/${props.sessionId}/?token=${encodeURIComponent(props.token)}`
}

onMounted(async () => {
  await loadState(true)
  await loadFiles()
  await loadVersions()
  await loadDeployUrl()
})
onBeforeUnmount(closeEvents)
</script>

<template>
  <div class="bp">
    <header class="bp-head">
      <div class="tabs">
        <button v-for="t in ['log', 'file', 'preview', 'version']" :key="t"
          :class="['tab', { active: tab === t }]" @click="tab = t">
          {{ { log: '构建日志', file: '文件', preview: '预览', version: '版本' }[t] }}
        </button>
      </div>
      <div class="badge" :class="status">
        <span class="dot"></span>
        {{ statusLabel[status] || status }}<span v-if="['coding', 'debugging', 'validating', 'modifying'].includes(status)">（第 {{ iterations }}/8 轮）</span>
      </div>
    </header>

    <p v-if="!ears && !build" class="ears-hint">
      尚未生成 EARS 规格。请先点击顶部「⬇ 下载低歧义EARS需求」完成转换，然后即可「生成应用」。
    </p>
    <div class="build-inputs">
      <button class="btn" :disabled="busy" @click="startBuild">生成应用</button>
      <input v-model="modifyInput" placeholder="输入修改指令，如：苹果数量改为 15" :disabled="busy" @keydown.enter="modify" />
      <button class="btn" :disabled="busy || !modifyInput.trim()" @click="modify">修改</button>
      <button class="btn" :disabled="busy" @click="revalidate">重新验证</button>
      <button class="btn" :disabled="busy" @click="downloadZip">下载 ZIP</button>
      <a v-if="status === 'passed'" class="btn ghost" :href="newWindowHref()" target="_blank" rel="noopener">新窗口打开</a>
    </div>

    <div class="bp-body">
      <!-- 构建日志 -->
      <div v-if="tab === 'log'" class="log-list">
        <div v-for="ev in events" :key="ev.id" class="log-item">
          <span class="agent" :class="ev.agent">{{ ev.agent }}</span>
          <span class="etype">{{ ev.event_type }}</span>
          <span class="ev-time">{{ fmtTime(ev.created_at) }}</span>
          <pre class="ev-content">{{ ev.content }}</pre>
        </div>
        <p v-if="events.length === 0" class="empty">暂无日志。触发一次构建后这里将实时滚动显示 coder / sandbox / debugger 的活动。</p>
      </div>

      <!-- 文件 -->
      <div v-else-if="tab === 'file'" class="file-tab">
        <div class="file-left">
          <FileTree :nodes="files" @select="viewFile" />
          <p v-if="files.length === 0" class="empty">尚未生成文件</p>
        </div>
        <div class="file-right">
          <div class="file-name">{{ selected ? selected.path : '（点击左侧文件查看内容）' }}</div>
          <pre class="code">{{ fileContent }}</pre>
        </div>
      </div>

      <!-- 预览 -->
      <div v-else-if="tab === 'preview'" class="preview-tab">
        <p v-if="status !== 'passed'" class="empty">构建通过后即可预览运行效果（当前状态：{{ statusLabel[status] }}）。</p>
        <iframe v-else :src="previewSrc()" class="preview-frame" :sandbox="remoteUrl ? 'allow-scripts allow-same-origin allow-forms' : 'allow-scripts'"></iframe>
      </div>

      <!-- 版本 -->
      <div v-else class="version-tab">
        <table class="vtable">
          <thead><tr><th>版本</th><th>说明</th><th>时间</th><th></th></tr></thead>
          <tbody>
            <tr v-for="v in versions" :key="v.hash">
              <td class="mono">{{ v.hash.slice(0, 8) }}</td>
              <td>{{ v.message }}</td>
              <td>{{ fmtTime(v.time) }}</td>
              <td><button class="mini" :disabled="busy" @click="restore(v.hash)">恢复到此版本</button></td>
            </tr>
          </tbody>
        </table>
        <p v-if="versions.length === 0" class="empty">暂无版本记录</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bp {
  background: #fff;
  border-top: 1px solid #eee;
  display: flex;
  flex-direction: column;
  height: 60vh;
  min-height: 320px;
}
.bp-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-bottom: 1px solid #eee;
  gap: 10px;
  flex-wrap: wrap;
}
.tabs { display: flex; gap: 4px; }
.tab {
  padding: 6px 12px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 13px;
  color: #888;
  border-bottom: 2px solid transparent;
}
.tab.active { color: #667eea; border-bottom-color: #667eea; font-weight: 600; }
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  background: #f1f3f9;
  color: #555;
}
.badge .dot { width: 8px; height: 8px; border-radius: 50%; background: #bbb; }
.badge.passed { background: #e8f8ee; color: #1a7f37; }
.badge.passed .dot { background: #1a7f37; }
.badge.failed { background: #fdecea; color: #c0392b; }
.badge.failed .dot { background: #c0392b; }
.badge.coding, .badge.debugging, .badge.validating, .badge.modifying { background: #fff6e6; color: #b5651d; }
.badge.coding .dot, .badge.debugging .dot, .badge.validating .dot, .badge.modifying .dot { background: #e5a50a; }
.badge.queued { color: #6c757d; }

.build-inputs { display: flex; gap: 8px; padding: 10px 14px; flex-wrap: wrap; align-items: center; border-bottom: 1px solid #f0f0f0; }
.build-inputs input { flex: 1; min-width: 180px; padding: 8px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.btn { padding: 7px 14px; border: none; border-radius: 6px; background: #667eea; color: #fff; font-size: 13px; cursor: pointer; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn.ghost { background: #fff; color: #667eea; border: 1px solid #667eea; text-decoration: none; }

.log-list { flex: 1; overflow-y: auto; padding: 10px 14px; }
.log-item { margin-bottom: 10px; }
.agent { display: inline-block; padding: 1px 7px; border-radius: 4px; font-size: 11px; color: #fff; background: #95a5a6; margin-right: 6px; }
.agent.coder { background: #667eea; }
.agent.sandbox { background: #27ae60; }
.agent.debugger { background: #e67e22; }
.agent.system { background: #95a5a6; }
.etype { font-size: 11px; color: #999; margin-right: 6px; }
.ev-time { font-size: 11px; color: #bbb; }
.ev-content { margin: 4px 0 0; background: #f6f7fb; padding: 8px; border-radius: 6px; font-size: 12px; white-space: pre-wrap; word-break: break-all; max-height: 160px; overflow: auto; }

.file-tab { flex: 1; display: flex; height: 100%; overflow: hidden; }
.file-left { width: 42%; max-width: 340px; overflow: auto; padding: 10px; border-right: 1px solid #eee; }
.file-right { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
.file-name { padding: 8px 12px; font-size: 12px; color: #999; border-bottom: 1px solid #f0f0f0; }
.code { flex: 1; margin: 0; padding: 12px; overflow: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; line-height: 1.5; }

.preview-tab { flex: 1; display: flex; flex-direction: column; height: 100%; }
.preview-frame { flex: 1; width: 100%; border: none; background: #fff; }

.version-tab { flex: 1; overflow: auto; }
.vtable { width: 100%; border-collapse: collapse; font-size: 13px; }
.vtable th, .vtable td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #f0f0f0; }
.mono { font-family: ui-monospace, monospace; }
.mini { padding: 4px 8px; font-size: 12px; border: 1px solid #ddd; border-radius: 4px; background: #fff; color: #333; cursor: pointer; }
.empty { color: #aaa; text-align: center; padding: 20px; }
.ears-hint {
  margin: 0 0 10px;
  padding: 8px 12px;
  background: #fff8e1;
  border: 1px solid #ffe082;
  border-radius: 6px;
  color: #795548;
  font-size: 13px;
}
</style>