import type { RouteRecordRaw } from 'vue-router'
import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import type { Role } from '@/types/api'

const roleHome: Record<string, string> = {
  STUDENT: '/student/jobs',
  COMPANY: '/company/dashboard',
  ADMIN: '/admin/reviews',
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: () => {
      const auth = useAuthStore()
      return auth.isLoggedIn ? roleHome[String(auth.role)] || '/student/jobs' : '/login'
    },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/student',
    component: () => import('@/layouts/DashboardLayout.vue'),
    meta: { roles: ['STUDENT'] satisfies Role[] },
    children: [
      { path: '', redirect: '/student/jobs' },
      { path: 'jobs', name: 'student-jobs', component: () => import('@/views/student/StudentJobs.vue') },
      {
        path: 'resumes',
        name: 'student-resumes',
        component: () => import('@/views/student/StudentResumes.vue'),
      },
      {
        path: 'profile',
        name: 'student-profile',
        component: () => import('@/views/student/StudentProfile.vue'),
      },
      {
        path: 'skills',
        name: 'student-skills',
        component: () => import('@/views/student/StudentSkills.vue'),
      },
      {
        path: 'experiences',
        name: 'student-experiences',
        component: () => import('@/views/student/StudentExperiences.vue'),
      },
      {
        path: 'applications',
        name: 'student-applications',
        component: () => import('@/views/student/StudentApplications.vue'),
      },
      {
        path: 'notifications',
        name: 'student-notifications',
        component: () => import('@/views/student/StudentNotifications.vue'),
      },
    ],
  },
  {
    path: '/company',
    component: () => import('@/layouts/DashboardLayout.vue'),
    meta: { roles: ['COMPANY'] satisfies Role[] },
    children: [
      { path: '', redirect: '/company/dashboard' },
      { path: 'dashboard', name: 'company-dashboard', component: () => import('@/views/company/CompanyDashboard.vue') },
      { path: 'jobs', name: 'company-jobs', component: () => import('@/views/company/CompanyJobs.vue') },
      { path: 'info', name: 'company-info', component: () => import('@/views/company/CompanyInfo.vue') },
      {
        path: 'applications',
        name: 'company-applications',
        component: () => import('@/views/company/CompanyApplications.vue'),
      },
      {
        path: 'notifications',
        name: 'company-notifications',
        component: () => import('@/views/company/CompanyNotifications.vue'),
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layouts/DashboardLayout.vue'),
    meta: { roles: ['ADMIN'] satisfies Role[] },
    children: [
      { path: '', redirect: '/admin/reviews' },
      { path: 'reviews', name: 'admin-reviews', component: () => import('@/views/admin/AdminReviews.vue') },
      { path: 'users', name: 'admin-users', component: () => import('@/views/admin/AdminUsers.vue') },
      {
        path: 'resume-templates',
        name: 'admin-resume-templates',
        component: () => import('@/views/admin/AdminResumeTemplates.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    return auth.isLoggedIn ? roleHome[String(auth.role)] || '/student/jobs' : true
  }
  if (!auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  const roles = to.matched.flatMap((record) => (record.meta.roles || []) as Role[])
  if (roles.length && !roles.includes(auth.role)) {
    return roleHome[String(auth.role)] || '/student/jobs'
  }
  return true
})

export default router
