<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="抓取与总结"
    width="560px"
    :close-on-click-modal="false"
    @closed="resetState">

    <!-- 初始状态：触发按钮 -->
    <div v-if="!taskId" style="text-align: center; padding: 24px">
      <p style="margin-bottom: 16px; color: #606266">触发 RSS 抓取并调用 AI 生成中文摘要日报</p>
      <el-button type="primary" size="large" @click="startFetch" :loading="fetching">
        开始抓取
      </el-button>
    </div>

    <!-- 任务进行中 -->
    <div v-else>
      <el-steps :active="stepIndex" finish-status="success" align-center>
        <el-step title="抓取 RSS" :description="stepDescriptions[0]" />
        <el-step title="AI 总结" :description="stepDescriptions[1]" />
        <el-step title="完成" :description="stepDescriptions[2]" />
      </el-steps>

      <!-- 结果统计 -->
      <div v-if="taskDone" class="result-box">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="RSS 源数">{{ taskResult.source_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="文章数">{{ taskResult.article_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="总结成功">{{ taskResult.summary_success || 0 }}</el-descriptions-item>
          <el-descriptions-item label="总结失败">{{ taskResult.summary_failed || 0 }}</el-descriptions-item>
          <el-descriptions-item label="触发方式">{{ taskResult.trigger_source || '-' }}</el-descriptions-item>
          <el-descriptions-item label="任务 ID">{{ taskId }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </div>

    <template #footer v-if="taskDone">
      <el-button type="primary" @click="closeAndDone">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { triggerFetch, getTaskStatus } from '../api/index.js'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['update:visible', 'done'])

const fetching = ref(false)
const taskId = ref('')
const taskResult = ref({})
const taskDone = ref(false)
const currentStage = ref('')

let pollTimer = null

const stepIndex = computed(() => {
  if (taskDone.value) return 3
  if (currentStage.value === 'summarizing') return 1
  if (currentStage.value === 'fetching') return 0
  return 0
})

const stepDescriptions = computed(() => {
  const fetchingDesc = currentStage.value === 'fetching' ? '抓取中...' : (taskDone.value ? '已完成' : '')
  const summarizingDesc = currentStage.value === 'summarizing' ? '总结中...' : (taskDone.value ? '已完成' : '')
  const doneDesc = taskDone.value ? '日报已生成' : ''
  return [fetchingDesc, summarizingDesc, doneDesc]
})

async function startFetch() {
  fetching.value = true
  try {
    const res = await triggerFetch()
    taskId.value = res.data.task_id
    startPolling(res.data.task_id)
  } catch (e) {
    // ignore
  } finally {
    fetching.value = false
  }
}

function startPolling(id) {
  pollTimer = setInterval(async () => {
    try {
      const res = await getTaskStatus(id)
      const t = res.data
      currentStage.value = t.stage || ''
      if (t.status === 'done' || t.status === 'error' || t.result) {
        taskDone.value = true
        taskResult.value = t.result || {}
        clearInterval(pollTimer)
      }
    } catch {
      // polling error, ignore
    }
  }, 3000)
}

function resetState() {
  clearInterval(pollTimer)
  taskId.value = ''
  taskResult.value = {}
  taskDone.value = false
  currentStage.value = ''
}

function closeAndDone() {
  emit('done')
  emit('update:visible', false)
  resetState()
}

onUnmounted(() => {
  clearInterval(pollTimer)
})
</script>

<style scoped>
.result-box {
  margin-top: 24px;
}
</style>
