<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentAdd, MagicStick, Refresh, View } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'

import { previewFile, uploadFile } from '@/api/files'
import {
  createResume,
  deleteResume,
  generateResume,
  getResumeGenerationContext,
  listResumesByStudent,
  updateResume,
} from '@/api/student'
import ModuleCard from '@/components/ModuleCard.vue'
import { useAuthStore } from '@/stores/auth'
import type {
  GeneratedResumeResponse,
  Resume,
  ResumeGenerationSnapshot,
  ResumeTemplate,
  StudentExperience,
  StudentProfile,
  StudentSkill,
} from '@/types/api'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const generating = ref(false)
const contextLoading = ref(false)
const dialogVisible = ref(false)
const generatorVisible = ref(false)
const editing = ref<Resume | null>(null)
const formRef = ref<FormInstance>()
const resumes = ref<Resume[]>([])
const templates = ref<ResumeTemplate[]>([])
const selectedTemplateId = ref<number>()
const generatedResult = ref<GeneratedResumeResponse | null>(null)

const previewVisible = ref(false)
const previewUrl = ref('')
const previewLoading = ref(false)
const previewError = ref('')
const previewTitle = ref('简历预览')

const form = reactive<Resume>({
  resumeName: '',
  resumeType: 'UPLOAD',
  targetPosition: '',
  fileId: undefined,
  fileUrl: '',
  school: '',
  major: '',
  educationLevel: '',
  graduationDate: '',
  skillTags: '',
})

const snapshot = reactive<ResumeGenerationSnapshot>({
  resumeName: '',
  targetPosition: '',
  profile: {},
  skills: [],
  experiences: [],
})
const availableSkills = ref<StudentSkill[]>([])
const availableExperiences = ref<StudentExperience[]>([])
const selectedSkillKeys = ref<string[]>([])
const selectedExperienceKeys = ref<string[]>([])

const resumeStats = computed(() => ({
  total: resumes.value.length,
  uploaded: resumes.value.filter((item) => item.resumeType === 'UPLOAD').length,
  online: resumes.value.filter((item) => item.resumeType === 'ONLINE').length,
}))

const rules = {
  targetPosition: [{ required: true, message: '请填写目标岗位', trigger: 'blur' }],
  school: [{ required: true, message: '请填写学校', trigger: 'blur' }],
  major: [{ required: true, message: '请填写专业', trigger: 'blur' }],
}

const selectedTemplate = computed(() => templates.value.find((item) => item.id === selectedTemplateId.value))
const selectedTemplateCode = computed(() => selectedTemplate.value?.templateCode || 'classic')
const groupedExperiences = computed(() => snapshot.experiences || [])

function resumeTypeLabel(type?: string) {
  return type === 'ONLINE' ? '模板生成' : '上传简历'
}

function resumeTypeTag(type?: string): 'success' | 'primary' {
  return type === 'ONLINE' ? 'success' : 'primary'
}

function resetForm() {
  Object.assign(form, {
    resumeName: '',
    resumeType: 'UPLOAD',
    targetPosition: '',
    fileId: undefined,
    fileUrl: '',
    school: '',
    major: '',
    educationLevel: '',
    graduationDate: '',
    skillTags: '',
  })
}

function applySnapshot(next: ResumeGenerationSnapshot) {
  snapshot.resumeName = next.resumeName || ''
  snapshot.targetPosition = next.targetPosition || ''
  snapshot.profile = { ...(next.profile || {}) }
  availableSkills.value = (next.skills || []).map((item) => ({ ...item }))
  availableExperiences.value = (next.experiences || []).map((item) => ({ ...item }))
  selectedSkillKeys.value = availableSkills.value.map(skillKey)
  selectedExperienceKeys.value = availableExperiences.value.map(experienceKey)
  syncSelectedSkills()
  syncSelectedExperiences()
}

function skillKey(skill: StudentSkill, index = 0) {
  return skill.id ? `skill-${skill.id}` : `skill-${index}-${skill.skillName || 'empty'}`
}

function experienceKey(item: StudentExperience, index = 0) {
  return item.id ? `experience-${item.id}` : `experience-${index}-${item.title || 'empty'}`
}

function syncSelectedSkills() {
  const selected = new Set(selectedSkillKeys.value)
  snapshot.skills = availableSkills.value
    .filter((item, index) => selected.has(skillKey(item, index)))
    .map((item) => ({ ...item }))
}

