<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Upload } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'

import { getFileResource, uploadFile } from '@/api/files'
import { getMyProfile, updateMyProfile } from '@/api/student'
import ModuleCard from '@/components/ModuleCard.vue'
import type { StudentProfile } from '@/types/api'

const loading = ref(false)
const saving = ref(false)
const avatarUploading = ref(false)
const avatarUrl = ref('')
const formRef = ref<FormInstance>()

const form = reactive<StudentProfile>({
  realName: '',
  gender: '',
  age: undefined,
  hometown: '',
  politicalStatus: '',
  phone: '',
  email: '',
  wechat: '',
  qq: '',
  school: '',
  major: '',
  educationLevel: '',
  gpa: '',
  graduationDate: '',
  expectedPosition: '',
  expectedCity: '',
  expectedSalary: '',
  selfIntro: '',
  avatarFileId: undefined,
})

const completion = computed(() => {
  const keys: Array<keyof StudentProfile> = [
    'realName',
    'phone',
    'email',
    'school',
    'major',
    'educationLevel',
    'graduationDate',
    'expectedPosition',
    'expectedCity',
    'selfIntro',
  ]
  const filled = keys.filter((key) => Boolean(String(form[key] ?? '').trim())).length
  return Math.round((filled / keys.length) * 100)
})

function assignProfile(profile: StudentProfile) {
  Object.assign(form, {
    ...profile,
    graduationDate: profile.graduationDate || '',
  })
}

async function load() {
  loading.value = true
  try {
    const profile = await getMyProfile()
    assignProfile(profile || {})
    if (profile?.avatarFileId) {
      const file = await getFileResource(profile.avatarFileId)
      avatarUrl.value = file.fileUrl || ''
    } else {
      avatarUrl.value = ''
    }
  } finally {
    loading.value = false
  }
}

const rules = {
  realName: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
  ],
}

async function save() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const saved = await updateMyProfile({ ...form })
    assignProfile(saved)
    ElMessage.success('个人信息已保存')
  } finally {
    saving.value = false
  }
}

async function onAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  avatarUploading.value = true
  try {
    const uploaded = await uploadFile(file, 'AVATAR')
    form.avatarFileId = uploaded.id
    avatarUrl.value = uploaded.fileUrl
    ElMessage.success('头像已上传，保存资料后生效')
  } finally {
    avatarUploading.value = false
  }
}

onMounted(load)
</script>

