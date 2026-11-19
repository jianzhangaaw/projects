<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const roleHome: Record<string, string> = {
  STUDENT: '/student/jobs',
  COMPANY: '/company/dashboard',
  ADMIN: '/admin/reviews',
}

async function submit() {
  loading.value = true
  try {
    const session = await auth.login(form)
    ElMessage.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    await router.replace(redirect || roleHome[String(session.role)] || '/student/jobs')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-panel">
      <div class="auth-copy">
        <div class="brand-row">
          <div class="brand-mark">聘</div>
          <span>招聘简历平台</span>
        </div>
        <h1>招聘简历平台</h1>
        <p>让学生求职、企业招聘、平台审核在同一个清晰工作台里完成。</p>
        <div class="copy-metrics">
          <div><strong>岗位</strong><span>精准发布</span></div>
          <div><strong>简历</strong><span>高效流转</span></div>
          <div><strong>审核</strong><span>实时反馈</span></div>
        </div>
        <ul class="auth-trust-list" aria-label="平台服务特点">
          <li>角色权限清晰，数据按端隔离</li>
          <li>简历、投递与审核状态实时可追溯</li>
        </ul>
      </div>
      <el-card class="auth-card" shadow="never">
        <h2>欢迎登录</h2>
        <el-form label-position="top" @submit.prevent="submit">
          <el-form-item label="用户名">
            <el-input v-model="form.username" autocomplete="username" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" autocomplete="current-password" show-password />
          </el-form-item>
          <el-button type="primary" :loading="loading" class="submit" @click="submit">登录</el-button>
        </el-form>
        <div class="switch">
          <span>还没有账号</span>
          <RouterLink to="/register">去注册</RouterLink>
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

.auth-panel {
  width: min(960px, 100%);
  display: grid;
  grid-template-columns: 1fr 380px;
  align-items: center;
  gap: 42px;
  padding: 42px;
  border: 1px solid rgba(219, 231, 246, 0.52);
  border-radius: var(--rp-radius-lg);
  background: rgba(255, 255, 255, 0.56);
  box-shadow: 0 24px 60px rgba(16, 42, 86, 0.16);
  backdrop-filter: blur(14px);
}

.auth-copy {
  color: #102033;
}

.brand-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 44px;
  font-weight: 750;
}

.brand-mark {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--rp-navy);
  color: #fff;
  box-shadow: 0 10px 22px rgba(16, 42, 86, 0.18);
}

.auth-copy h1 {
  margin: 0;
  font-size: 44px;
  line-height: 1.15;
  text-wrap: balance;
}

.auth-copy p {
  margin-top: 16px;
  max-width: 460px;
  color: #516579;
  font-size: 16px;
  line-height: 1.8;
}

.copy-metrics {
  display: flex;
  gap: 12px;
  margin-top: 34px;
}

.copy-metrics div {
  min-width: 104px;
  padding: 14px;
  border: 1px solid rgba(188, 210, 245, 0.9);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.62);
}

.copy-metrics strong,
.copy-metrics span {
  display: block;
}

.copy-metrics strong {
  font-size: 18px;
}

.copy-metrics span {
  margin-top: 4px;
  color: #64748b;
  font-size: 12px;
}

.auth-trust-list {
  display: grid;
  gap: 8px;
  padding: 0;
  margin: 26px 0 0;
  color: #53647c;
  font-size: 13px;
  list-style: none;
}

.auth-trust-list li { display: flex; align-items: center; gap: 8px; }
.auth-trust-list li::before {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--rp-accent);
  content: '';
}

.auth-card {
  border-radius: var(--rp-radius-md);
  border-color: var(--rp-border);
  box-shadow: var(--rp-shadow);
}

.auth-card h2 {
  margin: 0 0 22px;
  font-size: 24px;
}

.submit {
  width: 100%;
  height: 42px;
  font-weight: 650;
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

@media (max-width: 820px) {
  .auth-panel {
    grid-template-columns: 1fr;
    padding: 26px;
  }

  .auth-copy h1 {
    font-size: 30px;
  }

  .copy-metrics {
    flex-wrap: wrap;
  }
}
</style>
