<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Bell,
  Briefcase,
  DataAnalysis,
  Document,
  Files,
  House,
  Menu,
  Medal,
  OfficeBuilding,
  SwitchButton,
  User,
  UserFilled,
} from '@element-plus/icons-vue'

import { getUnreadCount } from '@/api/notifications'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const mobileMenuVisible = ref(false)
let pollTimer: ReturnType<typeof setInterval> | undefined

const menus = computed(() => {
  const base = auth.role === 'ADMIN' ? [
    { path: '/admin/reviews', label: '审核中心', icon: UserFilled },
    { path: '/admin/users', label: '用户管理', icon: User },
    { path: '/admin/resume-templates', label: '模板管理', icon: Files },
  ] : auth.role === 'COMPANY' ? [
    { path: '/company/dashboard', label: '企业工作台', icon: DataAnalysis },
    { path: '/company/jobs', label: '职位管理', icon: Briefcase },
    { path: '/company/applications', label: '投递管理', icon: Document },
    { path: '/company/info', label: '企业信息', icon: OfficeBuilding },
    { path: '/company/notifications', label: '消息通知', icon: Bell, badge: true },
  ] : [
    { path: '/student/jobs', label: '职位大厅', icon: Briefcase },
    { path: '/student/resumes', label: '简历管理', icon: Document },
    { path: '/student/profile', label: '个人信息', icon: User },
    { path: '/student/skills', label: '技能管理', icon: Medal },
    { path: '/student/experiences', label: '经历管理', icon: Document },
    { path: '/student/applications', label: '我的投递', icon: House },
    { path: '/student/notifications', label: '消息通知', icon: Bell, badge: true },
  ]
  return base
})

const activeTitle = computed(() => menus.value.find((item) => item.path === route.path)?.label || '工作台')
const roleLabel = computed(() => ({ STUDENT: '学生端', COMPANY: '企业端', ADMIN: '管理端' })[auth.role] || '工作台')
async function fetchUnreadCount() {
  if (!auth.isLoggedIn || auth.role === 'ADMIN') return
  try {
    const count = await getUnreadCount()
    auth.setUnreadCount(count)
  } catch {
    // silently fail
  }
}

