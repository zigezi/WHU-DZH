<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ sessionId: Number })
const emit = defineEmits(['installed', 'close'])

const apiBase = import.meta.env.DEV ? 'http://127.0.0.1:3000/api' : '/api'
const token = localStorage.getItem('token')

const query = ref('')
const results = ref([])
const installed = ref([])
const loading = ref(false)
const installing = ref(null) // 当前正在安装的 skill id
const detail = ref(null) // 选中查看详情的 skill

async function api(path, opts = {}) {
  return fetch(`${apiBase}${path}`, {
    ...opts,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...(opts.headers || {}) },
  })
}

async function search() {
  if (!query.value.trim()) { results.value = []; return }
  loading.value = true
  try {
    const r = await api(`/modelscope/skills/search?q=${encodeURIComponent(query.value)}&size=15`)
    const data = await r.json()
    results.value = data?.data?.skills || []
  } catch { results.value = [] }
  finally { loading.value = false }
}

async function loadInstalled() {
  if (!props.sessionId) return
  try {
    const r = await api(`/modelscope/skills/installed/${props.sessionId}`)
    const data = await r.json()
    installed.value = (data.skills || []).map((s) => s.id)
  } catch {}
}

async function showDetail(skill) {
  detail.value = { ...skill, loading: true }
  try {
    // skill.id 格式 "@owner/name" → 分割
    const raw = skill.id.replace(/^@/, '')
    const r = await api(`/modelscope/skills/@${raw}`)
    const data = await r.json()
    detail.value = { ...skill, ...(data.data || data), loading: false }
  } catch { detail.value = { ...skill, loading: false } }
}

async function installSkill(skill) {
  if (!props.sessionId) return
  installing.value = skill.id
  try {
    const r = await api('/modelscope/skills/install', {
      method: 'POST',
      body: JSON.stringify({ sessionId: props.sessionId, skillId: skill.id }),
    })
    const data = await r.json()
    if (r.ok) {
      installed.value.push(skill.id)
      emit('installed', { skillId: skill.id, ...data })
    } else {
      alert(data.message || data.hint || '安装失败')
    }
  } catch { alert('安装失败，请稍后重试') }
  finally { installing.value = null }
}

watch(() => props.sessionId, loadInstalled, { immediate: true })
</script>

<template>
  <div class="skill-panel">
    <div class="sp-header">
      <h3>🔍 搜索 ModelScope 技能</h3>
      <button class="sp-close" @click="$emit('close')">✕</button>
    </div>

    <div class="sp-search-row">
      <input v-model="query" placeholder="搜索关键词（如：天气、支付、爬虫...）" @keydown.enter="search" autofocus />
      <button @click="search" :disabled="loading">{{ loading ? '搜索中...' : '搜索' }}</button>
    </div>

    <!-- 搜索结果 -->
    <div v-if="results.length" class="sp-results">
      <div
        v-for="skill in results"
        :key="skill.id"
        :class="['sp-card', { installed: installed.includes(skill.id) }]"
        @click="showDetail(skill)"
      >
        <div class="sp-card-top">
          <span class="sp-name">{{ skill.display_name || skill.id }}</span>
          <span v-if="installed.includes(skill.id)" class="sp-badge">已安装</span>
        </div>
        <div class="sp-desc">{{ skill.description }}</div>
        <div class="sp-meta">
          <span v-if="skill.downloads">↓ {{ skill.downloads }}</span>
          <span v-if="skill.view_count">👁 {{ skill.view_count }}</span>
          <span v-if="skill.category">{{ skill.category }}</span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && query" class="sp-empty">无结果，换个关键词试试？</div>

    <!-- 详情弹窗 -->
    <div v-if="detail" class="sp-detail-overlay" @click.self="detail = null">
      <div class="sp-detail">
        <div class="sp-detail-header">
          <h3>{{ detail.display_name || detail.id }}</h3>
          <button class="sp-close" @click="detail = null">✕</button>
        </div>
        <div v-if="detail.loading" class="sp-detail-loading">加载中...</div>
        <template v-else>
          <p class="sp-detail-desc">{{ detail.description }}</p>
          <div v-if="detail.readme" class="sp-detail-readme">
            <pre>{{ detail.readme }}</pre>
          </div>
          <div class="sp-detail-actions">
            <button
              v-if="!installed.includes(detail.id)"
              class="sp-install-btn"
              :disabled="installing === detail.id"
              @click="installSkill(detail)"
            >
              {{ installing === detail.id ? '安装中...' : '📦 安装到当前会话' }}
            </button>
            <span v-else class="sp-installed-text">✅ 已安装</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.skill-panel { display:flex; flex-direction:column; height:100%; background:#fff; }
.sp-header { display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-bottom:1px solid #eee; }
.sp-header h3 { margin:0; font-size:15px; color:#333; }
.sp-close { background:none; border:none; font-size:18px; cursor:pointer; color:#999; padding:4px 8px; }
.sp-close:hover { color:#333; }
.sp-search-row { display:flex; gap:8px; padding:12px 16px; }
.sp-search-row input { flex:1; padding:8px 12px; border:1px solid #ddd; border-radius:6px; font-size:14px; }
.sp-search-row input:focus { outline:none; border-color:#667eea; }
.sp-search-row button { padding:8px 16px; background:#667eea; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:14px; white-space:nowrap; }
.sp-search-row button:hover { opacity:0.9; }
.sp-search-row button:disabled { opacity:0.5; }
.sp-results { flex:1; overflow-y:auto; padding:0 16px 16px; display:flex; flex-direction:column; gap:8px; }
.sp-card { border:1px solid #eee; border-radius:8px; padding:12px; cursor:pointer; transition:border-color 0.2s; }
.sp-card:hover { border-color:#667eea; }
.sp-card.installed { border-color:#27ae60; background:#f0fff4; }
.sp-card-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.sp-name { font-weight:600; font-size:14px; color:#333; }
.sp-badge { font-size:11px; background:#27ae60; color:#fff; padding:2px 8px; border-radius:10px; }
.sp-desc { font-size:13px; color:#666; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.sp-meta { font-size:11px; color:#999; margin-top:6px; display:flex; gap:12px; }
.sp-empty { text-align:center; color:#999; padding:40px 16px; font-size:14px; }
.sp-detail-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.4); display:flex; align-items:center; justify-content:center; z-index:1000; }
.sp-detail { background:#fff; border-radius:12px; width:520px; max-height:80vh; display:flex; flex-direction:column; box-shadow:0 10px 40px rgba(0,0,0,0.3); }
.sp-detail-header { display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid #eee; }
.sp-detail-header h3 { margin:0; font-size:16px; }
.sp-detail-loading { padding:40px; text-align:center; color:#999; }
.sp-detail-desc { padding:0 20px; font-size:14px; color:#555; margin:12px 0; }
.sp-detail-readme { margin:0 20px; max-height:300px; overflow-y:auto; background:#f8f8f8; border-radius:8px; padding:12px; }
.sp-detail-readme pre { margin:0; font-size:12px; white-space:pre-wrap; word-break:break-word; }
.sp-detail-actions { padding:16px 20px; border-top:1px solid #eee; }
.sp-install-btn { width:100%; padding:10px; background:#667eea; color:#fff; border:none; border-radius:8px; font-size:15px; cursor:pointer; font-weight:600; }
.sp-install-btn:hover { opacity:0.9; }
.sp-install-btn:disabled { opacity:0.5; cursor:not-allowed; }
.sp-installed-text { text-align:center; display:block; color:#27ae60; font-weight:600; }
</style>
