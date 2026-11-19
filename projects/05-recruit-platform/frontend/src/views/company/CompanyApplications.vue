<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { listCompanyApplicationDetails, updateApplicationStatus } from '@/api/applications'
import { previewFile } from '@/api/files'
import { getMyCompany, getStudentDetail } from '@/api/company'
import ModuleCard from '@/components/ModuleCard.vue'
import { useAuthStore } from '@/stores/auth'
import type { Company, CompanyApplicationDetail, StudentDetailResponse, StudentExperience, StudentProfile, StudentSkill } from '@/types/api'

const auth = useAuthStore()
const loading = ref(false)
const processing = ref(false)
const company = ref<Company | null>(null)
const applications = ref<CompanyApplicationDetail[]>([])
const keyword = ref('')
const statusFilter = ref('PENDING')
const jobFilter = ref('')
const drawerVisible = ref(false)
const selected = ref<CompanyApplicationDetail | null>(null)
const remark = ref('')
const selectedIds = ref<number[]>([])
const PAGE_SIZE = 8
const pageByGroup = ref<Record<string, number>>({})
const expandedGroups = ref<Record<string, boolean>>({})

const previewVisible = ref(false)
const previewUrl = ref('')
const previewLoading = ref(false)
const previewError = ref('')
const previewName = ref('简历预览')

const detailVisible = ref(false)
const detailLoading = ref(false)
const detailStudent = ref<StudentProfile | null>(null)
const detailSkills = ref<StudentSkill[]>([])
const detailExperiences = ref<StudentExperience[]>([])
const detailRow = ref<CompanyApplicationDetail | null>(null)

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

const genderText: Record<string, string> = {
  MALE: '男',
  FEMALE: '女',
}

const jobOptions = computed(() => {
  const names = [...new Set(applications.value.map((a) => a.jobName).filter(Boolean))]
  return names.map((n) => ({ label: n, value: n }))
})

type ApplicationGroup = {
  groupKey: string
  jobName: string
  items: CompanyApplicationDetail[]
}

const filterSignature = computed(() => `${jobFilter.value}|${statusFilter.value}|${keyword.value.trim().toLowerCase()}`)

const grouped = computed<ApplicationGroup[]>(() => {
  const filtered = applications.value.filter((item) => {
    const text = `${item.studentName || ''}${item.school || ''}${item.major || ''}${item.jobName || ''}`
    const matchKeyword = !keyword.value || text.toLowerCase().includes(keyword.value.toLowerCase())
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    const matchJob = !jobFilter.value || item.jobName === jobFilter.value
    return matchKeyword && matchStatus && matchJob
  })

  const map = new Map<string, ApplicationGroup>()
  for (const item of filtered) {
    const groupKey = String(item.jobId ?? `job:${item.jobName || '未命名岗位'}`)
    const group = map.get(groupKey)
    if (group) group.items.push(item)
    else {
      map.set(groupKey, {
        groupKey,
        jobName: item.jobName || '未命名岗位',
        items: [item],
      })
    }
  }
  return [...map.values()]
})

function resetPageState() {
  pageByGroup.value = {}
}

function isGroupExpanded(groupKey: string) {
  return expandedGroups.value[groupKey] !== false
}

function toggleGroup(groupKey: string) {
  expandedGroups.value = {
    ...expandedGroups.value,
    [groupKey]: !isGroupExpanded(groupKey),
  }
}

watch(filterSignature, resetPageState)

function pageFor(groupKey: string, total: number) {
  const maxPage = Math.max(1, Math.ceil(total / PAGE_SIZE))
  return Math.min(pageByGroup.value[groupKey] || 1, maxPage)
}

function visibleItems(group: ApplicationGroup) {
  const page = pageFor(group.groupKey, group.items.length)
  const start = (page - 1) * PAGE_SIZE
  return group.items.slice(start, start + PAGE_SIZE)
}

function updatePage(groupKey: string, page: number) {
  pageByGroup.value = { ...pageByGroup.value, [groupKey]: page }
}

