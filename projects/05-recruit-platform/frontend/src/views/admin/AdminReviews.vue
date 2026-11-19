<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  approveCompany,
  rejectCompany,
  approveJob,
  rejectJob,
  listPendingCompanies,
  listPendingJobs,
} from '@/api/admin'
import { previewFile } from '@/api/files'
import ModuleCard from '@/components/ModuleCard.vue'
import type { Company, Job } from '@/types/api'
import { OfficeBuilding, User, Phone, Histogram, Collection, Money, Reading, School, Edit } from '@element-plus/icons-vue'

const loading = ref(false)
const companies = ref<Company[]>([])
const jobs = ref<Job[]>([])

const logoUrlMap = ref<Record<number, string>>({})
const logoLoadingSet = ref<Set<number>>(new Set())

async function loadLogo(row: Company | Job) {
  const logoId = (row as Company).logoFileId ?? (row as Job).logoFileId
  if (!logoId || logoUrlMap.value[logoId] || logoLoadingSet.value.has(logoId)) return
  logoLoadingSet.value.add(logoId)
  try {
    const blob = await previewFile(logoId)
    if (blob.type.startsWith('image/')) {
      logoUrlMap.value[logoId] = URL.createObjectURL(blob)
    }
  } catch {
  } finally {
    logoLoadingSet.value.delete(logoId)
  }
}

function companyInitial(row: Company) {
  return (row.companyName || '企').charAt(0) || '企'
}

function formatDate(value?: string) {
  if (!value) return '—'
  return value.length >= 10 ? value.slice(0, 10) : value
}

function reviewLabel(row: Company) {
  return row.reviewType === 'INFO_EDIT' ? '信息修改' : '入驻申请'
}

async function load() {
  loading.value = true
  try {
    const [companyRows, jobRows] = await Promise.all([listPendingCompanies(), listPendingJobs()])
    companies.value = companyRows || []
    jobs.value = jobRows || []
    companies.value.forEach(loadLogo)
    jobs.value.forEach(loadLogo)
  } finally {
    loading.value = false
  }
}

async function handleApproveCompany(row: Company) {
  if (!row.id) return
  try {
    await ElMessageBox.confirm(
      `确定要通过「${row.companyName}」的${reviewLabel(row)}吗？`,
      '通过确认',
      { type: 'info', confirmButtonText: '通过', cancelButtonText: '取消' },
    )
  } catch { return }
  await approveCompany(row.id)
  ElMessage.success('已通过')
  load()
}

async function handleRejectCompany(row: Company) {
  if (!row.id) return
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入驳回「${row.companyName}」${reviewLabel(row)}的原因：`,
      '驳回确认',
      {
        confirmButtonText: '驳回',
        cancelButtonText: '取消',
        inputType: 'textarea',
        inputValidator: (v: string) => (v ? true : '驳回原因不能为空'),
        inputErrorMessage: '驳回原因不能为空',
      },
    )
    await rejectCompany(row.id, value)
    ElMessage.success('已驳回')
    load()
  } catch {}
}

async function handleApproveJob(row: Job) {
  if (!row.id) return
  try {
    await ElMessageBox.confirm(`确定要通过岗位「${row.jobName}」并发布吗？`, '通过确认', { type: 'info', confirmButtonText: '通过并发布', cancelButtonText: '取消' })
  } catch { return }
  await approveJob(row.id)
  ElMessage.success('已发布')
  load()
}

async function handleRejectJob(row: Job) {
  if (!row.id) return
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入驳回岗位「${row.jobName}」的原因：`, '驳回确认',
      { confirmButtonText: '驳回', cancelButtonText: '取消', inputType: 'textarea', inputValidator: (v: string) => (v ? true : '驳回原因不能为空'), inputErrorMessage: '驳回原因不能为空' },
    )
    await rejectJob(row.id, value)
    ElMessage.success('已驳回')
    load()
  } catch {}
}

const hasCompanies = computed(() => companies.value.length > 0)

onMounted(load)
onUnmounted(() => { Object.values(logoUrlMap.value).forEach((url) => URL.revokeObjectURL(url)) })
</script>

