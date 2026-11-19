import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const source = (path) => readFile(new URL(path, import.meta.url), 'utf8')

test('core views expose reusable hierarchy hooks for the redesigned experience', async () => {
  const [layout, moduleCard, login, register, jobs, resumes, companyDashboard] = await Promise.all([
    source('../src/layouts/DashboardLayout.vue'),
    source('../src/components/ModuleCard.vue'),
    source('../src/views/auth/LoginView.vue'),
    source('../src/views/auth/RegisterView.vue'),
    source('../src/views/student/StudentJobs.vue'),
    source('../src/views/student/StudentResumes.vue'),
    source('../src/views/company/CompanyDashboard.vue'),
  ])

  for (const [content, hook] of [
    [layout, 'topbar-context'],
    [moduleCard, 'module-card__header'],
    [login, 'auth-trust-list'],
    [register, 'register-trust-note'],
    [jobs, 'job-result-summary'],
    [resumes, 'resume-action-bar'],
    [companyDashboard, 'dashboard-intro'],
  ]) {
    assert.match(content, new RegExp(hook))
  }

  assert.doesNotMatch(register, /value: 'ADMIN'/)
  assert.match(resumes, /resume-row-actions/)

  for (const content of [layout, login, register]) {
    assert.match(content, /招聘简历平台/)
    assert.doesNotMatch(content, /校园招聘智能简历平台/)
  }
})
