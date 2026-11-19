<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Briefcase, DocumentChecked, OfficeBuilding, Tickets } from '@element-plus/icons-vue'

import { listCompanyApplicationDetails } from '@/api/applications'
import { getMyCompany } from '@/api/company'
import { getFileResource } from '@/api/files'
import { listJobsByCompany } from '@/api/jobs'
import ModuleCard from '@/components/ModuleCard.vue'
import { useAuthStore } from '@/stores/auth'
import type { Company, CompanyApplicationDetail, Job } from '@/types/api'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const company = ref<Company | null>(null)
const jobs = ref<Job[]>([])
const applications = ref<CompanyApplicationDetail[]>([])
const logoUrl = ref('')
const logoLoadError = ref(false)

const reviewText: Record<string, string> = {
  PENDING: '审核中',
  APPROVED: '已通过',
  REJECTED: '已驳回',
}

const reviewTagType = computed(() => {
  if (company.value?.reviewStatus === 'APPROVED') return 'success'
  if (company.value?.reviewStatus === 'REJECTED') return 'danger'
  return 'warning'
})

const statusLabel = (s: string | undefined) => {
  const map: Record<string, string> = { PENDING: '待处理', PASSED: '已通过', REJECTED: '已拒绝' }
  return map[s || ''] || s || '-'
}

const statusTag = (s: string | undefined) => {
  const map: Record<string, string> = { PENDING: 'warning', PASSED: 'success', REJECTED: 'danger' }
  return map[s || ''] || 'info'
}

const stats = computed(() => {
  const published = jobs.value.filter((item) => item.status === 'PUBLISHED').length
  const pending = jobs.value.filter((item) => item.status === 'PENDING').length
  const offline = jobs.value.filter((item) => item.status === 'OFFLINE').length
  const waiting = applications.value.filter((item) => item.status === 'PENDING').length
  return [
    { label: '全部岗位', value: jobs.value.length, icon: Briefcase, tone: 'blue' },
    { label: '已发布', value: published, icon: DocumentChecked, tone: 'cyan' },
    { label: '待审核', value: pending, icon: Tickets, tone: 'amber' },
    { label: '待处理投递', value: waiting, icon: OfficeBuilding, tone: 'indigo' },
    { label: '已下线', value: offline, icon: Briefcase, tone: 'gray' },
  ]
})

const recentApplications = computed(() => applications.value.slice(0, 6))

const logoFallback = computed(() => company.value?.companyName?.trim().charAt(0) || '企')
const displayLogoUrl = computed(() => (logoUrl.value && !logoLoadError.value ? logoUrl.value : ''))

async function loadLogo(fileId?: number) {
  logoUrl.value = ''
  logoLoadError.value = false
  if (!fileId) return
  try {
    const file = await getFileResource(fileId)
    logoUrl.value = file?.fileUrl || ''
    logoLoadError.value = false
  } catch {
    logoUrl.value = ''
    logoLoadError.value = false
  }
}

