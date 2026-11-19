<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'

import { getMyCompany, saveMyCompany, updateMyCompanyLogo } from '@/api/company'
import { getFileResource, uploadFile } from '@/api/files'
import ModuleCard from '@/components/ModuleCard.vue'
import { useAuthStore } from '@/stores/auth'
import type { Company } from '@/types/api'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const logoUrl = ref('')
const logoLoadError = ref(false)
const localLogoPreviewUrl = ref('')

const form = reactive<Company>({
  companyName: '',
  industry: '',
  companySize: '',
  contactName: '',
  contactPhone: '',
  description: '',
})

const reviewText: Record<string, string> = {
  PENDING: '审核中',
  APPROVED: '已通过',
  REJECTED: '已驳回',
}

const companySizeOptions = ['少于50人', '50-150人', '150-500人', '500人以上']
const displayLogoUrl = computed(() => (logoUrl.value && !logoLoadError.value ? logoUrl.value : ''))

function setLogoUrl(url: string) {
  logoUrl.value = url
  logoLoadError.value = false
}

function revokeLocalLogoPreview() {
  if (localLogoPreviewUrl.value) {
    URL.revokeObjectURL(localLogoPreviewUrl.value)
    localLogoPreviewUrl.value = ''
  }
}

function fillForm(company?: Company | null) {
  Object.assign(form, {
    id: company?.id,
    userId: company?.userId,
    companyName: company?.companyName || '',
    industry: company?.industry || '',
    companySize: company?.companySize || '',
    contactName: company?.contactName || '',
    contactPhone: company?.contactPhone || '',
    description: company?.description || '',
    logoFileId: company?.logoFileId,
    reviewStatus: company?.reviewStatus,
    reviewReason: company?.reviewReason,
  })
}

async function loadLogo(fileId?: number) {
  setLogoUrl('')
  if (!fileId) return
  try {
    const file = await getFileResource(fileId)
    setLogoUrl(file?.fileUrl || '')
  } catch {
    setLogoUrl('')
  }
}

async function load() {
  if (!auth.userId) return
  loading.value = true
  try {
    const company = await getMyCompany(auth.userId)
    fillForm(company)
    await loadLogo(company?.logoFileId)
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!auth.userId || uploading.value) return
  if (!form.companyName?.trim()) {
    ElMessage.warning('请先填写企业名称')
    return
  }
  saving.value = true
  try {
    const expectedLogoFileId = form.logoFileId
    const payload: Company = {
      companyName: form.companyName.trim(),
      industry: form.industry,
      companySize: form.companySize,
      contactName: form.contactName,
      contactPhone: form.contactPhone,
      description: form.description,
      logoFileId: expectedLogoFileId,
    }
    const saved = await saveMyCompany(auth.userId, payload)
    const refreshed = (await getMyCompany(auth.userId)) || saved
    fillForm(refreshed)
    if (expectedLogoFileId && refreshed.logoFileId !== expectedLogoFileId) {
      ElMessage.error('Logo 文件ID未保存成功，请重试')
      return
    }
    if (!localLogoPreviewUrl.value) {
      await loadLogo(refreshed.logoFileId)
    }
    ElMessage.success('企业资料已提交')
  } finally {
    saving.value = false
  }
}

async function handleLogoChange(file: UploadFile) {
  if (!file.raw || !auth.userId) return
  const previousLogoFileId = form.logoFileId
  revokeLocalLogoPreview()
  localLogoPreviewUrl.value = URL.createObjectURL(file.raw)
  setLogoUrl(localLogoPreviewUrl.value)
  uploading.value = true
  try {
    const uploaded = await uploadFile(file.raw, 'LOGO')
    form.logoFileId = uploaded.id
    if (form.id) {
      const saved = await updateMyCompanyLogo(auth.userId, uploaded.id)
      fillForm(saved)
      ElMessage.success('Logo 已上传并保存')
      return
    }
    ElMessage.success('Logo 已上传，保存企业资料后生效')
  } catch (error) {
    form.logoFileId = previousLogoFileId
    revokeLocalLogoPreview()
    await loadLogo(previousLogoFileId)
    throw error
  } finally {
    uploading.value = false
  }
}

onMounted(load)
onBeforeUnmount(revokeLocalLogoPreview)
</script>

