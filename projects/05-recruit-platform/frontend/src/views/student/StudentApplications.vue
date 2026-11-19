<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, View } from '@element-plus/icons-vue'

import { listStudentApplicationDetails, withdrawApplication } from '@/api/applications'
import { previewFile } from '@/api/files'
import ModuleCard from '@/components/ModuleCard.vue'
import type { StudentApplicationDetail } from '@/types/api'

const loading = ref(false)
const processing = ref(false)
const applications = ref<StudentApplicationDetail[]>([])
const statusFilter = ref('')
const keyword = ref('')

const previewVisible = ref(false)
const previewUrl = ref('')
const previewLoading = ref(false)
const previewError = ref('')
const previewTitle = ref('简历预览')

const detailVisible = ref(false)
const detailRow = ref<StudentApplicationDetail | null>(null)

const statusText: Record<string, string> = {
  PENDING: '待处理',
  PASSED: '已通过',
  REJECTED: '已拒绝',
}

const statusType: Record<string, string> = {
  PENDING: 'warning',
  PASSED: 'success',
  REJECTED: 'danger',
}

const filtered = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return applications.value.filter((item) => {
    const haystack = `${item.jobName || ''}${item.companyName || ''}${item.resumeName || ''}`.toLowerCase()
    const matchText = !text || haystack.includes(text)
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    return matchText && matchStatus
  })
})

const counts = computed(() => ({
  total: applications.value.length,
  pending: applications.value.filter((item) => item.status === 'PENDING').length,
  passed: applications.value.filter((item) => item.status === 'PASSED').length,
}))

function formatTime(value?: string) {
  return value ? value.replace('T', ' ').substring(0, 19) : '-'
}

async function load() {
  loading.value = true
  try {
    applications.value = await listStudentApplicationDetails()
  } finally {
    loading.value = false
  }
}

async function preview(row: StudentApplicationDetail) {
  if (!row.resumeFileId) {
    ElMessage.warning('该投递没有可预览简历')
    return
  }
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
  previewVisible.value = true
  previewLoading.value = true
  previewError.value = ''
  previewTitle.value = row.resumeName || '简历预览'
  try {
    const blob = await previewFile(row.resumeFileId)
    previewUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    previewError.value = error instanceof Error ? error.message : '简历预览失败'
  } finally {
    previewLoading.value = false
  }
}

async function withdraw(row: StudentApplicationDetail) {
  if (!row.id) return
  try {
    await ElMessageBox.confirm(`确定撤回「${row.jobName || '该岗位'}」的投递吗？`, '撤回确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  processing.value = true
  try {
    await withdrawApplication(row.id)
    ElMessage.success('投递已撤回')
    await load()
  } finally {
    processing.value = false
  }
}

function closePreview() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = ''
  previewError.value = ''
  previewVisible.value = false
}

function onRowClick(row: StudentApplicationDetail) {
  detailRow.value = row
  detailVisible.value = true
}

onMounted(load)
</script>

<template>
  <ModuleCard title="我的投递" subtitle="跟踪职位投递状态和企业反馈">
    <template #actions>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </template>

    <div class="application-stats">
      <div>
        <span>全部投递</span>
        <strong>{{ counts.total }}</strong>
      </div>
      <div>
        <span>待处理</span>
        <strong>{{ counts.pending }}</strong>
      </div>
      <div>
        <span>已通过</span>
        <strong>{{ counts.passed }}</strong>
      </div>
    </div>

    <div class="toolbar">
      <el-select v-model="statusFilter" clearable placeholder="全部状态" class="filter-item">
        <el-option v-for="(label, value) in statusText" :key="value" :label="label" :value="value" />
      </el-select>
      <el-input v-model="keyword" clearable placeholder="搜索职位、企业、简历" class="filter-search" />
    </div>

    <el-table v-loading="loading" :data="filtered" border @row-click="onRowClick">
      <el-table-column prop="jobName" label="职位" min-width="160" show-overflow-tooltip />
      <el-table-column prop="companyName" label="企业" min-width="150" show-overflow-tooltip />
      <el-table-column prop="city" label="城市" width="100" />
      <el-table-column prop="salaryRange" label="薪资" width="130" show-overflow-tooltip />
      <el-table-column prop="resumeName" label="投递简历" min-width="150" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType[row.status] || 'info'" effect="plain">
            {{ statusText[row.status] || row.status || '-' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="投递时间" width="170">
        <template #default="{ row }">{{ formatTime(row.createdAt) }}</template>
      </el-table-column>
      <el-table-column prop="remark" label="企业备注" min-width="160" show-overflow-tooltip />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button :icon="View" type="primary" link @click.stop="preview(row)">简历</el-button>
          <el-button
            v-if="row.status === 'PENDING'"
            type="danger"
            link
            :loading="processing"
            @click.stop="withdraw(row)"
          >
            撤回
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="previewVisible"
      :title="previewTitle"
      width="min(1180px, 96vw)"
      class="resume-preview-dialog"
      destroy-on-close
      @closed="closePreview"
    >
      <div v-loading="previewLoading" class="preview-container">
        <el-result v-if="previewError" icon="error" :title="previewError" />
        <iframe v-else-if="previewUrl" :src="previewUrl" class="preview-iframe" />
        <el-empty v-else-if="!previewLoading" description="无可预览内容" />
      </div>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="投递详情" width="540px">
      <el-descriptions v-if="detailRow" :column="1" border>
        <el-descriptions-item label="职位">{{ detailRow.jobName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="企业">{{ detailRow.companyName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="城市">{{ detailRow.city || '-' }}</el-descriptions-item>
        <el-descriptions-item label="薪资">{{ detailRow.salaryRange || '-' }}</el-descriptions-item>
        <el-descriptions-item label="投递简历">{{ detailRow.resumeName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType[detailRow.status || ''] || 'info'" effect="plain">
            {{ statusText[detailRow.status || ''] || detailRow.status || '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="企业备注">{{ detailRow.remark || '暂无备注' }}</el-descriptions-item>
        <el-descriptions-item label="投递时间">{{ formatTime(detailRow.createdAt) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </ModuleCard>
</template>

<style scoped>
.application-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.application-stats div {
  padding: 14px 16px;
  border: 1px solid var(--rp-border);
  border-radius: 8px;
  background: #f7fbff;
}

.application-stats span {
  color: var(--rp-muted);
  font-size: 13px;
}

.application-stats strong {
  display: block;
  margin-top: 8px;
  color: #0f1f35;
  font-size: 24px;
}

.toolbar {
  margin-bottom: 16px;
}

.filter-item {
  width: 150px;
}

.filter-search {
  width: 260px;
}

.preview-container {
  min-height: min(78vh, 860px);
  height: min(78vh, 860px);
}

:deep(.resume-preview-dialog .el-dialog__body) {
  padding-top: 12px;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: 1px solid var(--rp-border);
  border-radius: 8px;
}

@media (max-width: 720px) {
  .application-stats {
    grid-template-columns: 1fr;
  }

  .filter-search,
  .filter-item {
    width: 100%;
  }
}

:deep(.el-table__body tr) {
  cursor: pointer;
}
</style>
