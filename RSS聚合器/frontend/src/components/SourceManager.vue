<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="RSS 源管理"
    direction="rtl"
    size="720px"
    <!-- 手动添加 -->
    <div class="add-section">
      <el-input v-model="newName" placeholder="源名称" style="width: 200px; margin-right: 8px" />
      <el-input v-model="newUrl" placeholder="RSS URL" style="width: 320px; margin-right: 8px" />
      <el-button type="primary" @click="addSource" :loading="adding">添加</el-button>
    </div>

    <div v-loading="loading" style="min-height: 200px">
      <!-- 已有源列表 -->
      <el-table :data="sources" max-height="400" style="width: 100%; margin-top: 16px">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" width="160" />
        <el-table-column prop="url" label="URL" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="toggleSource(row)" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button link type="primary" @click="startEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="removeSource(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 推荐源 -->
      <h3 style="margin: 24px 0 12px; color: #303133">推荐 RSS 源</h3>
      <el-collapse>
        <el-collapse-item
          v-for="(sources, category) in recommendations"
          :key="category"
          :title="`${category} (${sources.length})`"
          :name="category">
          <div v-for="src in sources" :key="src.url" class="rec-item">
            <el-checkbox
              v-model="src._checked"
              :disabled="existingUrls.has(src.url)"
              style="flex:1">
              {{ src.name }}
              <span class="rec-url">{{ src.url }}</span>
            </el-checkbox>
            <el-tag v-if="existingUrls.has(src.url)" size="small" type="info">已添加</el-tag>
          </div>
        </el-collapse-item>
      </el-collapse>

      <div style="margin-top: 16px" v-if="hasCheckedRecommendations">
        <el-button type="primary" @click="bulkAdd" :loading="bulkAdding">
          批量添加选中源 ({{ checkedCount }})
        </el-button>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑 RSS 源" width="420px" append-to-body>
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="URL">
          <el-input v-model="editForm.url" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listSources, createSource, updateSource, deleteSource,
  getRecommendations, bulkAddSources
} from '../api/index.js'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['update:visible', 'sourcesChanged'])

const sources = ref([])
const recommendations = ref({})
const existingUrls = computed(() => new Set(sources.value.map(s => s.url)))

const newName = ref('')
const newUrl = ref('')
const adding = ref(false)

const editVisible = ref(false)
const editForm = reactive({ id: null, name: '', url: '' })
const saving = ref(false)

const bulkAdding = ref(false)

const checkedCount = computed(() => {
  let n = 0
  for (const catSources of Object.values(recommendations.value)) {
    for (const src of catSources) {
      if (src._checked) n++
    }
  }
  return n
})

const hasCheckedRecommendations = computed(() => checkedCount.value > 0)

async function loadSources() {
  try {
    const res = await listSources()
    sources.value = res.data
  } catch {
    // ignore
  }
}

async function loadRecommendations() {
  try {
    const res = await getRecommendations()
    const cats = res.data.categories || {}
    for (const srcs of Object.values(cats)) {
      for (const src of srcs) {
        src._checked = false
      }
    }
    recommendations.value = cats
  } catch {
    // ignore
  }
}

async function addSource() {
  if (!newName.value || !newUrl.value) {
    ElMessage.warning('请填写名称和 URL')
    return
  }
  adding.value = true
  try {
    await createSource({ name: newName.value, url: newUrl.value })
    ElMessage.success('添加成功')
    newName.value = ''
    newUrl.value = ''
    await loadSources()
    emit('sourcesChanged')
  } catch (e) {
    ElMessage.error('添加失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    adding.value = false
  }
}

function startEdit(row) {
  editForm.id = row.id
  editForm.name = row.name
  editForm.url = row.url
  editVisible.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    await updateSource(editForm.id, { name: editForm.name, url: editForm.url })
    ElMessage.success('修改成功')
    editVisible.value = false
    await loadSources()
    emit('sourcesChanged')
  } catch (e) {
    ElMessage.error('修改失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function toggleSource(row) {
  try {
    await updateSource(row.id, { is_active: row.is_active })
  } catch {
    row.is_active = !row.is_active // revert
  }
}

async function removeSource(row) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.name}」及其所有文章吗？`, '确认删除', {
      type: 'warning'
    })
    await deleteSource(row.id)
    ElMessage.success('删除成功')
    await loadSources()
    emit('sourcesChanged')
  } catch {
    // cancelled
  }
}

async function bulkAdd() {
  const urls = []
  for (const catSources of Object.values(recommendations.value)) {
    for (const src of catSources) {
      if (src._checked) urls.push(src.url)
    }
  }
  if (urls.length === 0) return
  bulkAdding.value = true
  try {
    const res = await bulkAddSources(urls)
    ElMessage.success(`已添加 ${res.data.added} 个源` + (res.data.skipped > 0 ? `，${res.data.skipped} 个已存在跳过` : ''))
    await loadSources()
    emit('sourcesChanged')
  } catch (e) {
    ElMessage.error('批量添加失败')
  } finally {
    bulkAdding.value = false
  }
}

const loading = ref(true)

async function loadAll() {
  loading.value = true
  await Promise.all([loadSources(), loadRecommendations()])
  await nextTick()
  loading.value = false
}

onMounted(() => {
  nextTick(() => {
    loadAll()
  })
})
</script>

<style scoped>
.add-section {
  display: flex;
  align-items: center;
}

.rec-item {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}

.rec-url {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}
</style>
