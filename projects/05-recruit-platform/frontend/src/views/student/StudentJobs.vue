<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

import { createApplication } from '@/api/applications'
import { listPublishedJobs } from '@/api/jobs'
import { getMyProfile, listResumesByStudent } from '@/api/student'
import ModuleCard from '@/components/ModuleCard.vue'
import { useAuthStore } from '@/stores/auth'
import type { Job, Resume, StudentProfile } from '@/types/api'
import JobDetailPanel from './components/JobDetailPanel.vue'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)
const applying = ref(false)
const jobs = ref<Job[]>([])
const resumes = ref<Resume[]>([])
const profile = ref<StudentProfile | null>(null)
const keyword = ref('')
const city = ref('')
const jobType = ref('')
const selectedJobId = ref<number>()
const applyJob = ref<Job | null>(null)
const selectedResumeId = ref<number>()
const applyDialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const isMobile = ref(false)
let mobileMedia: MediaQueryList | undefined
let loadSequence = 0

const cityOptions = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京', '西安']
const typeOptions = ['技术', '产品', '运营', '设计', '市场', '职能', '金融', '其他']

const selectedJob = computed(() => {
  return jobs.value.find((job) => job.id === selectedJobId.value) || null
})

function syncViewport(event?: MediaQueryListEvent) {
  isMobile.value = event?.matches ?? mobileMedia?.matches ?? false
  if (!isMobile.value) {
    detailDrawerVisible.value = false
  }
}

function selectJob(job: Job) {
  selectedJobId.value = job.id
  if (isMobile.value) {
    detailDrawerVisible.value = true
  }
}

async function load() {
  const requestId = ++loadSequence
  loading.value = true
  try {
    const page = await listPublishedJobs({
      current: 1,
      size: 12,
      keyword: keyword.value || undefined,
      city: city.value || undefined,
      jobType: jobType.value || undefined,
    })
    if (requestId !== loadSequence) return
    const records = page.records || []
    const previousSelectionExists = records.some((job) => job.id === selectedJobId.value)
    jobs.value = records
    selectedJobId.value = previousSelectionExists ? selectedJobId.value : records[0]?.id
    if (!records.length) {
      detailDrawerVisible.value = false
    }
  } catch {
    if (requestId !== loadSequence) return
    jobs.value = []
    selectedJobId.value = undefined
    detailDrawerVisible.value = false
  } finally {
    if (requestId === loadSequence) {
      loading.value = false
    }
  }
}

async function loadStudentContext() {
  if (!auth.userId) return
  const [profileRow, resumeRows] = await Promise.all([
    getMyProfile(),
    listResumesByStudent(auth.userId),
  ])
  profile.value = profileRow
  resumes.value = resumeRows || []
}

async function openApply(job: Job) {
  if (!auth.userId) return
  await loadStudentContext()
  if (!profile.value?.id) {
    ElMessage.warning('请先完善个人信息后再投递')
    router.push('/student/profile')
    return
  }
  if (!resumes.value.length) {
    ElMessage.warning('请先创建或上传一份简历')
    router.push('/student/resumes')
    return
  }
  applyJob.value = job
  selectedResumeId.value = resumes.value[0]?.id
  detailDrawerVisible.value = false
  applyDialogVisible.value = true
}

async function submitApplication() {
  if (!applyJob.value?.id || !selectedResumeId.value) {
    ElMessage.warning('请选择投递简历')
    return
  }
  applying.value = true
  try {
    await createApplication({
      jobId: applyJob.value.id,
      resumeId: selectedResumeId.value,
    })
    ElMessage.success('投递成功，可在我的投递中查看进度')
    applyDialogVisible.value = false
  } finally {
    applying.value = false
  }
}

onMounted(async () => {
  mobileMedia = window.matchMedia('(max-width: 899px)')
  syncViewport()
  mobileMedia.addEventListener('change', syncViewport)
  await Promise.all([load(), loadStudentContext()])
})

onBeforeUnmount(() => {
  mobileMedia?.removeEventListener('change', syncViewport)
})
</script>