<template>
  <ModuleCard title="审核中心" subtitle="审核企业资料和职位发布">
    <template #actions>
      <el-button type="primary" @click="load">刷新</el-button>
    </template>

    <el-tabs>
      <el-tab-pane label="企业审核">
        <div v-loading="loading" class="company-list">
          <el-empty v-if="!loading && !hasCompanies" description="暂无待审核企业" />
          <div v-for="row in companies" :key="(row.reviewType || 'new') + '-' + row.id" class="company-card">
            <div v-if="row.reviewType" class="company-card__badge">
              <el-tag :type="row.reviewType === 'INFO_EDIT' ? 'info' : 'warning'" size="large" effect="dark">
                <el-icon style="margin-right:4px"><Edit /></el-icon>
                {{ row.reviewType === 'INFO_EDIT' ? '企业信息修改' : '新企业入驻' }}
              </el-tag>
            </div>
            <div class="company-card__logo">
              <img v-if="row.logoFileId && logoUrlMap[row.logoFileId]" :src="logoUrlMap[row.logoFileId]" :alt="row.companyName" />
              <div v-else class="company-card__logo-placeholder">{{ companyInitial(row) }}</div>
            </div>
            <div class="company-card__body">
              <div class="company-card__header">
                <span class="company-card__name">{{ row.companyName || '未填写企业名称' }}</span>
                <span class="company-card__time">提交于 {{ formatDate(row.createdAt) }}</span>
              </div>
              <div class="company-card__meta">
                <span class="meta-item"><el-icon><OfficeBuilding /></el-icon><span class="meta-label">行业</span>{{ row.industry || '未填写' }}</span>
                <span class="meta-item"><el-icon><Histogram /></el-icon><span class="meta-label">规模</span>{{ row.companySize || '未填写' }}</span>
                <span class="meta-item"><el-icon><User /></el-icon><span class="meta-label">联系人</span>{{ row.contactName || '未填写' }}</span>
                <span class="meta-item"><el-icon><Phone /></el-icon><span class="meta-label">电话</span>{{ row.contactPhone || '未填写' }}</span>
              </div>
              <div class="company-card__desc-label">企业简介</div>
              <div class="company-card__desc">{{ row.description || '（企业尚未填写简介）' }}</div>
              <div v-if="row.reviewType === 'INFO_EDIT'" class="company-card__diff">
                <div class="diff-title">📌 与原信息对比</div>
                <div class="diff-grid">
                  <div class="diff-col diff-col--old">
                    <span class="diff-col__label">原信息</span>
                    <div class="diff-row"><strong>名称:</strong>{{ row.oldCompanyName || '—' }}</div>
                    <div class="diff-row"><strong>行业:</strong>{{ row.oldIndustry || '—' }}</div>
                    <div class="diff-row"><strong>规模:</strong>{{ row.oldCompanySize || '—' }}</div>
                    <div class="diff-row"><strong>联系人:</strong>{{ row.oldContactName || '—' }}</div>
                    <div class="diff-row"><strong>电话:</strong>{{ row.oldContactPhone || '—' }}</div>
                    <div class="diff-row"><strong>简介:</strong>{{ (row.oldDescription || '').substring(0, 50) || '（无）' }}</div>
                  </div>
                  <div class="diff-col diff-col--new">
                    <span class="diff-col__label">新信息</span>
                    <div class="diff-row"><strong>名称:</strong>{{ row.companyName || '—' }}</div>
                    <div class="diff-row"><strong>行业:</strong>{{ row.industry || '—' }}</div>
                    <div class="diff-row"><strong>规模:</strong>{{ row.companySize || '—' }}</div>
                    <div class="diff-row"><strong>联系人:</strong>{{ row.contactName || '—' }}</div>
                    <div class="diff-row"><strong>电话:</strong>{{ row.contactPhone || '—' }}</div>
                    <div class="diff-row"><strong>简介:</strong>{{ (row.description || '').substring(0, 50) || '（无）' }}</div>
                  </div>
                </div>
              </div>
              <div class="company-card__actions">
                <el-button type="danger" plain @click="handleRejectCompany(row)">驳回</el-button>
                <el-button type="success" @click="handleApproveCompany(row)">通过</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="职位审核">
        <div v-loading="loading" class="job-list">
          <el-empty v-if="!loading && jobs.length === 0" description="暂无待审核岗位" />
          <div v-for="row in jobs" :key="row.id" class="job-card">
            <div class="company-card__logo">
              <img v-if="row.logoFileId && logoUrlMap[row.logoFileId]" :src="logoUrlMap[row.logoFileId]" :alt="row.companyName" />
              <div v-else class="company-card__logo-placeholder">{{ (row.companyName || '企').charAt(0) || '企' }}</div>
            </div>
            <div class="job-card__body">
              <div class="job-card__header">
                <span class="job-card__name">{{ row.jobName || '未填写职位名称' }}</span>
                <span class="job-card__city">{{ row.city || '' }}</span>
                <span class="job-card__time">提交于 {{ formatDate(row.createdAt) }}</span>
              </div>
              <div class="job-card__meta">
                <span class="meta-item" v-if="row.jobType"><el-icon><Collection /></el-icon>{{ row.jobType }}</span>
                <span class="meta-item" v-if="row.salaryRange"><el-icon><Money /></el-icon>{{ row.salaryRange }}</span>
                <span class="meta-item" v-if="row.educationRequirement"><el-icon><Reading /></el-icon>{{ row.educationRequirement }}</span>
                <span class="meta-item" v-if="row.majorRequirement"><el-icon><School /></el-icon>{{ row.majorRequirement }}</span>
              </div>
              <div class="job-card__company-bar" v-if="row.companyName">
                <el-icon><OfficeBuilding /></el-icon>{{ row.companyName }}<span v-if="row.industry"> · {{ row.industry }}</span><span v-if="row.companySize"> · {{ row.companySize }}</span>
              </div>
              <div v-if="row.skillRequirement" class="job-card__section"><span class="section-label">💡 技能要求</span><div class="job-card__desc">{{ row.skillRequirement }}</div></div>
              <div v-if="row.description" class="job-card__section"><span class="section-label">📝 岗位描述</span><div class="job-card__desc">{{ row.description }}</div></div>
              <div class="job-card__actions">
                <el-button type="danger" plain @click="handleRejectJob(row)">驳回</el-button>
                <el-button type="success" @click="handleApproveJob(row)">通过并发布</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </ModuleCard>
