import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const source = (path) => readFile(new URL(path, import.meta.url), 'utf8')

test('company job and application screens expose spacious layout hooks', async () => {
  const [jobs, applications, css] = await Promise.all([
    source('../src/views/company/CompanyJobs.vue'),
    source('../src/views/company/CompanyApplications.vue'),
    source('../src/style.css'),
  ])

  for (const [content, hook] of [
    [jobs, 'jobs-filter-panel'],
    [jobs, 'jobs-table-shell'],
    [jobs, 'job-row-actions'],
    [jobs, 'form-section'],
    [applications, 'applications-filter-panel'],
    [applications, 'application-job-card'],
    [applications, 'application-job-card__header'],
    [applications, 'application-job-card__toggle'],
    [applications, 'toggleGroup'],
    [applications, 'expandedGroups'],
    [applications, 'candidate-card-grid'],
    [applications, 'candidate-card'],
    [applications, 'candidate-card__actions'],
    [applications, 'application-pagination'],
    [applications, 'visibleItems'],
    [applications, 'pageByGroup'],
    [applications, 'applications-bulk-bar'],
  ]) {
    assert.match(content, new RegExp(hook))
  }

  assert.match(css, /--rp-control-height: 44px/)
  assert.match(css, /\.el-form-item/)
  assert.match(applications, /substring\(0, 16\)/)
  assert.match(applications, /updateApplicationStatus/)
  assert.match(applications, /viewResume/)
  assert.match(applications, /PAGE_SIZE = 8/)
  assert.match(applications, /current-page/)
  assert.match(applications, /resetPageState/)
  assert.doesNotMatch(applications, /<el-table\b/)
  assert.match(css, /backdrop-filter: blur\(/)
  assert.match(css, /\.candidate-card-grid\s*\{/)
})