async function load() {
  if (!auth.userId) return
  loading.value = true
  try {
    company.value = await getMyCompany(auth.userId)
    await loadLogo(company.value?.logoFileId)
    if (company.value?.id) {
      const [jobRows, applicationRows] = await Promise.all([
        listJobsByCompany(company.value.id),
        listCompanyApplicationDetails(company.value.id),
      ])
      jobs.value = jobRows || []
      applications.value = applicationRows || []
    } else {
      jobs.value = []
      applications.value = []
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <ModuleCard title="企业工作台" subtitle="查看入驻状态、岗位与投递概览">
    <template #actions>
      <el-button type="primary" @click="router.push('/company/jobs')">发布职位</el-button>
    </template>

    <div v-loading="loading" class="dashboard-board">
      <div class="dashboard-intro">
        <span>招聘运营概览</span>
        <small>优先处理待审核岗位与待处理投递，保持招聘流程顺畅。</small>
      </div>
      <el-alert
        v-if="!company"
        title="请先完善企业资料并提交入驻审核"
        type="warning"
        show-icon
        :closable="false"
      >
        <template #default>
          <el-button type="warning" link @click="router.push('/company/info')">去完善资料</el-button>
        </template>
      </el-alert>

      <div v-else class="company-card">
        <div class="company-logo">
          <img v-if="displayLogoUrl" :src="displayLogoUrl" alt="企业Logo" @error="logoLoadError = true" />
          <span v-else>{{ logoFallback }}</span>
        </div>
        <div class="company-main">
          <div class="company-title-line">
            <div class="company-name">{{ company.companyName || '未填写企业名称' }}</div>
            <el-tag :type="reviewTagType" effect="light">
              {{ reviewText[company.reviewStatus || 'PENDING'] || company.reviewStatus }}
            </el-tag>
          </div>
          <div class="company-meta">
            <span>{{ company.industry || '未填写行业' }}</span>
            <span>{{ company.companySize || '未填写规模' }}</span>
            <span>联系人：{{ company.contactName || '未填写' }}</span>
            <span>电话：{{ company.contactPhone || '未填写' }}</span>
          </div>
          <div class="company-description">
            {{ company.description || '企业简介尚未填写，完善资料后学生和管理员可以更快了解企业。' }}
          </div>
        </div>
        <div class="company-actions">
          <div class="audit-card">
            <span>企业审核状态</span>
            <strong>{{ reviewText[company.reviewStatus || 'PENDING'] || company.reviewStatus }}</strong>
            <small v-if="company.reviewStatus === 'PENDING'">资料已提交，请等待审核</small>
            <small v-else-if="company.reviewStatus === 'APPROVED'">可发布岗位并处理投递</small>
            <small v-else>{{ company.reviewReason || '请根据审核意见修改资料' }}</small>
          </div>
          <el-button @click="router.push('/company/info')">维护资料</el-button>
        </div>
      </div>

      <div class="metric-grid">
        <div v-for="item in stats" :key="item.label" class="metric-tile" :class="`is-${item.tone}`">
          <el-icon class="metric-icon"><component :is="item.icon" /></el-icon>
          <div>
            <div class="metric-value">{{ item.value }}</div>
            <div class="metric-label">{{ item.label }}</div>
          </div>
        </div>
      </div>

      <div class="split">
        <section class="activity panel-card">
          <div class="section-title">近期投递</div>
          <el-table :data="recentApplications" height="280">
            <el-table-column prop="studentName" label="学生" width="120" />
            <el-table-column prop="jobName" label="投递岗位" min-width="160" />
            <el-table-column prop="school" label="学校" width="150" />
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="quick-panel panel-card">
          <div class="section-title">快捷入口</div>
          <el-button class="quick-button" @click="router.push('/company/info')">维护企业资料</el-button>
          <el-button class="quick-button" type="primary" @click="router.push('/company/jobs')">管理招聘岗位</el-button>
          <el-button class="quick-button" @click="router.push('/company/applications')">处理投递结果</el-button>
        </section>
      </div>
    </div>
  </ModuleCard>
</template>

<style scoped>
.dashboard-intro {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 13px 16px;
  border: 1px solid #dbe6f5;
  border-radius: var(--rp-radius-md);
  background: #f6f9fe;
}

.dashboard-intro span { color: var(--rp-navy); font-size: 14px; font-weight: 750; }
.dashboard-intro small { color: var(--rp-muted); font-size: 12px; text-align: right; }

.dashboard-board {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 420px;
}

.company-card {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr) 230px;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  border-radius: var(--rp-radius-lg);
  background:
    linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(246, 249, 254, 0.98)),
    #fff;
  border: 1px solid var(--rp-border-strong);
  box-shadow: 0 14px 34px rgba(37, 99, 235, 0.1);
}

.company-logo {
  width: 82px;
  height: 82px;
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: var(--rp-radius-md);
  background: linear-gradient(135deg, #1d4ed8, #60a5fa);
  color: #fff;
  font-size: 30px;
  font-weight: 800;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12);
}

.company-logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.company-main {
  min-width: 0;
}

.company-title-line {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.company-name {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.company-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 8px;
  color: #475467;
  font-size: 13px;
}

.company-description {
  max-width: 760px;
  margin-top: 10px;
  color: #344054;
  line-height: 1.6;
}

.company-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  justify-content: flex-end;
}

.audit-card {
  padding: 14px;
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.76);
}

.audit-card span,
.audit-card small {
  display: block;
  color: #64748b;
  font-size: 12px;
}

.audit-card strong {
  display: block;
  margin: 6px 0;
  color: var(--rp-primary);
  font-size: 18px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(120px, 1fr));
  gap: 12px;
}

.metric-tile {
  min-height: 96px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--rp-border);
  background: #fff;
  box-shadow: 0 8px 22px rgba(37, 99, 235, 0.05);
}

.metric-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  font-size: 20px;
}

.metric-value {
  font-size: 26px;
  font-weight: 750;
  color: #111827;
}

.metric-label {
  margin-top: 4px;
  color: #667085;
  font-size: 13px;
}

.is-blue .metric-icon {
  color: #1d4ed8;
  background: #dbeafe;
}

.is-cyan .metric-icon {
  color: #0369a1;
  background: #e0f2fe;
}

.is-amber .metric-icon {
  color: #b45309;
  background: #fef3c7;
}

.is-indigo .metric-icon {
  color: #4338ca;
  background: #e0e7ff;
}

.is-gray .metric-icon {
  color: #475467;
  background: #f2f4f7;
}

.split {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 16px;
}

.activity,
.quick-panel {
  min-width: 0;
}

.panel-card {
  padding: 16px;
  border: 1px solid var(--rp-border);
  border-radius: 8px;
  background: #fff;
}

.section-title {
  margin-bottom: 10px;
  font-weight: 700;
}

.quick-panel {
  display: flex;
  flex-direction: column;
}

.quick-button {
  justify-content: flex-start;
  margin-left: 0;
  margin-bottom: 10px;
  border-color: var(--rp-border);
}

@media (max-width: 980px) {
  .metric-grid,
  .split {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .dashboard-intro { align-items: flex-start; flex-direction: column; }
  .dashboard-intro small { text-align: left; }
  .metric-grid,
  .split,
  .company-card {
    grid-template-columns: 1fr;
  }

  .company-actions {
    justify-content: flex-start;
  }
}
</style>