</template>

<style scoped>
.company-list{display:flex;flex-direction:column;gap:16px;padding:4px 0;min-height:200px}
.company-card{position:relative;display:flex;gap:20px;padding:24px 20px 20px;background:#fff;border:1px solid #e5e7eb;border-radius:10px;box-shadow:0 2px 6px rgba(15,23,42,.04);transition:box-shadow .2s,border-color .2s}
.company-card:hover{border-color:#d1d5db;box-shadow:0 4px 14px rgba(15,23,42,.08)}
.company-card__badge{position:absolute;top:-12px;left:16px;z-index:2}
.company-card__logo{flex:0 0 80px;width:80px;height:80px;border-radius:10px;overflow:hidden;background:#f3f4f6;display:flex;align-items:center;justify-content:center}
.company-card__logo img{width:100%;height:100%;object-fit:cover}
.company-card__logo-placeholder{font-size:28px;font-weight:600;color:#6b7280;background:linear-gradient(135deg,#e0e7ff 0%,#f3f4f6 100%);width:100%;height:100%;display:flex;align-items:center;justify-content:center}
.company-card__body{flex:1;min-width:0;display:flex;flex-direction:column;gap:10px}
.company-card__header{display:flex;align-items:center;gap:10px}
.company-card__name{font-size:16px;font-weight:600;color:#111827}
.company-card__time{margin-left:auto;font-size:12px;color:#9ca3af}
.company-card__meta{display:flex;flex-wrap:wrap;gap:18px;font-size:13px;color:#4b5563}
.meta-item{display:inline-flex;align-items:center;gap:6px}
.meta-item :deep(.el-icon){color:#6b7280}
.meta-label{color:#9ca3af;font-size:11px}
.company-card__desc-label{font-size:12px;color:#6b7280;margin-top:4px}
.company-card__desc{font-size:13px;color:#374151;line-height:1.6;background:#f9fafb;border-radius:6px;padding:10px 12px;max-height:120px;overflow-y:auto;word-break:break-word}
.company-card__actions{display:flex;justify-content:flex-end;gap:10px;margin-top:6px}
.company-card__diff{margin-top:6px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden}
.diff-title{background:#f0f9ff;padding:8px 12px;font-size:13px;font-weight:600;color:#1e40af;border-bottom:1px solid #e5e7eb}
.diff-grid{display:grid;grid-template-columns:1fr 1fr;gap:0}
.diff-col{padding:10px 12px;font-size:12px;line-height:1.8}
.diff-col--old{background:#fef2f2;border-right:1px dashed #fca5a5}
.diff-col--new{background:#f0fdf4}
.diff-col__label{display:block;font-weight:700;font-size:12px;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #e5e7eb}
.diff-col--old .diff-col__label{color:#b91c1c}
.diff-col--new .diff-col__label{color:#15803d}
.diff-row{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.diff-row strong{color:#6b7280;font-weight:500}

.job-list{display:flex;flex-direction:column;gap:16px;padding:4px 0;min-height:200px}
.job-card{display:flex;gap:20px;padding:20px;background:#fff;border:1px solid #e5e7eb;border-radius:10px;box-shadow:0 2px 6px rgba(15,23,42,.04);transition:box-shadow .2s,border-color .2s}
.job-card:hover{border-color:#d1d5db;box-shadow:0 4px 14px rgba(15,23,42,.08)}
.job-card__body{flex:1;min-width:0;display:flex;flex-direction:column;gap:12px}
.job-card__header{display:flex;align-items:baseline;gap:10px}
.job-card__name{font-size:16px;font-weight:600;color:#111827}
.job-card__city{font-size:13px;color:#6b7280}
.job-card__city::before{content:'·';margin-right:6px;color:#d1d5db}
.job-card__time{margin-left:auto;font-size:12px;color:#9ca3af}
.job-card__meta{display:flex;flex-wrap:wrap;gap:18px;font-size:13px;color:#4b5563}
.job-card__company-bar{display:flex;align-items:center;gap:6px;font-size:13px;color:#4b5563;background:linear-gradient(135deg,#f0f9ff 0%,#f8fafc 100%);border-left:3px solid #60a5fa;padding:8px 12px;border-radius:4px}
.job-card__company-bar :deep(.el-icon){color:#3b82f6}
.job-card__section{display:flex;flex-direction:column;gap:6px}
.section-label{font-size:12px;color:#6b7280}
.job-card__desc{font-size:13px;color:#374151;line-height:1.6;background:#f9fafb;border-radius:6px;padding:10px 12px;display:-webkit-box;-webkit-line-clamp:4;line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;word-break:break-word;white-space:pre-wrap}
.job-card__actions{display:flex;justify-content:flex-end;gap:10px;margin-top:4px}
</style>