<template>
  <ModuleCard title="个人信息" subtitle="维护基础资料、教育背景和求职意向">
    <template #actions>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存资料</el-button>
    </template>

    <div v-loading="loading" class="profile-layout">
      <aside class="profile-side">
        <div class="avatar-box">
          <el-avatar :src="avatarUrl" :size="76">
            {{ form.realName?.charAt(0) || '学' }}
          </el-avatar>
          <strong>{{ form.realName || '未填写姓名' }}</strong>
          <span>{{ form.school || '学校待完善' }} · {{ form.major || '专业待完善' }}</span>
          <label class="upload-trigger">
            <el-icon><Upload /></el-icon>
            <span>{{ avatarUploading ? '上传中...' : '上传头像' }}</span>
            <input type="file" accept=".jpg,.jpeg,.png" :disabled="avatarUploading" @change="onAvatarChange" />
          </label>
        </div>

        <div class="completion-card">
          <div class="completion-head">
            <span>资料完善度</span>
            <strong>{{ completion }}%</strong>
          </div>
          <el-progress :percentage="completion" :show-text="false" />
          <p>完善联系方式、教育背景和求职意向后，企业查看简历时信息更完整。</p>
        </div>
      </aside>

      <el-form ref="formRef" :rules="rules" class="profile-form" :model="form" label-width="96px">
        <section class="form-section">
          <h3>基本信息</h3>
          <div class="form-grid">
            <el-form-item label="姓名" prop="realName">
              <el-input v-model="form.realName" placeholder="请输入真实姓名" />
            </el-form-item>
            <el-form-item label="性别">
              <el-select v-model="form.gender" clearable placeholder="请选择">
                <el-option label="男" value="MALE" />
                <el-option label="女" value="FEMALE" />
              </el-select>
            </el-form-item>
            <el-form-item label="年龄">
              <el-input-number v-model="form.age" :min="16" :max="60" controls-position="right" />
            </el-form-item>
            <el-form-item label="籍贯">
              <el-input v-model="form.hometown" placeholder="如：浙江杭州" />
            </el-form-item>
            <el-form-item label="政治面貌">
              <el-input v-model="form.politicalStatus" placeholder="如：共青团员" />
            </el-form-item>
          </div>
        </section>

        <section class="form-section">
          <h3>联系方式</h3>
          <div class="form-grid">
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" placeholder="请输入手机号" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="微信">
              <el-input v-model="form.wechat" placeholder="请输入微信号" />
            </el-form-item>
            <el-form-item label="QQ">
              <el-input v-model="form.qq" placeholder="请输入 QQ" />
            </el-form-item>
          </div>
        </section>

        <section class="form-section">
          <h3>教育背景</h3>
          <div class="form-grid">
            <el-form-item label="学校">
              <el-input v-model="form.school" placeholder="请输入学校" />
            </el-form-item>
            <el-form-item label="专业">
              <el-input v-model="form.major" placeholder="请输入专业" />
            </el-form-item>
            <el-form-item label="学历">
              <el-select v-model="form.educationLevel" clearable placeholder="请选择学历">
                <el-option label="专科" value="专科" />
                <el-option label="本科" value="本科" />
                <el-option label="硕士" value="硕士" />
                <el-option label="博士" value="博士" />
              </el-select>
            </el-form-item>
            <el-form-item label="GPA">
              <el-input v-model="form.gpa" placeholder="如：3.8/4.0" />
            </el-form-item>
            <el-form-item label="毕业时间">
              <el-date-picker v-model="form.graduationDate" type="date" value-format="YYYY-MM-DD" placeholder="请选择" />
            </el-form-item>
          </div>
        </section>

        <section class="form-section">
          <h3>求职意向</h3>
          <div class="form-grid">
            <el-form-item label="期望岗位">
              <el-input v-model="form.expectedPosition" placeholder="如：Java 后端开发" />
            </el-form-item>
            <el-form-item label="期望城市">
              <el-input v-model="form.expectedCity" placeholder="如：杭州、上海" />
            </el-form-item>
            <el-form-item label="期望薪资">
              <el-input v-model="form.expectedSalary" placeholder="如：12K-18K" />
            </el-form-item>
          </div>
          <el-form-item label="个人简介">
            <el-input v-model="form.selfIntro" type="textarea" :rows="5" placeholder="简要介绍你的能力、方向和优势" />
          </el-form-item>
        </section>
      </el-form>
    </div>
  </ModuleCard>
</template>

<style scoped>
.profile-layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 18px;
}

.profile-side {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.avatar-box,
.completion-card,
.form-section {
  border: 1px solid var(--rp-border);
  border-radius: 8px;
  background: #fff;
}

.avatar-box {
  display: flex;
  align-items: center;
  flex-direction: column;
  gap: 10px;
  padding: 22px 16px;
  text-align: center;
}

.avatar-box strong {
  color: #0f1f35;
  font-size: 17px;
}

.avatar-box span,
.completion-card p {
  color: var(--rp-muted);
  font-size: 13px;
}

.upload-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--rp-primary);
  cursor: pointer;
  font-size: 13px;
}

.upload-trigger input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.completion-card {
  padding: 16px;
}

.completion-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  color: #334155;
}

.profile-form {
  min-width: 0;
}

.form-section {
  padding: 18px 18px 4px;
  margin-bottom: 14px;
}

.form-section h3 {
  margin: 0 0 16px;
  color: #0f1f35;
  font-size: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 16px;
}

@media (max-width: 900px) {
  .profile-layout,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