<template>
  <ModuleCard title="企业信息" subtitle="维护企业资料和审核信息">
    <template #actions>
      <el-tag
        v-if="form.reviewStatus"
        :type="form.reviewStatus === 'APPROVED' ? 'success' : form.reviewStatus === 'REJECTED' ? 'danger' : 'warning'"
      >
        {{ reviewText[form.reviewStatus] || form.reviewStatus }}
      </el-tag>
    </template>

    <el-form v-loading="loading" label-width="108px" class="company-form">
      <el-alert
        v-if="form.reviewStatus === 'REJECTED'"
        class="review-alert"
        type="error"
        show-icon
        :closable="false"
        :title="form.reviewReason || '企业资料审核未通过，请修改后重新提交'"
      />

      <div class="info-grid">
        <section class="info-section main-section">
          <div class="section-heading">
            <div>
              <h3>基础信息</h3>
              <p>用于企业入驻审核和岗位展示</p>
            </div>
          </div>

          <el-form-item label="企业Logo">
            <div class="logo-line">
              <div class="logo-preview">
                <img v-if="displayLogoUrl" :src="displayLogoUrl" alt="企业Logo" @error="logoLoadError = true" />
                <span v-else>{{ form.logoFileId ? '已上传' : '未上传' }}</span>
              </div>
              <div>
                <el-upload :auto-upload="false" :show-file-list="false" accept="image/*" :on-change="handleLogoChange">
                  <el-button :loading="uploading">上传Logo</el-button>
                </el-upload>
                <p class="hint">支持 JPG / PNG，建议 200x200px</p>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="企业名称" required>
            <el-input v-model="form.companyName" placeholder="请输入企业名称" />
          </el-form-item>
          <el-form-item label="所属行业">
            <el-input v-model="form.industry" placeholder="例如：互联网、金融、智能制造" />
          </el-form-item>
          <el-form-item label="企业规模">
            <el-select v-model="form.companySize" placeholder="请选择企业规模" class="field">
              <el-option v-for="option in companySizeOptions" :key="option" :label="option" :value="option" />
            </el-select>
          </el-form-item>
          <el-form-item label="企业简介">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="6"
              maxlength="500"
              show-word-limit
              placeholder="介绍企业业务、校园招聘亮点和人才培养机制"
            />
          </el-form-item>
        </section>

        <aside class="side-sections">
          <section class="info-section">
            <div class="section-heading compact">
              <h3>联系信息</h3>
            </div>
            <el-form-item label="联系人">
              <el-input v-model="form.contactName" placeholder="请输入联系人姓名" />
            </el-form-item>
            <el-form-item label="联系电话">
              <el-input v-model="form.contactPhone" placeholder="请输入联系电话" />
            </el-form-item>
          </section>

          <section class="info-section audit-section">
            <div class="section-heading compact">
              <h3>审核信息</h3>
            </div>
            <div class="audit-line">
              <span>审核状态</span>
              <el-tag
                :type="form.reviewStatus === 'APPROVED' ? 'success' : form.reviewStatus === 'REJECTED' ? 'danger' : 'warning'"
                effect="light"
              >
                {{ reviewText[form.reviewStatus || 'PENDING'] || '审核中' }}
              </el-tag>
            </div>
            <p class="audit-copy">
              {{
                form.reviewStatus === 'APPROVED'
                  ? '企业资料已通过审核，可以发布职位。'
                  : form.reviewStatus === 'REJECTED'
                    ? form.reviewReason || '请根据审核意见修改后重新提交。'
                    : '资料提交后，平台通常会在 1-2 个工作日内完成审核。'
              }}
            </p>
            <el-button type="primary" :loading="saving" :disabled="uploading" class="save-button" @click="save">
              保存并提交审核
            </el-button>
          </section>
        </aside>
      </div>
    </el-form>
  </ModuleCard>
</template>

<style scoped>
.company-form {
  width: 100%;
}

.field {
  width: 100%;
}

.review-alert {
  margin-bottom: 18px;
}

.info-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
}

.info-section {
  padding: 18px;
  border: 1px solid var(--rp-border);
  border-radius: 8px;
  background: #fff;
}

.main-section {
  background:
    linear-gradient(180deg, rgba(244, 248, 255, 0.9), rgba(255, 255, 255, 0.92)),
    #fff;
}

.side-sections {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  margin-bottom: 18px;
}

.section-heading h3 {
  margin: 0;
  color: #0f1f35;
  font-size: 17px;
}

.section-heading p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.section-heading.compact {
  margin-bottom: 14px;
}

.logo-line {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-preview {
  width: 88px;
  height: 88px;
  display: grid;
  place-items: center;
  overflow: hidden;
  border: 1px dashed var(--rp-border-strong);
  border-radius: 8px;
  color: #64748b;
  font-size: 12px;
  background: #f4f8ff;
}

.logo-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hint {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 12px;
}

.audit-section {
  background: linear-gradient(180deg, #f7fbff, #fff);
}

.audit-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: var(--rp-primary-soft);
  color: #334155;
  font-weight: 650;
}

.audit-copy {
  min-height: 72px;
  margin: 14px 0 18px;
  color: #64748b;
  line-height: 1.7;
}

.save-button {
  width: 100%;
  height: 42px;
  font-weight: 650;
}

@media (max-width: 980px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .logo-line {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
