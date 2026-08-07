<script setup>
import { ref } from 'vue'

defineProps({ nodes: { type: Array, default: () => [] } })
const emit = defineEmits(['select'])
const expanded = ref({})

function toggle(node) {
  expanded.value[node.path] = !expanded.value[node.path]
}
function onNode(node) {
  if (node.type === 'dir') toggle(node)
  else emit('select', node)
}
</script>

<template>
  <ul class="tree" v-if="nodes && nodes.length">
    <li v-for="n in nodes" :key="n.path">
      <div class="row" :class="{ dir: n.type === 'dir' }" @click="onNode(n)">
        <span class="arrow">{{ n.type === 'dir' ? (expanded[n.path] ? '▾' : '▸') : '' }}</span>
        <span class="icon">{{ n.type === 'dir' ? '📁' : '📄' }}</span>
        <span class="name">{{ n.name }}</span>
      </div>
      <FileTree
        v-if="n.type === 'dir' && expanded[n.path]"
        :nodes="n.children"
        @select="(x) => emit('select', x)"
      />
    </li>
  </ul>
</template>

<style scoped>
.tree {
  list-style: none;
  margin: 0;
  padding: 0 0 0 14px;
}
.tree > :first-child {
  padding-left: 0;
}
.row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 6px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}
.row:hover {
  background: #eef1ff;
}
.row.dir {
  font-weight: 600;
}
.arrow {
  width: 12px;
  display: inline-block;
  opacity: 0.7;
}
.icon {
  opacity: 0.8;
}
.name {
  color: #333;
}
</style>