function syncSelectedExperiences() {
  const selected = new Set(selectedExperienceKeys.value)
  snapshot.experiences = availableExperiences.value
    .filter((item, index) => selected.has(experienceKey(item, index)))
    .map((item, index) => ({ ...item, sortOrder: item.sortOrder || index + 1 }))
}

async function load() {
  if (!auth.userId) return
  loading.value = true
  try {
    resumes.value = await listResumesByStudent(auth.userId)
  } finally {
    loading.value = false
  }
}

async function loadGenerationContext() {
  contextLoading.value = true
  try {
    const context = await getResumeGenerationContext()
    templates.value = context.templates || []
    selectedTemplateId.value = context.defaultTemplateId || templates.value[0]?.id
    applySnapshot(context.snapshot)
  } finally {
    contextLoading.value = false
  }
}

async function openGenerator() {
  generatedResult.value = null
  generatorVisible.value = true
  await loadGenerationContext()
}

function openCreate() {
  editing.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Resume) {
  editing.value = row
  Object.assign(form, {
    ...row,
    graduationDate: row.graduationDate || '',
  })
  dialogVisible.value = true
}

async function onResumeFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  uploading.value = true
  try {
    const uploaded = await uploadFile(file, 'RESUME')
    form.fileId = uploaded.id
    form.fileUrl = uploaded.fileUrl
    if (!form.resumeName) {
      form.resumeName = file.name.replace(/\.[^.]+$/, '')
    }
    ElMessage.success('简历文件已上传')
  } finally {
    uploading.value = false
  }
}

function buildPayload(): Resume {
  return {
    resumeName: form.resumeName,
    resumeType: form.resumeType || 'UPLOAD',
    targetPosition: form.targetPosition,
    fileId: form.fileId,
    school: form.school,
    major: form.major,
    educationLevel: form.educationLevel,
    graduationDate: form.graduationDate,
    skillTags: form.skillTags,
  }
}