<template>
  <ModuleCard title="职位大厅" subtitle="浏览招聘详情，发现适合你的校招机会">
    <template #actions>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </template>

    <div class="search-panel">
      <div class="search-row">
        <el-select v-model="jobType" clearable placeholder="全部职位" class="type-select" @change="load">
          <el-option v-for="type in typeOptions" :key="type" :label="type" :value="type" />
        </el-select>
        <el-input
          v-model="keyword"
          clearable
          placeholder="搜索职位名称、关键词"
          class="keyword-input"
          @keyup.enter="load"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="load">搜索</el-button>
      </div>

      <div class="filter-line">
        <span>工作地点：</span>
        <button type="button" :class="{ active: !city }" @click="city = ''; load()">全部</button>
        <button
          v-for="item in cityOptions"
          :key="item"
          type="button"
          :class="{ active: city === item }"
          @click="city = item; load()"
        >
          {{ item }}
        </button>
      </div>
      <div class="filter-line">
        <span>职位类别：</span>
        <button type="button" :class="{ active: !jobType }" @click="jobType = ''; load()">全部</button>
        <button
          v-for="item in typeOptions.slice(0, 7)"
          :key="item"
          type="button"
          :class="{ active: jobType === item }"
          @click="jobType = item; load()"
        >
          {{ item }}
        </button>
      </div>
    </div>

    <div class="job-result-summary">
      <strong>{{ jobs.length }}</strong>
      <span>个与当前筛选条件匹配的岗位</span>
      <small v-if="jobs.length">选择左侧岗位查看完整招聘信息</small>
    </div>

    <div class="job-browser">
      <section v-loading="loading" class="job-list job-list-column" aria-label="岗位列表">
        <el-empty v-if="!jobs.length && !loading" description="暂无匹配职位，请调整筛选条件" />
        <button
          v-for="job in jobs"
          v-else
          :key="job.id"
          type="button"
          class="job-card"
          :class="{ selected: selectedJobId === job.id }"
          :aria-pressed="selectedJobId === job.id"
          @click="selectJob(job)"
        >
          <span class="company-avatar" aria-hidden="true">
            {{ (job.companyName || job.jobName)?.charAt(0) || '职' }}
          </span>
          <span class="job-body">
            <span class="job-title-line">
              <strong>{{ job.jobName || '未命名职位' }}</strong>
              <b>{{ job.salaryRange || '薪资面议' }}</b>
            </span>
            <span class="job-company">{{ job.companyName || '优质企业' }}</span>
            <span class="job-meta">
              {{ job.city || '城市不限' }} · {{ job.educationRequirement || '学历不限' }} ·
              {{ job.jobType || '类别不限' }}
            </span>
            <span class="tag-row">
              <el-tag v-if="job.majorRequirement" size="small" effect="plain">{{ job.majorRequirement }}</el-tag>
              <el-tag v-if="job.skillRequirement" size="small" effect="plain" class="skill-summary">
                {{ job.skillRequirement }}
              </el-tag>
            </span>
          </span>
        </button>
      </section>

      <aside class="job-detail-column" aria-label="岗位详情">
        <JobDetailPanel :job="selectedJob" @apply="openApply" />
      </aside>
    </div>

    <el-drawer
      v-model="detailDrawerVisible"
      title="岗位详情"
      direction="rtl"
      size="92%"
      class="job-detail-drawer"
    >
      <JobDetailPanel :job="selectedJob" @apply="openApply" />
    </el-drawer>

    <el-dialog v-model="applyDialogVisible" title="选择简历投递" width="520px">
      <div v-if="applyJob" class="apply-summary">
        <strong>{{ applyJob.jobName }}</strong>
        <span>
          {{ applyJob.companyName || '优质企业' }} · {{ applyJob.city || '城市不限' }} ·
          {{ applyJob.salaryRange || '薪资面议' }}
        </span>
      </div>
      <el-form label-width="82px">
        <el-form-item label="投递简历" required>
          <el-select v-model="selectedResumeId" placeholder="请选择简历" class="resume-select">
            <el-option
              v-for="resume in resumes"
              :key="resume.id"
              :label="resume.resumeName || `简历 ${resume.id}`"
              :value="resume.id!"
            >
              <div class="resume-option">
                <span>{{ resume.resumeName || `简历 ${resume.id}` }}</span>
                <small>{{ resume.targetPosition || resume.skillTags || '未填写目标岗位' }}</small>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="applying" @click="submitApplication">确认投递</el-button>
      </template>
    </el-dialog>
  </ModuleCard>
</template>

<style scoped>
.search-panel,
.job-card {
  border: 1px solid var(--rp-border);
  border-radius: var(--rp-radius-sm);
  background: #fff;
}