function rangeStart(group: ApplicationGroup) {
  return (pageFor(group.groupKey, group.items.length) - 1) * PAGE_SIZE + 1
}

function rangeEnd(group: ApplicationGroup) {
  return Math.min(pageFor(group.groupKey, group.items.length) * PAGE_SIZE, group.items.length)
}

function formatApplicationTime(value?: string) {
  return value ? value.replace('T', ' ').substring(0, 16) : '-'
}

function initials(name?: string) {
  return (name || '候').trim().slice(0, 1)
}

function proficiencyTag(p?: string) {
  const map: Record<string, string> = { '精通': 'danger', '掌握': 'success', '熟悉': '', '了解': 'info' }
  return map[p || ''] || 'info'
}

function experienceLabel(t?: string) {
  const map: Record<string, string> = { PROJECT: '项目', INTERNSHIP: '实习', COMPETITION_HONOR: '竞赛/荣誉' }
  return map[t || ''] || t || '-'
}

function countByStatus(items: CompanyApplicationDetail[], status: string) {
  return items.filter((item) => item.status === status).length
}

function isSelected(id?: number) {
  return Boolean(id && selectedIds.value.includes(id))
}

function isJobSelected(items: CompanyApplicationDetail[]) {
  const ids = items.map((item) => item.id).filter((id): id is number => Boolean(id))
  return ids.length > 0 && ids.every((id) => selectedIds.value.includes(id))
}

function toggleSelection(row: CompanyApplicationDetail, checked: boolean) {
  if (!row.id) return
  const next = new Set(selectedIds.value)
  if (checked) next.add(row.id)
  else next.delete(row.id)
  selectedIds.value = [...next]
}

function toggleJobSelection(items: CompanyApplicationDetail[], checked: boolean) {
  const next = new Set(selectedIds.value)
  for (const item of items) {
    if (!item.id) continue
    if (checked) next.add(item.id)
    else next.delete(item.id)
  }
  selectedIds.value = [...next]
}

function openDetail(row: CompanyApplicationDetail) {
  selected.value = row
  remark.value = row.remark || ''
  drawerVisible.value = true
}

function openProcessing(row: CompanyApplicationDetail) {
  selected.value = row
  remark.value = row.remark || ''
  drawerVisible.value = true
}

async function load() {
  if (!auth.userId) return
  loading.value = true
  try {
    company.value = await getMyCompany(auth.userId)
    applications.value = company.value?.id ? await listCompanyApplicationDetails(company.value.id) : []
    selectedIds.value = selectedIds.value.filter((id) => applications.value.some((item) => item.id === id))
    resetPageState()
    expandedGroups.value = {}
  } finally {
    loading.value = false
  }
}

async function handleStatus(status: 'PASSED' | 'REJECTED') {
  if (!selected.value?.id) return
  processing.value = true
  try {
    await updateApplicationStatus(selected.value.id, status, remark.value)
    ElMessage.success(status === 'PASSED' ? '已通过该投递' : '已拒绝该投递')
    drawerVisible.value = false
    await load()
  } finally {
    processing.value = false
  }
}

async function batchUpdateStatus(status: 'PASSED' | 'REJECTED') {
  if (!selectedIds.value.length) {
    ElMessage.warning('请先勾选投递记录')
    return
  }
  const label = status === 'PASSED' ? '通过' : '拒绝'
  try {
    await ElMessageBox.confirm(`确定要批量${label} ${selectedIds.value.length} 条投递吗？`, `批量${label}`, {
      type: 'warning',
    })
  } catch {
    return
  }
  processing.value = true
  try {
    for (const id of selectedIds.value) {
      await updateApplicationStatus(id, status)
    }
    ElMessage.success(`已批量${label} ${selectedIds.value.length} 条投递`)
    selectedIds.value = []
    await load()
  } finally {
    processing.value = false
  }
}