async function save() {
  if (!form.resumeName?.trim()) {
    ElMessage.warning('请填写简历名称')
    return
  }
  if (form.resumeType === 'UPLOAD' && !form.fileId) {
    ElMessage.warning('请先上传简历文件')
    return
  }
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    if (editing.value?.id) {
      await updateResume(editing.value.id, buildPayload())
      ElMessage.success('简历已更新')
    } else {
      await createResume(buildPayload())
      ElMessage.success('简历已创建')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function remove(row: Resume) {
  if (!row.id) return
  try {
    await ElMessageBox.confirm(`确定删除简历「${row.resumeName || row.id}」吗？`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  await deleteResume(row.id)
  ElMessage.success('简历已删除')
  await load()
}

function addSkill() {
  snapshot.skills.push({ skillName: '', skillType: '', proficiency: '', years: 0 })
}

function removeSkill(index: number) {
  const item = snapshot.skills[index]
  selectedSkillKeys.value = selectedSkillKeys.value.filter((key) => key !== skillKey(item, index))
  snapshot.skills.splice(index, 1)
}

function addExperience() {
  snapshot.experiences.push({
    experienceType: 'PROJECT',
    title: '',
    timeRange: '',
    roleName: '',
    description: '',
    sortOrder: snapshot.experiences.length + 1,
  })
}

function removeExperience(index: number) {
  const item = snapshot.experiences[index]
  selectedExperienceKeys.value = selectedExperienceKeys.value.filter((key) => key !== experienceKey(item, index))
  snapshot.experiences.splice(index, 1)
}

async function generateFromSnapshot() {
  if (!selectedTemplateId.value) {
    ElMessage.warning('请选择简历模板')
    return
  }
  if (!snapshot.resumeName?.trim()) {
    ElMessage.warning('请填写简历名称')
    return
  }
  generating.value = true
  try {
    const result = await generateResume({
      templateId: selectedTemplateId.value,
      snapshot: {
        resumeName: snapshot.resumeName,
        targetPosition: snapshot.targetPosition,
        profile: { ...snapshot.profile },
        skills: snapshot.skills.map((item) => ({ ...item })),
        experiences: snapshot.experiences.map((item) => ({ ...item })),
      },
    })
    generatedResult.value = result
    ElMessage.success('简历 PDF 已生成')
    await load()
  } finally {
    generating.value = false
  }
}

function previewGeneratedPdf() {
  if (!generatedResult.value?.resume) return
  preview(generatedResult.value.resume)
}

async function preview(row: Resume) {
  if (!row.fileId) {
    ElMessage.warning('该简历没有可预览文件')
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
    const blob = await previewFile(row.fileId)
    previewUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    previewError.value = error instanceof Error ? error.message : '简历预览失败'
  } finally {
    previewLoading.value = false
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

function formatEducation(profile: StudentProfile) {
  return [profile.school, profile.major, profile.educationLevel, profile.graduationDate].filter(Boolean).join(' · ')
}

function skillText(skill: StudentSkill) {
  return [skill.skillName, skill.proficiency].filter(Boolean).join(' · ')
}

function experienceMeta(item: StudentExperience) {
  return [item.roleName, item.timeRange].filter(Boolean).join(' · ')
}

onMounted(load)
</script>

<template>
  <ModuleCard title="简历管理" subtitle="维护可投递简历，或使用模板生成 PDF">
    <template #actions>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
      <el-button type="primary" plain :icon="MagicStick" @click="openGenerator">模板生成</el-button>
      <el-button type="primary" :icon="DocumentAdd" @click="openCreate">上传简历</el-button>
    </template>

    <div class="resume-action-bar">
      <span>模板生成会保存独立快照，不会改动个人资料、技能或经历。</span>
      <el-tag type="info" effect="plain">PDF / Word 上传 + PDF 生成</el-tag>
    </div>

    <div class="resume-summary">
      <div>
        <span>简历总数</span>
        <strong>{{ resumeStats.total }}</strong>
      </div>
      <div>
        <span>上传简历</span>
        <strong>{{ resumeStats.uploaded }}</strong>
      </div>
      <div>
        <span>模板生成</span>
        <strong>{{ resumeStats.online }}</strong>
      </div>
    </div>

    <div class="table-scroll">
      <el-table v-loading="loading" :data="resumes" border>
        <el-table-column prop="resumeName" label="简历名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="targetPosition" label="目标岗位" min-width="140" show-overflow-tooltip />
        <el-table-column prop="school" label="学校" min-width="140" show-overflow-tooltip />
        <el-table-column prop="major" label="专业" min-width="120" show-overflow-tooltip />
        <el-table-column prop="educationLevel" label="学历" width="90" />
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-tag :type="resumeTypeTag(row.resumeType)" effect="plain">{{ resumeTypeLabel(row.resumeType) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" width="170" />
        <el-table-column label="操作" width="224" fixed="right">
          <template #default="{ row }">
            <div class="resume-row-actions">
              <el-button :icon="View" type="primary" link @click="preview(row)">预览</el-button>
              <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
              <el-button type="danger" link @click="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑简历' : '上传简历'" width="680px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <div class="dialog-grid">
          <el-form-item label="简历名称" required>
            <el-input v-model="form.resumeName" placeholder="如：Java 后端开发简历" />
          </el-form-item>
          <el-form-item label="简历类型">
            <el-select v-model="form.resumeType">
              <el-option label="上传简历" value="UPLOAD" />
              <el-option label="模板生成" value="ONLINE" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标岗位" prop="targetPosition">
            <el-input v-model="form.targetPosition" placeholder="如：后端开发工程师" />
          </el-form-item>
          <el-form-item label="学校" prop="school">
            <el-input v-model="form.school" placeholder="请输入学校" />
          </el-form-item>
          <el-form-item label="专业" prop="major">
            <el-input v-model="form.major" placeholder="请输入专业" />
          </el-form-item>
          <el-form-item label="学历">
            <el-select v-model="form.educationLevel" clearable placeholder="请选择">
              <el-option label="专科" value="专科" />
              <el-option label="本科" value="本科" />
              <el-option label="硕士" value="硕士" />
              <el-option label="博士" value="博士" />
            </el-select>
          </el-form-item>
          <el-form-item label="毕业时间">
            <el-date-picker v-model="form.graduationDate" type="date" value-format="YYYY-MM-DD" placeholder="请选择" />
          </el-form-item>
          <el-form-item label="技能标签">
            <el-input v-model="form.skillTags" placeholder="如：Java, Spring, MySQL" />
          </el-form-item>
        </div>
        <el-form-item label="简历文件">
          <div class="file-line">
            <el-button :loading="uploading" type="primary" plain>
              {{ form.fileId ? '重新上传' : '上传文件' }}
              <input type="file" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png" @change="onResumeFileChange" />
            </el-button>
            <span v-if="form.fileId" class="muted">已绑定文件 ID：{{ form.fileId }}</span>
            <span v-else class="muted">支持 PDF、Word、图片，Word 预览会转 PDF</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="generatorVisible" title="模板生成简历" size="min(1180px, 96vw)" destroy-on-close>
      <div v-loading="contextLoading" class="generator">
        <section class="generator-editor">
          <el-form label-position="top">
            <el-form-item label="模板">
              <el-radio-group v-model="selectedTemplateId" class="template-list">
                <el-radio-button v-for="template in templates" :key="template.id" :label="template.id">
                  {{ template.templateName }}
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="简历名称">
              <el-input v-model="snapshot.resumeName" />
            </el-form-item>
            <div class="editor-grid">
              <el-form-item label="姓名">
                <el-input v-model="snapshot.profile.realName" />
              </el-form-item>
              <el-form-item label="目标岗位">
                <el-input v-model="snapshot.targetPosition" />
              </el-form-item>
              <el-form-item label="电话">
                <el-input v-model="snapshot.profile.phone" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="snapshot.profile.email" />
              </el-form-item>
              <el-form-item label="学校">
                <el-input v-model="snapshot.profile.school" />
              </el-form-item>
              <el-form-item label="专业">
                <el-input v-model="snapshot.profile.major" />
              </el-form-item>
              <el-form-item label="学历">
                <el-input v-model="snapshot.profile.educationLevel" />
              </el-form-item>
              <el-form-item label="毕业时间">
                <el-date-picker v-model="snapshot.profile.graduationDate" type="date" value-format="YYYY-MM-DD" />
              </el-form-item>
            </div>
            <el-form-item label="个人简介">
              <el-input v-model="snapshot.profile.selfIntro" type="textarea" :rows="3" />
            </el-form-item>
          </el-form>

          <div class="source-panel">
            <div class="section-head">
              <strong>从已有技能选择</strong>
              <span class="muted">勾选后进入本次生成快照</span>
            </div>
            <el-checkbox-group v-model="selectedSkillKeys" class="choice-grid" @change="syncSelectedSkills">
              <el-checkbox
                v-for="(skill, index) in availableSkills"
                :key="skillKey(skill, index)"
                :label="skillKey(skill, index)"
                border
              >
                <span class="choice-title">{{ skill.skillName || '未命名技能' }}</span>
                <small>{{ [skill.skillType, skill.proficiency].filter(Boolean).join(' · ') }}</small>
              </el-checkbox>
            </el-checkbox-group>
            <el-empty v-if="!availableSkills.length" description="暂无已有技能，可在下方手动新增" />
          </div>

          <div class="source-panel">
            <div class="section-head">
              <strong>从已有经历选择</strong>
              <span class="muted">只生成你勾选的经历</span>
            </div>
            <el-checkbox-group v-model="selectedExperienceKeys" class="experience-choice-list" @change="syncSelectedExperiences">
              <el-checkbox
                v-for="(item, index) in availableExperiences"
                :key="experienceKey(item, index)"
                :label="experienceKey(item, index)"
                border
              >
                <span class="choice-title">{{ item.title || '未命名经历' }}</span>
                <small>{{ [item.experienceType, item.roleName, item.timeRange].filter(Boolean).join(' · ') }}</small>
              </el-checkbox>
            </el-checkbox-group>
            <el-empty v-if="!availableExperiences.length" description="暂无已有经历，可在下方手动新增" />
          </div>

          <div class="editor-section">
            <div class="section-head">
              <strong>技能</strong>
              <el-button type="primary" link @click="addSkill">新增技能</el-button>
            </div>
            <div v-for="(skill, index) in snapshot.skills" :key="index" class="inline-row">
              <el-input v-model="skill.skillName" placeholder="技能名称" />
              <el-input v-model="skill.proficiency" placeholder="熟练度" />
              <el-button type="danger" link @click="removeSkill(index)">删除</el-button>
            </div>
          </div>

          <div class="editor-section">
            <div class="section-head">
              <strong>项目与经历</strong>
              <el-button type="primary" link @click="addExperience">新增经历</el-button>
            </div>
            <div v-for="(item, index) in snapshot.experiences" :key="index" class="experience-editor">
              <div class="inline-row">
                <el-input v-model="item.title" placeholder="标题" />
                <el-input v-model="item.timeRange" placeholder="时间范围" />
                <el-button type="danger" link @click="removeExperience(index)">删除</el-button>
              </div>
              <el-input v-model="item.roleName" placeholder="角色/职责" />
              <el-input v-model="item.description" type="textarea" :rows="3" placeholder="经历描述" />
            </div>
          </div>

          <div class="generator-actions">
            <el-button @click="generatorVisible = false">关闭</el-button>
            <el-button type="primary" :loading="generating" @click="generateFromSnapshot">生成 PDF</el-button>
            <el-button v-if="generatedResult" type="success" plain @click="previewGeneratedPdf">预览生成结果</el-button>
          </div>
        </section>

        <section class="preview-paper" :class="`template-${selectedTemplateCode}`">
          <div class="preview-sidebar" v-if="selectedTemplateCode === 'project'">
            <h1>{{ snapshot.profile.realName || '未填写姓名' }}</h1>
            <p>{{ snapshot.targetPosition || snapshot.profile.expectedPosition || '求职目标' }}</p>
            <div class="preview-block">
              <strong>联系方式</strong>
              <span>{{ snapshot.profile.phone }}</span>
              <span>{{ snapshot.profile.email }}</span>
              <span>{{ snapshot.profile.expectedCity }}</span>
            </div>
            <div class="preview-block">
              <strong>核心技能</strong>
              <span v-for="skill in snapshot.skills" :key="skill.skillName">{{ skill.skillName }}</span>
            </div>
          </div>
          <div class="preview-main">
            <header v-if="selectedTemplateCode !== 'project'" class="preview-header">
              <h1>{{ snapshot.profile.realName || '未填写姓名' }}</h1>
              <p>{{ snapshot.targetPosition || snapshot.profile.expectedPosition || '求职目标' }}</p>
              <div>{{ [snapshot.profile.phone, snapshot.profile.email, snapshot.profile.expectedCity].filter(Boolean).join(' · ') }}</div>
            </header>
            <section v-if="snapshot.profile.selfIntro">
              <h2>个人简介</h2>
              <p>{{ snapshot.profile.selfIntro }}</p>
            </section>
            <section>
              <h2>教育背景</h2>
              <strong>{{ formatEducation(snapshot.profile) || '学校 / 专业 / 学历' }}</strong>
            </section>
            <section v-if="selectedTemplateCode !== 'project' && snapshot.skills.length">
              <h2>技能标签</h2>
              <div class="preview-skills">
                <span v-for="skill in snapshot.skills" :key="skill.skillName">{{ skillText(skill) }}</span>
              </div>
            </section>
            <section v-if="groupedExperiences.length">
              <h2>项目与经历</h2>
              <article v-for="item in groupedExperiences" :key="item.title" class="preview-exp">
                <div>
                  <strong>{{ item.title || '经历标题' }}</strong>
                  <span>{{ experienceMeta(item) }}</span>
                </div>
                <p>{{ item.description }}</p>
              </article>
            </section>
          </div>
        </section>
      </div>
    </el-drawer>

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
  </ModuleCard>
</template>

<style scoped>
.resume-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  color: var(--rp-muted);
  font-size: 13px;
  line-height: 1.6;
}

.resume-row-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  white-space: nowrap;
}

.resume-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.resume-summary div {
  padding: 14px 16px;
  border: 1px solid var(--rp-border);
  border-radius: var(--rp-radius-md);
  background: var(--rp-surface-muted);
}

.resume-summary span,
.file-line .muted {
  display: block;
  color: var(--rp-muted);
  font-size: 13px;
}

.resume-summary strong {
  display: block;
  margin-top: 8px;
  color: #0f1f35;
  font-size: 24px;
}

.dialog-grid,
.editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 14px;
}

.file-line {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.file-line .el-button {
  position: relative;
  overflow: hidden;
}

.file-line input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.generator {
  display: grid;
  grid-template-columns: minmax(360px, 480px) minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}

.generator-editor {
  max-height: calc(100vh - 132px);
  overflow: auto;
  padding-right: 4px;
}

.template-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.editor-section {
  margin-top: 16px;
  border-top: 1px solid var(--rp-border);
  padding-top: 12px;
}

.source-panel {
  margin-top: 16px;
  border: 1px solid var(--rp-border);
  border-radius: 8px;
  padding: 12px;
  background: #f8fafc;
}

.choice-grid,
.experience-choice-list {
  display: grid;
  gap: 8px;
}

.choice-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.experience-choice-list {
  grid-template-columns: 1fr;
}

.choice-grid :deep(.el-checkbox),
.experience-choice-list :deep(.el-checkbox) {
  height: auto;
  display: flex;
  align-items: flex-start;
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff;
  white-space: normal;
}

.choice-grid :deep(.el-checkbox__label),
.experience-choice-list :deep(.el-checkbox__label) {
  min-width: 0;
  display: grid;
  gap: 3px;
  line-height: 1.35;
}

.choice-title {
  overflow: hidden;
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
  text-overflow: ellipsis;
}

.choice-grid small,
.experience-choice-list small {
  color: #64748b;
  font-size: 12px;
}

.section-head,
.generator-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.inline-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  gap: 8px;
  margin-bottom: 8px;
}

.experience-editor {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
  border: 1px solid var(--rp-border);
  border-radius: 8px;
  padding: 10px;
  background: #fbfcff;
}

.preview-paper {
  width: min(100%, 720px);
  min-height: 920px;
  display: grid;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
  background: #fff;
  color: #172033;
  border: 1px solid var(--rp-border);
  box-shadow: 0 16px 42px rgba(16, 42, 86, 0.12);
}

.template-classic::before {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 26px;
  background: linear-gradient(90deg, #1d4ed8, #14b8a6 56%, #f59e0b);
  content: '';
}

.preview-main {
  padding: 34px 38px;
}

.preview-header {
  border-bottom: 1px solid #dbe3ee;
  padding-bottom: 14px;
}

.preview-paper h1 {
  margin: 0;
  font-size: 28px;
  letter-spacing: 0;
}

.preview-paper h2 {
  margin: 18px 0 9px;
  color: #0f172a;
  font-size: 15px;
}

.preview-paper p {
  margin: 0;
  white-space: pre-line;
}

.preview-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-skills span {
  border: 1px solid #c9d7ec;
  border-radius: 999px;
  padding: 5px 9px;
  background: #f8fbff;
  font-size: 12px;
}

.preview-exp {
  margin-bottom: 12px;
}

.preview-exp div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.preview-exp span {
  color: #64748b;
  font-size: 12px;
}

.template-compact .preview-main {
  padding: 28px 34px;
}

.template-compact .preview-header {
  border: 1px solid #d9e2ee;
  border-left: 5px solid #0f766e;
  border-radius: 8px;
  padding: 12px 14px;
  background: #f8fbfb;
}

.template-compact h2 {
  border-radius: 5px;
  padding: 4px 8px;
  background: #eef6f5;
  color: #0f3f3b;
}

.template-project {
  grid-template-columns: 210px minmax(0, 1fr);
}

.template-project .preview-sidebar {
  padding: 34px 24px;
  background: linear-gradient(180deg, #172554, #0f172a 58%, #111827);
  color: #e5eefc;
}

.template-project .preview-sidebar p {
  color: #93c5fd;
  font-weight: 700;
}

.preview-block {
  display: grid;
  gap: 6px;
  margin-top: 22px;
  font-size: 12px;
}

.preview-block strong {
  color: #bfdbfe;
}

.template-project .preview-main {
  padding: 34px 34px;
}

.template-project .preview-exp {
  border: 1px solid #e2e8f0;
  border-left: 4px solid #f59e0b;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fffdfa;
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

@media (max-width: 920px) {
  .generator {
    grid-template-columns: 1fr;
  }

  .generator-editor {
    max-height: none;
  }
}

@media (max-width: 720px) {
  .resume-action-bar {
    align-items: flex-start;
    flex-direction: column;
  }

  .resume-summary,
  .dialog-grid,
  .editor-grid {
    grid-template-columns: 1fr;
  }

  .inline-row {
    grid-template-columns: 1fr;
  }

  .choice-grid {
    grid-template-columns: 1fr;
  }
}
</style>
