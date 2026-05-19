<template>
  <div id="app-container">
    <!-- 顶部导航 -->
    <el-header class="top-header">
      <div class="header-left">
        <h1>每日新闻聚合器</h1>
      </div>
      <div class="header-right">
        <el-tag :type="aiConfigured ? 'success' : 'danger'" size="large">
          {{ aiConfigured ? `AI已配置 (${aiProvider})` : 'AI未配置' }}
        </el-tag>
        <el-button type="primary" @click="showConfigDialog = true">
          <el-icon><Setting /></el-icon>
          设置 API Key
        </el-button>
      </div>
    </el-header>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="showSourceDrawer = true">
        <el-icon><FolderOpened /></el-icon>
        RSS 源管理
      </el-button>
      <el-button type="success" @click="showFetchDialog = true">
        <el-icon><RefreshRight /></el-icon>
        抓取与总结
      </el-button>
    </div>

    <!-- 主区域：日报 -->
    <div class="main-content">
      <DailyReport ref="dailyReportRef" />
    </div>

    <!-- AI 配置弹窗 -->
    <el-dialog v-model="showConfigDialog" title="AI 接口配置" width="520px" :close-on-click-modal="false" destroy-on-close>
      <el-form :model="configForm" label-position="top">
        <el-form-item label="API Key">
          <el-input v-model="configForm.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="接口地址 (Base URL)">
          <el-select v-model="configForm.base_url" filterable allow-create placeholder="选择或输入自定义地址">
            <el-option label="OpenAI" value="https://api.openai.com/v1" />
            <el-option label="DeepSeek" value="https://api.deepseek.com/v1" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-input v-model="configForm.model" placeholder="gpt-3.5-turbo / deepseek-chat" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" :loading="configSaving" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>

    <!-- RSS 源管理抽屉 -->
    <SourceManager
      v-if="showSourceDrawer"
      v-model:visible="showSourceDrawer"
      @sources-changed="checkAIConfig" />

    <!-- 抓取任务弹窗 -->
    <FetchTrigger
      v-if="showFetchDialog"
      v-model:visible="showFetchDialog"
      @done="onFetchDone" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, FolderOpened, RefreshRight } from '@element-plus/icons-vue'
import DailyReport from './components/DailyReport.vue'
import SourceManager from './components/SourceManager.vue'
import FetchTrigger from './components/FetchTrigger.vue'
import { checkOpenAIKey, setOpenAIKey } from './api/index.js'

const showConfigDialog = ref(false)
const showSourceDrawer = ref(false)
const showFetchDialog = ref(false)
const dailyReportRef = ref(null)

const aiConfigured = ref(false)
const aiProvider = ref('')
const configSaving = ref(false)

const configForm = reactive({
  api_key: '',
  base_url: 'https://api.openai.com/v1',
  model: 'gpt-3.5-turbo'
})

async function checkAIConfig() {
  try {
    const res = await checkOpenAIKey()
    aiConfigured.value = res.data.configured
    aiProvider.value = res.data.provider
    if (aiConfigured.value) {
      configForm.base_url = res.data.base_url || configForm.base_url
      configForm.model = res.data.model || configForm.model
    }
  } catch {
    // ignore
  }
}

async function saveConfig() {
  if (!configForm.api_key) {
    ElMessage.warning('请输入 API Key')
    return
  }
  configSaving.value = true
  try {
    await setOpenAIKey({
      api_key: configForm.api_key,
      base_url: configForm.base_url,
      model: configForm.model
    })
    ElMessage.success('AI 配置已保存')
    showConfigDialog.value = false
    await checkAIConfig()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    configSaving.value = false
  }
}

function onFetchDone() {
  dailyReportRef.value?.refresh()
}

onMounted(() => {
  checkAIConfig()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa;
}

#app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  padding: 0 24px;
  height: 60px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  flex-shrink: 0;
}

.top-header h1 {
  font-size: 20px;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
