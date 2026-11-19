<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, Refresh } from '@element-plus/icons-vue'

import {
  createResumeTemplate,
  listResumeTemplatesForAdmin,
  updateResumeTemplate,
  updateResumeTemplateEnabled,
  updateResumeTemplateSort,
} from '@/api/admin'
import { uploadFile } from '@/api/files'
import ModuleCard from '@/components/ModuleCard.vue'
import type { ResumeTemplate } from '@/types/api'

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const dialogVisible = ref(false)
const editing = ref<ResumeTemplate | null>(null)
const templates = ref<ResumeTemplate[]>([])

const form = reactive<ResumeTemplate>({
  templateName: '',
  templateCode: 'classic',
  coverFileId: undefined,
  coverUrl: '',
  description: '',
  enabled: 1,
  sortOrder: 0,
  version: 1,
})

async function load() {
  loading.value = true
  try {
    templates.value = await listResumeTemplatesForAdmin()
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form, {
    templateName: '',
    templateCode: 'classic',
    coverFileId: undefined,
    coverUrl: '',
    description: '',
    enabled: 1,
    sortOrder: 0,
    version: 1,
  })
}

function openCreate() {
  editing.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: ResumeTemplate) {
  editing.value = row
  Object.assign(form, { ...row })
  dialogVisible.value = true
}

async function onCoverChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  uploading.value = true
  try {
    const uploaded = await uploadFile(file, 'TEMPLATE_COVER')
    form.coverFileId = uploaded.id
    form.coverUrl = uploaded.fileUrl
    ElMessage.success('模板封面已上传')
  } finally {
    uploading.value = false
  }
}

async function save() {
  if (!form.templateName?.trim()) {
    ElMessage.warning('请填写模板名称')
    return
  }
  if (!form.templateCode?.trim()) {
    ElMessage.warning('请填写模板代码')
    return
  }
  saving.value = true
  try {
    if (editing.value?.id) {
      await updateResumeTemplate(editing.value.id, { ...form })
      ElMessage.success('模板已更新')
    } else {
      await createResumeTemplate({ ...form })
      ElMessage.success('模板已创建')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function toggleEnabled(row: ResumeTemplate) {
  if (!row.id) return
  const next = row.enabled !== 1
  await updateResumeTemplateEnabled(row.id, next)
  ElMessage.success(next ? '模板已启用' : '模板已停用')
  await load()
}

async function persistSort(row: ResumeTemplate) {
  if (!row.id) return
  await updateResumeTemplateSort(row.id, row.sortOrder || 0)
  ElMessage.success('排序已保存')
  await load()
}

onMounted(load)
</script>

<template>
  <ModuleCard title="模板管理" subtitle="维护简历生成模板的名称、封面、启用状态和排序">
    <template #actions>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
      <el-button type="primary" @click="openCreate">新增模板</el-button>
    </template>

    <el-table v-loading="loading" :data="templates" border>
      <el-table-column label="封面" width="104">
        <template #default="{ row }">
          <div class="cover">
            <img v-if="row.coverUrl" :src="row.coverUrl" :alt="row.templateName" />
            <el-icon v-else><Picture /></el-icon>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="templateName" label="模板名称" min-width="150" />
      <el-table-column prop="templateCode" label="模板代码" width="130" />
      <el-table-column prop="description" label="说明" min-width="220" show-overflow-tooltip />
      <el-table-column label="排序" width="160">
        <template #default="{ row }">
          <div class="sort-line">
            <el-input-number v-model="row.sortOrder" :min="0" :step="10" size="small" />
            <el-button link type="primary" @click="persistSort(row)">保存</el-button>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.enabled === 1 ? 'success' : 'info'" effect="plain">
            {{ row.enabled === 1 ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
          <el-button :type="row.enabled === 1 ? 'warning' : 'success'" link @click="toggleEnabled(row)">
            {{ row.enabled === 1 ? '停用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑模板' : '新增模板'" width="640px">
      <el-form :model="form" label-width="96px">
        <el-form-item label="模板名称" required>
          <el-input v-model="form.templateName" placeholder="如：经典专业版" />
        </el-form-item>
        <el-form-item label="模板代码" required>
          <el-select v-model="form.templateCode" filterable allow-create>
            <el-option label="经典专业版 classic" value="classic" />
            <el-option label="紧凑校园版 compact" value="compact" />
            <el-option label="项目突出版 project" value="project" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sortOrder" :min="0" :step="10" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input-number v-model="form.version" :min="1" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="模板封面">
          <div class="cover-upload">
            <div class="cover cover-large">
              <img v-if="form.coverUrl" :src="form.coverUrl" alt="模板封面" />
              <el-icon v-else><Picture /></el-icon>
            </div>
            <el-button :loading="uploading" type="primary" plain>
              上传封面
              <input type="file" accept=".jpg,.jpeg,.png,.webp" @change="onCoverChange" />
            </el-button>
            <span v-if="form.coverFileId" class="muted">文件 ID：{{ form.coverFileId }}</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </ModuleCard>
</template>

<style scoped>
.cover {
  width: 72px;
  height: 48px;
  display: grid;
  place-items: center;
  overflow: hidden;
  border: 1px solid var(--rp-border);
  border-radius: 8px;
  background: #f8fafc;
  color: #94a3b8;
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-large {
  width: 144px;
  height: 96px;
}

.cover-upload {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.cover-upload .el-button {
  position: relative;
  overflow: hidden;
}

.cover-upload input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.muted {
  color: var(--rp-muted);
  font-size: 13px;
}

.sort-line {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
