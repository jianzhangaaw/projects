<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { OfficeBuilding, School } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  password: '',
  role: 'STUDENT',
  email: '',
  phone: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
}

const roleOptions = [
  { label: '学生', value: 'STUDENT', desc: '搜索职位，投递简历', icon: School },
  { label: '企业', value: 'COMPANY', desc: '发布岗位，招募人才', icon: OfficeBuilding },
]

async function submit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    await auth.register(form)
    ElMessage.success('注册成功')
    await router.replace('/login')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-shell">
      <div class="brand-row">
        <div class="brand-mark">聘</div>
        <span>招聘简历平台</span>
      </div>

      <div class="scene-panel">
        <div class="campus-visual">
          <div class="tower"></div>
          <div class="student-card one"></div>
          <div class="student-card two"></div>
        </div>
        <h2>开启高校招聘协同之旅</h2>
        <p>连接学生、企业与审核管理，让职位发布、简历投递和审核反馈都更清晰。</p>
      </div>

      <el-card class="auth-card" shadow="never">
        <div class="card-heading">
          <h1>注册账号</h1>
          <p>选择您的角色，开启高校招聘 / 求职之旅</p>
        </div>

        <div class="role-grid">
          <button
            v-for="role in roleOptions"
            :key="role.value"
            type="button"
            class="role-card"
            :class="{ active: form.role === role.value }"
            @click="form.role = role.value"
          >
            <el-icon><component :is="role.icon" /></el-icon>
            <strong>{{ role.label }}</strong>
            <span>{{ role.desc }}</span>
          </button>
        </div>

        <el-form ref="formRef" :rules="rules" :model="form" label-position="top" @submit.prevent="submit">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
          </el-form-item>
          <el-button type="primary" :loading="loading" class="submit" @click="submit">注册</el-button>
        </el-form>
        <p class="register-trust-note">管理员账号由平台预置，请使用已有管理员账号登录。</p>
        <div class="switch">
          <span>已有账号？</span>
          <RouterLink to="/login">去登录</RouterLink>
        </div>
      </el-card>
    </section>
  </main>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 14% 18%, rgba(96, 165, 250, 0.16), transparent 30%),
    radial-gradient(circle at 84% 10%, rgba(37, 99, 235, 0.1), transparent 26%),
    linear-gradient(135deg, #f1f5fb 0%, #f8faff 52%, #ffffff 100%);
}

.auth-shell {
  width: min(1180px, 100%);
  min-height: 650px;
  display: grid;
  grid-template-columns: minmax(320px, 0.95fr) minmax(420px, 1.05fr);
  gap: 28px;
  position: relative;
}

.brand-row {
  position: absolute;
  top: 22px;
  left: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 750;
  color: #102033;
  z-index: 2;
}

.brand-mark {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #fff;
  background: var(--rp-navy);
  box-shadow: 0 10px 20px rgba(16, 42, 86, 0.18);
}

.scene-panel {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  min-height: 100%;
  padding: 96px 44px 54px;
  border: 1px solid var(--rp-border);
  border-radius: var(--rp-radius-lg);
  background:
    linear-gradient(180deg, rgba(239, 246, 255, 0.2), rgba(219, 234, 254, 0.86)),
    #f7fbff;
  box-shadow: var(--rp-shadow);
  overflow: hidden;
}

.campus-visual {
  position: relative;
  height: 280px;
  margin-bottom: 24px;
}

.tower {
  position: absolute;
  left: 16%;
  bottom: 0;
  width: 120px;
  height: 220px;
  border-radius: 60px 60px 8px 8px;
  background: linear-gradient(180deg, rgba(147, 197, 253, 0.42), rgba(37, 99, 235, 0.08));
}

.tower::before {
  content: '';
  position: absolute;
  left: 34px;
  top: -66px;
  border-left: 26px solid transparent;
  border-right: 26px solid transparent;
  border-bottom: 72px solid rgba(37, 99, 235, 0.18);
}

.student-card {
  position: absolute;
  bottom: 4px;
  width: 118px;
  height: 150px;
  border-radius: 26px 26px 8px 8px;
  background: linear-gradient(180deg, #dbeafe, #fff);
  border: 1px solid #bfdbfe;
  box-shadow: 0 16px 30px rgba(37, 99, 235, 0.12);
}

.student-card::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 36px;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: #93c5fd;
}

.student-card.one {
  left: 44%;
}

.student-card.two {
  left: 68%;
  width: 100px;
  height: 128px;
  background: linear-gradient(180deg, #eff6ff, #fff);
}

.scene-panel h2 {
  margin: 0;
  color: #0f2a5f;
  font-size: 30px;
  line-height: 1.25;
}

.scene-panel p {
  max-width: 430px;
  margin: 12px 0 0;
  color: #516579;
  line-height: 1.8;
}

.auth-card {
  align-self: center;
  width: 100%;
  border-radius: var(--rp-radius-md);
  border-color: var(--rp-border);
  box-shadow: var(--rp-shadow);
}

.card-heading {
  text-align: center;
}

h1 {
  margin: 0;
  font-size: 28px;
  color: #0f1f35;
}

.card-heading p {
  margin: 8px 0 24px;
  color: #64748b;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.role-card {
  min-height: 118px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--rp-border);
  border-radius: var(--rp-radius-md);
  background: #fff;
  color: #334155;
  cursor: pointer;
  transition: 0.18s ease;
}

.role-card .el-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 22px;
  color: var(--rp-primary);
  background: var(--rp-primary-soft);
}

.role-card strong {
  font-size: 15px;
}

.role-card span {
  color: #64748b;
  font-size: 12px;
}

.role-card.active {
  border-color: var(--rp-primary);
  background: #f7fbff;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.submit {
  width: 100%;
  height: 42px;
  font-weight: 650;
}

.register-trust-note {
  margin: 14px 0 0;
  color: var(--rp-muted);
  font-size: 12px;
  line-height: 1.6;
  text-align: center;
}

.switch {
  margin-top: 18px;
  display: flex;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  color: #6b7280;
}

.switch a {
  color: var(--rp-primary);
  font-weight: 650;
}

@media (max-width: 900px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }

  .scene-panel {
    min-height: 320px;
  }
}

@media (max-width: 560px) {
  .role-grid {
    grid-template-columns: 1fr;
  }

  .auth-shell {
    min-height: auto;
  }

  .scene-panel {
    display: none;
  }

  .brand-row {
    position: static;
    margin-bottom: 16px;
  }
}
</style>