onMounted(() => {
  fetchUnreadCount()
  pollTimer = setInterval(fetchUnreadCount, 30000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

function navigate(path: string) {
  mobileMenuVisible.value = false
  if (route.path !== path) {
    router.push(path)
  }
}

function logout() {
  mobileMenuVisible.value = false
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <el-container class="dashboard">
    <el-aside class="sidebar" width="232px">
      <div class="brand">
        <div class="brand-mark">聘</div>
        <div class="brand-copy">
          <div class="brand-name">招聘简历平台</div>
          <div class="brand-subtitle">Resume Platform</div>
        </div>
      </div>
      <el-menu :default-active="route.path" class="menu" @select="navigate">
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
          <span v-if="item.badge && auth.unreadCount > 0" class="nav-badge">{{ auth.unreadCount > 99 ? '99+' : auth.unreadCount }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="workspace">
      <el-header class="topbar">
        <div class="mobile-brand">
          <div class="brand-mark brand-mark-small">聘</div>
          <span>招聘简历平台</span>
        </div>
        <div class="topbar-context">
          <span class="topbar-kicker">{{ roleLabel }}</span>
          <div class="topbar-title">{{ route.meta.title || activeTitle }}</div>
        </div>
        <div class="topbar-actions">
          <el-tag class="role-tag" effect="plain">{{ roleLabel }}</el-tag>
          <span class="username">{{ auth.username }}</span>
          <el-button :icon="SwitchButton" text class="logout-button" @click="logout">退出</el-button>
          <el-button
            :icon="Menu"
            circle
            class="menu-toggle"
            aria-label="打开导航"
            title="打开导航"
            @click="mobileMenuVisible = true"
          />
        </div>
      </el-header>
      <el-main class="content">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>

  <el-drawer v-model="mobileMenuVisible" direction="ltr" size="296px" :with-header="false" class="mobile-drawer">
    <div class="drawer-brand">
      <div class="brand-mark">聘</div>
      <div class="brand-copy">
        <div class="brand-name">招聘简历平台</div>
        <div class="brand-subtitle">{{ roleLabel }}</div>
      </div>
    </div>
    <el-menu :default-active="route.path" class="menu drawer-menu" @select="navigate">
      <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
        <span v-if="item.badge && auth.unreadCount > 0" class="nav-badge">{{ auth.unreadCount > 99 ? '99+' : auth.unreadCount }}</span>
      </el-menu-item>
    </el-menu>
    <div class="drawer-footer">
      <span class="username">{{ auth.username }}</span>
      <el-button :icon="SwitchButton" text @click="logout">退出登录</el-button>
    </div>
  </el-drawer>
</template>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: var(--rp-bg);
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  background: #fbfcff;
  border-right: 1px solid var(--rp-border);
  box-shadow: 10px 0 30px rgba(16, 42, 86, 0.05);
}

.workspace {
  min-width: 0;
}

.brand,
.drawer-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand {
  height: 76px;
  padding: 0 18px;
  border-bottom: 1px solid var(--rp-border);
}

.brand-mark {
  width: 38px;
  height: 38px;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 10px;
  background: var(--rp-navy);
  color: #fff;
  font-size: 20px;
  font-weight: 800;
  box-shadow: 0 8px 16px rgba(16, 42, 86, 0.18);
}

.brand-mark-small {
  width: 32px;
  height: 32px;
  font-size: 17px;
}

.brand-copy {
  min-width: 0;
}

.brand-name {
  overflow: hidden;
  color: #102033;
  font-size: 15px;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brand-subtitle {
  margin-top: 3px;
  color: #7a8da8;
  font-size: 12px;
}

.menu {
  padding: 12px 0;
  border-right: 0;
  background: transparent;
}

.menu :deep(.el-menu-item) {
  position: relative;
  height: 44px;
  margin: 4px 12px;
  padding: 0 12px !important;
  border-radius: 10px;
  color: #516579;
  line-height: 44px;
}

.menu :deep(.el-menu-item .el-icon) {
  margin-right: 10px;
  font-size: 17px;
}

.menu :deep(.el-menu-item.is-active),
.menu :deep(.el-menu-item:hover) {
  color: var(--rp-navy);
  background: #e8f0ff;
}

.menu :deep(.el-menu-item.is-active)::before {
  position: absolute;
  top: 10px;
  left: -12px;
  width: 3px;
  height: 24px;
  border-radius: 0 3px 3px 0;
  background: var(--rp-accent);
  content: '';
}

.topbar {
  height: 76px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 0 28px;
  border-bottom: 1px solid var(--rp-border);
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 5px 18px rgba(16, 42, 86, 0.04);
}

.mobile-brand,
.menu-toggle {
  display: none;
}

.topbar-context {
  min-width: 0;
}

.topbar-kicker {
  display: block;
  margin-bottom: 3px;
  color: #70809a;
  font-size: 11px;
  font-weight: 750;
  letter-spacing: 0.08em;
}

.topbar-title {
  min-width: 0;
  overflow: hidden;
  color: var(--rp-navy-strong);
  font-size: 17px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.role-tag {
  --el-tag-bg-color: var(--rp-primary-lighter);
  --el-tag-border-color: var(--rp-border-strong);
  --el-tag-text-color: var(--rp-primary);
}

.username {
  max-width: 144px;
  overflow: hidden;
  color: #475569;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-button {
  color: #516579;
}

.nav-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  margin-left: auto;
  padding: 0 5px;
  border-radius: 9px;
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.content {
  min-height: calc(100vh - 76px);
  padding: 24px 28px 32px;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.07), transparent 360px),
    var(--rp-bg);
}

.drawer-brand {
  height: 76px;
  padding: 0 18px;
  border-bottom: 1px solid var(--rp-border);
}

.drawer-menu {
  padding-top: 14px;
}

.drawer-footer {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--rp-border);
  background: #fff;
}

@media (max-width: 899px) {
  .sidebar {
    display: none;
  }

  .topbar {
    height: 64px;
    padding: 0 16px;
  }

  .mobile-brand {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 9px;
    color: #102033;
    font-size: 15px;
    font-weight: 750;
    white-space: nowrap;
  }

  .topbar-context,
  .role-tag,
  .username,
  .logout-button {
    display: none;
  }

  .menu-toggle {
    display: inline-flex;
  }

  .content {
    min-height: calc(100vh - 64px);
    padding: 16px;
  }
}
</style>