async function openCandidateDetail(row: CompanyApplicationDetail) {
  if (!row.studentId) {
    ElMessage.warning('无法获取候选人信息')
    return
  }
  detailRow.value = row
  detailVisible.value = true
  detailLoading.value = true
  detailStudent.value = null
  detailSkills.value = []
  detailExperiences.value = []
  try {
    const data: StudentDetailResponse = await getStudentDetail(row.studentId)
    detailStudent.value = data.profile || null
    detailSkills.value = data.skills || []
    detailExperiences.value = data.experiences || []
  } catch {
    ElMessage.error('获取候选人详情失败')
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

async function viewResume(row: CompanyApplicationDetail) {
  if (!row.resumeFileId) {
    ElMessage.warning('该简历无可预览文件')
    return
  }
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
  previewVisible.value = true
  previewLoading.value = true
  previewError.value = ''
  previewName.value = row.resumeName || '简历预览'
  try {
    const blob = await previewFile(row.resumeFileId)
    previewUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    previewError.value = error instanceof Error ? error.message : '获取简历文件失败'
  } finally {
    previewLoading.value = false
  }
}

function closePreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewVisible.value = false
  previewUrl.value = ''
  previewError.value = ''
}

onMounted(load)
</script>

<template>
  <ModuleCard title="投递管理" subtitle="按岗位分组处理学生投递">
    <div class="applications-filter-panel">
      <div class="applications-filter-row">
        <el-select v-model="jobFilter" clearable placeholder="全部岗位" class="filter-item">
          <el-option v-for="opt in jobOptions" :key="opt.value!" :label="opt.label" :value="opt.value!" />
        </el-select>
        <el-select v-model="statusFilter" clearable placeholder="全部状态" class="filter-item">
          <el-option v-for="(label, value) in statusText" :key="value" :label="label" :value="value" />
        </el-select>
        <el-input v-model="keyword" clearable placeholder="搜索学生、学校、专业" class="filter-search" />
        <el-button @click="load">刷新</el-button>
      </div>
      <div v-if="selectedIds.length" class="applications-bulk-bar">
        <div class="bulk-selection">
          <span class="bulk-selection-dot" />
          已选 <strong>{{ selectedIds.length }}</strong> 条投递
        </div>
        <div class="bulk-actions">
          <el-button type="success" :loading="processing" @click="batchUpdateStatus('PASSED')">批量通过</el-button>
          <el-button type="danger" :loading="processing" @click="batchUpdateStatus('REJECTED')">批量拒绝</el-button>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="application-job-list">
      <el-empty v-if="!grouped.length" description="暂无投递记录" />

      <article v-for="group in grouped" :key="group.groupKey" class="application-job-card liquid-glass">
        <header class="application-job-card__header">
          <div class="application-job-card__identity">
            <span class="application-job-card__eyebrow">招聘岗位</span>
            <h3 :title="group.jobName">{{ group.jobName }}</h3>
            <div class="application-job-card__meta">
              <span v-if="group.items[0]?.city">{{ group.items[0].city }}</span>
              <span v-if="group.items[0]?.jobType">{{ group.items[0].jobType }}</span>
              <span v-if="group.items[0]?.salaryRange">{{ group.items[0].salaryRange }}</span>
            </div>
          </div>
          <div class="application-job-card__header-actions">
            <div class="application-job-card__stats" aria-label="岗位投递统计">
              <div class="job-stat"><strong>{{ group.items.length }}</strong><span>全部投递</span></div>
              <div class="job-stat is-warning"><strong>{{ countByStatus(group.items, 'PENDING') }}</strong><span>待处理</span></div>
              <div class="job-stat is-success"><strong>{{ countByStatus(group.items, 'PASSED') }}</strong><span>已通过</span></div>
            </div>
            <button
              type="button"
              class="application-job-card__toggle"
              :aria-expanded="isGroupExpanded(group.groupKey)"
              :aria-label="`${isGroupExpanded(group.groupKey) ? '收起' : '展开'}${group.jobName}`"
              @click.stop="toggleGroup(group.groupKey)"
            >
              <span>{{ isGroupExpanded(group.groupKey) ? '收起' : '展开' }}</span>
              <ArrowDown class="application-job-card__chevron" :class="{ 'is-collapsed': isGroupExpanded(group.groupKey) }" aria-hidden="true" />
            </button>
          </div>
        </header>

        <div v-show="isGroupExpanded(group.groupKey)" class="application-job-card__body">
          <div class="application-job-card__toolbar">
          <label class="job-select-all">
            <el-checkbox
              :model-value="isJobSelected(group.items)"
              @change="toggleJobSelection(group.items, Boolean($event))"
            />
            <span>全选本岗位</span>
          </label>
          <span class="job-candidate-count">{{ group.items.length }} 位候选人</span>
          </div>

          <div class="candidate-card-grid">
          <article
            v-for="row in visibleItems(group)"
            :key="row.id"
            class="candidate-card liquid-glass"
            :class="{ 'is-selected': isSelected(row.id) }"
          >
            <div class="candidate-card__topline">
              <el-checkbox
                :model-value="isSelected(row.id)"
                :aria-label="`选择${row.studentName || '候选人'}`"
                @change="toggleSelection(row, Boolean($event))"
              />
              <el-tag :type="statusType[row.status || ''] || 'info'" effect="light" size="small">
                {{ statusText[row.status || ''] || row.status || '未知状态' }}
              </el-tag>
            </div>

            <div class="candidate-card__identity">
              <div class="candidate-avatar" aria-hidden="true">{{ initials(row.studentName) }}</div>
              <div class="candidate-name-block">
                <h4 :title="row.studentName || '未填写姓名'">{{ row.studentName || '未填写姓名' }}</h4>
                <p :title="row.school || '学校未填写'">{{ row.school || '学校未填写' }}</p>
              </div>
            </div>

            <div class="candidate-card__facts">
              <div><span>专业</span><strong :title="row.major || '-'">{{ row.major || '-' }}</strong></div>
              <div><span>学历</span><strong>{{ row.educationLevel || '-' }}</strong></div>
            </div>

            <div class="candidate-card__resume">
              <div class="resume-copy">
                <span class="resume-label">简历</span>
                <span class="resume-name" :title="row.resumeName || '未关联简历'">{{ row.resumeName || '未关联简历' }}</span>
              </div>
              <time :datetime="row.createdAt">{{ formatApplicationTime(row.createdAt) }}</time>
            </div>

            <div class="candidate-card__actions">
              <el-button size="small" type="primary" plain @click="openDetail(row)">详情</el-button>
              <el-button size="small" type="success" plain @click="openCandidateDetail(row)">查看简历</el-button>
              <el-button v-if="row.status === 'PENDING'" size="small" type="warning" plain @click="openProcessing(row)">处理</el-button>
            </div>
          </article>
          </div>

          <div v-if="group.items.length > PAGE_SIZE" class="application-pagination">
            <span class="application-pagination__summary">
              显示 {{ rangeStart(group) }}-{{ rangeEnd(group) }} / {{ group.items.length }} 位候选人
            </span>
            <el-pagination
              :current-page="pageFor(group.groupKey, group.items.length)"
              :page-size="PAGE_SIZE"
              :total="group.items.length"
              layout="prev, pager, next"
              background
              @current-change="updatePage(group.groupKey, $event)"
            />
          </div>
        </div>
      </article>
    </div>

    <el-drawer v-model="drawerVisible" title="投递详情" size="520px">
      <template v-if="selected">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="学生">{{ selected.studentName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ genderText[selected.gender || ''] || selected.gender || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机">{{ selected.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ selected.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="学校">{{ selected.school || '-' }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ selected.major || '-' }}</el-descriptions-item>
          <el-descriptions-item label="学历">{{ selected.educationLevel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="投递职位">{{ selected.jobName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="岗位类型">{{ selected.jobType || '-' }}</el-descriptions-item>
          <el-descriptions-item label="城市">{{ selected.city || '-' }}</el-descriptions-item>
          <el-descriptions-item label="薪资">{{ selected.salaryRange || '-' }}</el-descriptions-item>
          <el-descriptions-item label="简历名称">{{ selected.resumeName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="简历类型">{{ selected.resumeType || '-' }}</el-descriptions-item>
          <el-descriptions-item label="期望职位">{{ selected.targetPosition || '-' }}</el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="statusType[selected.status || ''] || 'info'">
              {{ statusText[selected.status || ''] || selected.status }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="remark-box">
          <div class="remark-title">企业备注</div>
          <el-input v-model="remark" type="textarea" :rows="4" placeholder="填写通过/拒绝原因或面试安排" />
        </div>
      </template>
      <template #footer>
        <el-button @click="drawerVisible = false">关闭</el-button>
        <el-button v-if="selected?.resumeFileId" type="info" @click="viewResume(selected!)">查看简历</el-button>
        <el-button type="danger" :loading="processing" :disabled="selected?.status === 'REJECTED'" @click="handleStatus('REJECTED')">拒绝</el-button>
        <el-button type="primary" :loading="processing" :disabled="selected?.status === 'PASSED'" @click="handleStatus('PASSED')">通过</el-button>
      </template>
    </el-drawer>

    <el-dialog
      v-model="previewVisible"
      :title="previewName"
      width="min(1180px, 96vw)"
      class="resume-preview-dialog"
      :close-on-click-modal="false"
      destroy-on-close
      @closed="closePreview"
    >
      <div v-loading="previewLoading" class="preview-container">
        <div v-if="previewError" class="preview-error"><el-result icon="error" :title="previewError" /></div>
        <iframe v-else-if="previewUrl" :src="previewUrl" class="preview-iframe" frameborder="0" />
        <el-empty v-else-if="!previewLoading" description="无可预览内容" />
      </div>
    </el-dialog>

    <el-dialog
      v-model="detailVisible"
      :title="detailRow?.studentName ? `候选人详情 — ${detailRow.studentName}` : '候选人详情'"
      width="min(820px, 96vw)"
      class="candidate-detail-dialog"
      destroy-on-close
    >
      <div v-loading="detailLoading" class="candidate-detail-body">
        <el-tabs v-if="!detailLoading && detailStudent" type="border-card">
          <el-tab-pane label="基本资料">
            <div class="detail-grid">
              <div><span>姓名</span><strong>{{ detailStudent.realName || '-' }}</strong></div>
              <div><span>性别</span><strong>{{ genderText[detailStudent.gender || ''] || detailStudent.gender || '-' }}</strong></div>
              <div><span>年龄</span><strong>{{ detailStudent.age ?? '-' }}</strong></div>
              <div><span>学校</span><strong>{{ detailStudent.school || '-' }}</strong></div>
              <div><span>专业</span><strong>{{ detailStudent.major || '-' }}</strong></div>
              <div><span>学历</span><strong>{{ detailStudent.educationLevel || '-' }}</strong></div>
              <div><span>GPA</span><strong>{{ detailStudent.gpa || '-' }}</strong></div>
              <div><span>毕业时间</span><strong>{{ detailStudent.graduationDate || '-' }}</strong></div>
              <div><span>家乡</span><strong>{{ detailStudent.hometown || '-' }}</strong></div>
              <div><span>政治面貌</span><strong>{{ detailStudent.politicalStatus || '-' }}</strong></div>
              <div><span>手机</span><strong>{{ detailStudent.phone || '-' }}</strong></div>
              <div><span>邮箱</span><strong>{{ detailStudent.email || '-' }}</strong></div>
              <div><span>微信</span><strong>{{ detailStudent.wechat || '-' }}</strong></div>
              <div><span>QQ</span><strong>{{ detailStudent.qq || '-' }}</strong></div>
              <div><span>期望职位</span><strong>{{ detailStudent.expectedPosition || '-' }}</strong></div>
              <div><span>期望城市</span><strong>{{ detailStudent.expectedCity || '-' }}</strong></div>
              <div><span>期望薪资</span><strong>{{ detailStudent.expectedSalary || '-' }}</strong></div>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="`技能 (${detailSkills.length})`">
            <el-empty v-if="!detailSkills.length" description="暂无技能信息" />
            <div v-else class="detail-skill-list">
              <div v-for="s in detailSkills" :key="s.id" class="detail-skill-item">
                <div class="detail-skill-header">
                  <strong>{{ s.skillName }}</strong>
                  <el-tag size="small" :type="proficiencyTag(s.proficiency)">{{ s.proficiency || '-' }}</el-tag>
                </div>
                <div class="detail-skill-meta">
                  <span v-if="s.skillType">{{ s.skillType }}</span>
                  <span v-if="s.years">{{ s.years }} 年</span>
                </div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="`经历 (${detailExperiences.length})`">
            <el-empty v-if="!detailExperiences.length" description="暂无经历信息" />
            <div v-else class="detail-exp-list">
              <div v-for="e in detailExperiences" :key="e.id" class="detail-exp-item">
                <div class="detail-exp-header">
                  <el-tag size="small" type="info">{{ experienceLabel(e.experienceType) }}</el-tag>
                  <strong>{{ e.title }}</strong>
                  <span class="detail-exp-time">{{ e.timeRange || '-' }}</span>
                </div>
                <p v-if="e.roleName" class="detail-exp-role">{{ e.roleName }}</p>
                <p v-if="e.description" class="detail-exp-desc">{{ e.description }}</p>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="自我评价">
            <el-empty v-if="!detailStudent?.selfIntro" description="暂无自我评价" />
            <p v-else class="detail-self-intro">{{ detailStudent.selfIntro }}</p>
          </el-tab-pane>
        </el-tabs>
        <el-empty v-if="!detailLoading && !detailStudent" description="暂无数据" />
      </div>
      <template #footer>
        <el-button v-if="detailRow?.resumeFileId" type="primary" @click="detailVisible = false; viewResume(detailRow!)">查看简历文件</el-button>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </ModuleCard>
</template>

<style scoped>
.applications-filter-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  margin-bottom: 22px;
  border: 1px solid var(--rp-border);
  border-radius: var(--rp-radius-lg);
  background: var(--rp-surface-muted);
}

.applications-filter-row,
.applications-bulk-bar,
.bulk-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.applications-filter-row .filter-item { width: 160px; }
.filter-search { width: min(300px, 100%); }

.applications-bulk-bar {
  justify-content: space-between;
  padding: 11px 13px;
  border: 1px solid rgba(37, 99, 235, 0.15);
  border-radius: var(--rp-radius-md);
  background: rgba(234, 242, 255, 0.72);
}

.bulk-selection { color: var(--rp-muted); font-size: 13px; }
.bulk-selection strong { color: var(--rp-navy); font-size: 17px; }
.bulk-selection-dot { display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%; background: var(--rp-primary); }
.bulk-actions .el-button { min-width: 92px; }

.application-job-list { display: grid; gap: 20px; min-height: 220px; }

.application-job-card {
  padding: 20px;
  border: 1px solid rgba(185, 203, 228, 0.72);
  border-radius: 22px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.82), rgba(247, 250, 255, 0.62));
  box-shadow: 0 18px 45px rgba(16, 42, 86, 0.08), inset 0 1px rgba(255, 255, 255, 0.8);
}

.application-job-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 18px;
  border-bottom: 1px solid rgba(217, 227, 240, 0.78);
}

.application-job-card__identity { min-width: 0; }
.application-job-card__eyebrow { color: var(--rp-primary); font-size: 11px; font-weight: 800; letter-spacing: 0.12em; }
.application-job-card h3 { max-width: 620px; margin: 6px 0 8px; overflow: hidden; color: var(--rp-navy-strong); font-size: 20px; line-height: 1.35; text-overflow: ellipsis; white-space: nowrap; }
.application-job-card__meta { display: flex; flex-wrap: wrap; gap: 8px; color: var(--rp-muted); font-size: 13px; }
.application-job-card__meta span { padding: 4px 9px; border-radius: 999px; background: rgba(234, 242, 255, 0.7); }

.application-job-card__header-actions { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.application-job-card__stats { display: flex; flex-shrink: 0; gap: 8px; }
.job-stat { min-width: 76px; padding: 9px 11px; border: 1px solid rgba(217, 227, 240, 0.76); border-radius: 13px; background: rgba(255, 255, 255, 0.58); text-align: center; }
.job-stat strong { display: block; color: var(--rp-navy); font-size: 18px; line-height: 1.1; }
.job-stat span { display: block; margin-top: 4px; color: var(--rp-muted); font-size: 11px; }
.job-stat.is-warning strong { color: #b7791f; }
.job-stat.is-success strong { color: #2f855a; }
.application-job-card__toggle { display: inline-flex; align-items: center; gap: 6px; min-height: 34px; padding: 6px 9px; border: 1px solid rgba(185, 203, 228, 0.82); border-radius: 10px; color: var(--rp-primary); background: rgba(255, 255, 255, 0.58); font-size: 12px; font-weight: 750; cursor: pointer; transition: background-color 0.18s ease, border-color 0.18s ease; }
.application-job-card__toggle:hover { border-color: rgba(59, 130, 246, 0.52); background: rgba(234, 242, 255, 0.8); }
.application-job-card__toggle:focus-visible { outline: none; box-shadow: var(--rp-focus-ring); }
.application-job-card__chevron { display: inline-flex; width: 16px; height: 16px; transition: transform 0.18s ease; }
.application-job-card__chevron.is-collapsed { transform: rotate(180deg); }
.application-job-card__body { padding-top: 1px; }

.application-job-card__toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px 2px 14px; }
.job-select-all { display: inline-flex; align-items: center; gap: 7px; color: var(--rp-text); font-size: 13px; font-weight: 700; cursor: pointer; }
.job-candidate-count { color: var(--rp-muted); font-size: 12px; }

.candidate-card-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.candidate-card { min-width: 0; padding: 16px; border: 1px solid rgba(217, 227, 240, 0.9); border-radius: 17px; background: rgba(255, 255, 255, 0.72); box-shadow: 0 8px 24px rgba(16, 42, 86, 0.05); transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease; }
.candidate-card:hover { border-color: rgba(59, 130, 246, 0.42); box-shadow: 0 14px 30px rgba(16, 42, 86, 0.1); transform: translateY(-1px); }
.candidate-card.is-selected { border-color: rgba(37, 99, 235, 0.62); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1), 0 14px 30px rgba(16, 42, 86, 0.09); }
.candidate-card__topline { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.candidate-card__identity { display: flex; align-items: center; gap: 11px; min-width: 0; margin: 14px 0; }
.candidate-avatar { display: grid; flex: 0 0 40px; width: 40px; height: 40px; place-items: center; border-radius: 13px; color: #fff; background: linear-gradient(135deg, var(--rp-primary), var(--rp-navy)); font-size: 17px; font-weight: 800; }
.candidate-name-block { min-width: 0; }
.candidate-name-block h4 { margin: 0 0 4px; overflow: hidden; color: var(--rp-navy-strong); font-size: 16px; text-overflow: ellipsis; white-space: nowrap; }
.candidate-name-block p { margin: 0; overflow: hidden; color: var(--rp-muted); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.candidate-card__facts { display: grid; grid-template-columns: 1fr 0.7fr; gap: 10px; margin-bottom: 12px; }
.candidate-card__facts div { min-width: 0; padding: 9px 10px; border-radius: 11px; background: rgba(244, 247, 251, 0.78); }
.candidate-card__facts span { display: block; margin-bottom: 4px; color: var(--rp-muted); font-size: 11px; }
.candidate-card__facts strong { display: block; overflow: hidden; color: var(--rp-text); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.candidate-card__resume { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-width: 0; padding: 10px 0 13px; border-top: 1px solid rgba(217, 227, 240, 0.78); color: var(--rp-muted); font-size: 12px; }
.resume-copy { display: flex; align-items: center; gap: 7px; min-width: 0; }
.resume-label { flex-shrink: 0; color: var(--rp-primary); font-weight: 800; }
.resume-name { overflow: hidden; color: var(--rp-text); text-overflow: ellipsis; white-space: nowrap; }
.candidate-card__resume time { flex-shrink: 0; white-space: nowrap; }
.candidate-card__actions { display: flex; gap: 7px; padding-top: 12px; border-top: 1px solid rgba(217, 227, 240, 0.78); }
.candidate-card__actions .el-button { flex: 1 1 0; min-width: 0; }
.application-pagination { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 18px; padding: 12px 14px; border: 1px solid rgba(217, 227, 240, 0.78); border-radius: 14px; background: rgba(248, 250, 255, 0.68); }
.application-pagination__summary { color: var(--rp-muted); font-size: 12px; white-space: nowrap; }
.application-pagination :deep(.el-pagination) { margin-left: auto; }
.application-pagination :deep(.el-pagination.is-background .el-pager li.is-active) { background-color: var(--rp-primary); }

.remark-box { margin-top: 18px; }
.remark-title { margin-bottom: 8px; color: var(--rp-navy); font-weight: 700; }
.preview-container { display: flex; align-items: center; justify-content: center; min-height: min(78vh, 860px); height: min(78vh, 860px); }
:deep(.resume-preview-dialog .el-dialog__body) { padding-top: 12px; }
.preview-iframe { width: 100%; height: 100%; border: 1px solid var(--rp-border); border-radius: 8px; }
.preview-error { padding: 40px; text-align: center; }

@media (max-width: 860px) {
  .application-job-card { padding: 16px; border-radius: 18px; }
  .application-job-card__header { flex-direction: column; gap: 14px; }
  .application-job-card__header-actions { width: 100%; align-items: stretch; flex-wrap: wrap; }
  .application-job-card__stats { width: 100%; }
  .job-stat { flex: 1; }
  .application-job-card__toggle { justify-content: center; }
  .application-job-card h3 { max-width: 100%; white-space: normal; }
  .candidate-card-grid { grid-template-columns: 1fr; }
  .applications-filter-row .filter-item,
  .filter-search { width: 100%; }
  .applications-filter-row > .el-button { width: 100%; }
  .applications-bulk-bar { align-items: flex-start; flex-direction: column; }
  .bulk-actions { width: 100%; }
  .bulk-actions .el-button { flex: 1; }
  .application-pagination { align-items: flex-start; flex-direction: column; gap: 10px; }
  .application-pagination :deep(.el-pagination) { width: 100%; margin-left: 0; justify-content: center; }
}

.candidate-detail-body { min-height: 320px; }
.candidate-detail-body :deep(.el-tabs__content) { padding: 16px 20px; }
.detail-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.detail-grid div { min-width: 0; padding: 10px 12px; border-radius: 10px; background: rgba(244, 247, 251, 0.72); }
.detail-grid span { display: block; margin-bottom: 2px; color: var(--rp-muted); font-size: 12px; }
.detail-grid strong { display: block; color: var(--rp-text); font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.detail-skill-list { display: grid; gap: 10px; }
.detail-skill-item { padding: 11px 13px; border-radius: 10px; background: rgba(244, 247, 251, 0.72); }
.detail-skill-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.detail-skill-meta { display: flex; gap: 10px; margin-top: 6px; color: var(--rp-muted); font-size: 12px; }
.detail-exp-list { display: grid; gap: 12px; }
.detail-exp-item { padding: 13px 14px; border-radius: 10px; background: rgba(244, 247, 251, 0.72); }
.detail-exp-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.detail-exp-time { margin-left: auto; color: var(--rp-muted); font-size: 12px; white-space: nowrap; }
.detail-exp-role { margin: 6px 0 0; color: var(--rp-muted); font-size: 13px; }
.detail-exp-desc { margin: 6px 0 0; color: var(--rp-text); font-size: 13px; line-height: 1.6; white-space: pre-wrap; }
.detail-self-intro { margin: 0; color: var(--rp-text); font-size: 14px; line-height: 1.8; white-space: pre-wrap; }

@media (max-width: 480px) {
  .application-job-card__toolbar { align-items: flex-start; flex-direction: column; }
  .candidate-card { padding: 14px; }
  .candidate-card__actions { flex-wrap: wrap; }
  .candidate-card__actions .el-button { flex: 1 1 30%; }
}
</style>
