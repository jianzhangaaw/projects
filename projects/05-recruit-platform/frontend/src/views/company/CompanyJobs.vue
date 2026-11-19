<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { getMyCompany } from '@/api/company'
import { createJob, deleteJob, listJobsByCompany, updateJob, updateJobStatus } from '@/api/jobs'
import ModuleCard from '@/components/ModuleCard.vue'
import { useAuthStore } from '@/stores/auth'
import type { Company, Job } from '@/types/api'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const drawerVisible = ref(false)
const company = ref<Company | null>(null)
const jobs = ref<Job[]>([])
const keyword = ref('')
const statusFilter = ref('')

const form = reactive<Job>({
  jobName: '',
  jobType: '',
  city: '',
  salaryRange: '',
  educationRequirement: '',
  majorRequirement: '',
  skillRequirement: '',
  description: '',
})

const statusText: Record<string, string> = {
  DRAFT: '草稿',
  PENDING: '待审核',
  PUBLISHED: '已发布',
  OFFLINE: '已下线',
  REJECTED: '已驳回',
}

const statusType: Record<string, string> = {
  DRAFT: 'info',
  PENDING: 'warning',
  PUBLISHED: 'success',
  OFFLINE: 'info',
  REJECTED: 'danger',
}

const canSubmit = computed(() => company.value?.reviewStatus === 'APPROVED')

const jobTypeOptions = ['技术', '产品', '运营', '设计', '市场', '职能', '金融', '其他']
const educationOptions = ['不限', '大专及以上', '本科及以上', '硕士及以上', '博士']
const salaryOptions = ['3k-5k', '5k-8k', '8k-12k', '12k-18k', '18k-25k', '25k-35k', '35k以上', '面议']
const cityOptions = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京', '西安', '重庆', '苏州', '天津', '长沙', '郑州', '青岛', '厦门', '合肥']

const filteredJobs = computed(() => {
  return jobs.value.filter((item) => {
    const text = `${item.jobName || ''}${item.city || ''}${item.jobType || ''}`
    const matchKeyword = !keyword.value || text.toLowerCase().includes(keyword.value.toLowerCase())
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    return matchKeyword && matchStatus
  })
})

function resetForm(job?: Job) {
  Object.assign(form, {
    id: job?.id,
    companyId: job?.companyId || company.value?.id,
    jobName: job?.jobName || '',
    jobType: job?.jobType || '',
    city: job?.city || '',
    salaryRange: job?.salaryRange || '',
    educationRequirement: job?.educationRequirement || '',
    majorRequirement: job?.majorRequirement || '',
    skillRequirement: job?.skillRequirement || '',
    description: job?.description || '',
    status: job?.status || 'DRAFT',
    reviewReason: job?.reviewReason,
  })
}