.search-panel {
  padding: 16px;
}

.search-row {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}

.type-select {
  width: 140px;
}

.keyword-input {
  flex: 1;
}

.filter-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 10px;
  color: #516579;
  font-size: 13px;
}

.filter-line span {
  color: #334155;
  font-weight: 650;
}

.filter-line button {
  padding: 4px 9px;
  border: 0;
  border-radius: 999px;
  color: #516579;
  background: transparent;
  cursor: pointer;
}

.filter-line button.active,
.filter-line button:hover {
  color: var(--rp-primary);
  background: var(--rp-primary-soft);
}

.job-result-summary {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 18px 2px 10px;
  color: var(--rp-muted);
  font-size: 13px;
}

.job-result-summary strong {
  color: var(--rp-navy);
  font-size: 21px;
  font-variant-numeric: tabular-nums;
}

.job-result-summary small {
  margin-left: auto;
  color: #8a98aa;
}

.job-browser {
  display: grid;
  grid-template-columns: minmax(300px, 360px) minmax(0, 1fr);
  align-items: start;
  gap: 16px;
}

.job-list-column,
.job-detail-column {
  min-width: 0;
}

.job-list {
  display: flex;
  height: clamp(520px, calc(100vh - 330px), 680px);
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
  overflow-y: auto;
}

.job-detail-column {
  position: sticky;
  top: 16px;
}

.job-card {
  display: grid;
  width: 100%;
  grid-template-columns: 46px minmax(0, 1fr);
  align-items: start;
  gap: 12px;
  padding: 14px;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.job-card:hover {
  border-color: var(--rp-border-strong);
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.08);
}

.job-card.selected {
  border-color: var(--rp-primary);
  background: #f5f8ff;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
}

.company-avatar {
  display: grid;
  width: 46px;
  height: 46px;
  place-items: center;
  border-radius: 10px;
  color: #fff;
  background: var(--rp-primary);
  font-size: 18px;
  font-weight: 800;
}

.job-body,
.job-title-line,
.job-company,
.job-meta,
.tag-row {
  display: flex;
}

.job-body {
  min-width: 0;
  flex-direction: column;
}

.job-title-line {
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.job-title-line > strong {
  overflow: hidden;
  color: var(--rp-navy-strong);
  font-size: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.job-title-line b {
  flex: 0 0 auto;
  color: #f97316;
  font-size: 15px;
}

.job-company {
  margin-top: 7px;
  color: #3c506e;
  font-size: 13px;
  font-weight: 650;
}

.job-meta {
  margin-top: 6px;
  color: var(--rp-muted);
  font-size: 12px;
}

.tag-row {
  gap: 6px;
  margin-top: 10px;
  overflow: hidden;
}

.skill-summary {
  min-width: 0;
  max-width: 170px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.apply-summary {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  margin-bottom: 16px;
  border: 1px solid var(--rp-border);
  border-radius: 8px;
  background: #f7fbff;
}

.apply-summary strong {
  color: #0f1f35;
}

.apply-summary span,
.resume-option small {
  color: var(--rp-muted);
  font-size: 13px;
}

.resume-select {
  width: 100%;
}

.resume-option {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

:global(.job-detail-drawer .el-drawer__body) {
  padding: 12px;
  background: var(--rp-bg);
}

:global(.job-detail-drawer .el-drawer__header) {
  padding: 16px 18px;
  margin-bottom: 0;
  border-bottom: 1px solid var(--rp-border);
  color: var(--rp-navy-strong);
  font-weight: 750;
}

@media (max-width: 1180px) {
  .job-browser {
    grid-template-columns: minmax(280px, 330px) minmax(0, 1fr);
  }
}

@media (max-width: 899px) {
  .job-browser {
    grid-template-columns: 1fr;
  }

  .job-detail-column {
    display: none;
  }

  .job-list {
    height: auto;
    max-height: none;
    overflow: visible;
  }
}

@media (max-width: 640px) {
  .search-row {
    flex-direction: column;
  }

  .type-select,
  .search-row .el-button {
    width: 100%;
  }

  .job-result-summary small {
    display: none;
  }

  .job-card {
    grid-template-columns: 40px minmax(0, 1fr);
    padding: 12px;
  }

  .company-avatar {
    width: 40px;
    height: 40px;
  }
}
</style>