async function load() {
  if (!auth.userId) return
  loading.value = true
  try {
    company.value = await getMyCompany(auth.userId)
    jobs.value = company.value?.id ? await listJobsByCompany(company.value.id) : []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  resetForm()
  drawerVisible.value = true
}

function openEdit(row: Job) {
  resetForm(row)
  drawerVisible.value = true
}

async function saveWithStatus(status: 'DRAFT' | 'PENDING') {
  if (!company.value?.id) {
    ElMessage.warning('请先完善企业资料')
    return
  }
  if (status === 'PENDING' && !canSubmit.value) {
    ElMessage.warning('企业入驻审核通过后才能提交岗位审核')
    return
  }
  saving.value = true
  try {
    const payload: Job = { ...form, companyId: company.value.id, status }
    if (form.id) {
      await updateJob(form.id, payload)
    } else {
      await createJob(payload)
    }
    ElMessage.success(status === 'DRAFT' ? '职位草稿已保存' : '职位已提交审核')
    drawerVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function submitRow(row: Job) {
  if (!row.id) return
  if (!canSubmit.value) {
    ElMessage.warning('企业入驻审核通过后才能提交岗位审核')
    return
  }
  await updateJobStatus(row.id, 'PENDING')
  ElMessage.success('职位已提交审核')
  await load()
}

async function offlineRow(row: Job) {
  if (!row.id) return
  await updateJobStatus(row.id, 'OFFLINE')
  ElMessage.success('职位已下线')
  await load()
}

async function removeRow(row: Job) {
  if (!row.id) return
  await ElMessageBox.confirm('确定删除该职位吗？删除后不可恢复。', '删除职位', {
    type: 'warning',
  })
  await deleteJob(row.id)
  ElMessage.success('职位已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <ModuleCard title="职位管理" subtitle="发布、编辑和下线招聘职位">
    <template #actions>
      <el-button type="primary" @click="openCreate">发布职位</el-button>
    </template>

    <el-alert
      v-if="!company"
      class="notice"
      title="请先完善企业资料，再创建招聘职位"
      type="warning"
      show-icon
      :closable="false"
    />
    <el-alert
      v-else-if="company.reviewStatus !== 'APPROVED'"
      class="notice"
      title="企业入驻审核通过前，职位可以保存草稿，但不能提交审核"
      type="info"
      show-icon
      :closable="false"
    />

    <div class="jobs-filter-panel">
      <div class="jobs-filter-row">
        <el-input v-model="keyword" clearable placeholder="搜索职位、城市、类型" class="search" />
        <el-select v-model="statusFilter" clearable placeholder="全部状态" class="status-filter">
          <el-option v-for="(label, value) in statusText" :key="value" :label="label" :value="value" />
        </el-select>
        <el-button @click="load">刷新</el-button>
      </div>
      <div class="jobs-filter-meta">
        <strong>{{ filteredJobs.length }}</strong>
        <span>个职位符合当前筛选条件</span>
      </div>
    </div>

    <div class="jobs-table-shell">
    <el-table v-loading="loading" :data="filteredJobs" border height="430">
      <el-table-column prop="jobName" label="职位" min-width="170" />
      <el-table-column prop="city" label="城市" width="120" />
      <el-table-column prop="jobType" label="类型" width="120" />
      <el-table-column prop="salaryRange" label="薪资" width="140" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType[row.status] || 'info'">{{ statusText[row.status] || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updatedAt" label="更新时间" width="180" />
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <div class="job-row-actions">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button v-if="['DRAFT', 'REJECTED', 'OFFLINE'].includes(row.status)" type="success" link @click="submitRow(row)">
              提交审核
            </el-button>
            <el-button v-if="row.status === 'PUBLISHED'" type="warning" link @click="offlineRow(row)">下线</el-button>
            <el-button type="danger" link @click="removeRow(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <el-drawer v-model="drawerVisible" :title="form.id ? '编辑职位' : '发布职位'" size="520px">
      <el-form label-width="96px" class="job-form">
        <div class="form-section">
          <div class="form-section-heading">基础信息</div>
        <el-form-item label="职位名称">
          <el-input v-model="form.jobName" placeholder="例如：Java开发工程师" />
        </el-form-item>
        <el-form-item label="职位类型">
          <el-select v-model="form.jobType" placeholder="请选择职位类型" clearable class="full-width">
            <el-option v-for="t in jobTypeOptions" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="工作城市">
          <el-select v-model="form.city" placeholder="请选择城市" clearable filterable allow-create class="full-width">
            <el-option v-for="c in cityOptions" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="薪资范围">
          <el-select v-model="form.salaryRange" placeholder="请选择薪资范围" clearable class="full-width">
            <el-option v-for="s in salaryOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="学历要求">
          <el-select v-model="form.educationRequirement" placeholder="请选择学历要求" clearable class="full-width">
            <el-option v-for="e in educationOptions" :key="e" :label="e" :value="e" />
          </el-select>
        </el-form-item>
        </div>
        <div class="form-section">
          <div class="form-section-heading">职位要求</div>
        <el-form-item label="专业要求">
          <el-input v-model="form.majorRequirement" placeholder="例如：计算机相关专业" />
        </el-form-item>
        <el-form-item label="技能要求">
          <el-input v-model="form.skillRequirement" placeholder="例如：Java, Spring Boot, MySQL" />
        </el-form-item>
        <el-form-item label="职位描述">
          <el-input v-model="form.description" type="textarea" :rows="6" placeholder="描述岗位职责、培养计划和任职要求" />
        </el-form-item>
        </div>
        <el-alert v-if="form.reviewReason" class="notice" :title="form.reviewReason" type="error" show-icon :closable="false" />
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button :loading="saving" @click="saveWithStatus('DRAFT')">保存草稿</el-button>
        <el-button type="primary" :loading="saving" :disabled="!canSubmit" @click="saveWithStatus('PENDING')">
          提交审核
        </el-button>
      </template>
    </el-drawer>
  </ModuleCard>
</template>

<style scoped>
.notice {
  margin-bottom: 18px;
}

.jobs-filter-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 15px 16px;
  margin-bottom: 16px;
  border: 1px solid var(--rp-border);
  border-radius: var(--rp-radius-md);
  background: var(--rp-surface-muted);
}

.jobs-filter-row { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.jobs-filter-meta { display: flex; align-items: baseline; gap: 7px; color: var(--rp-muted); font-size: 12px; white-space: nowrap; }
.jobs-filter-meta strong { color: var(--rp-navy); font-size: 18px; font-variant-numeric: tabular-nums; }
.jobs-table-shell { width: 100%; overflow-x: auto; }
.job-row-actions { display: flex; align-items: center; gap: 3px; white-space: nowrap; }

.job-form { padding: 4px 2px 12px; }
.form-section { padding: 8px 0 5px; margin-bottom: 12px; border-bottom: 1px solid #edf1f7; }
.form-section-heading { margin: 0 0 15px; color: var(--rp-navy); font-size: 14px; font-weight: 800; }

.search {
  width: 260px;
}

.status-filter {
  width: 150px;
}

.full-width {
  width: 100%;
}

@media (max-width: 720px) {
  .jobs-filter-panel { align-items: flex-start; flex-direction: column; }
  .jobs-filter-row { width: 100%; }
  .jobs-filter-row .search { flex: 1 1 220px; }
  .jobs-filter-row .status-filter { flex: 1 1 150px; }
  .jobs-filter-meta { width: 100%; }
}
</style>
