import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const source = (path) => readFile(new URL(path, import.meta.url), 'utf8').catch(() => '')

test('student jobs provides a selectable master-detail experience', async () => {
  const [page, detail] = await Promise.all([
    source('../src/views/student/StudentJobs.vue'),
    source('../src/views/student/components/JobDetailPanel.vue'),
  ])

  for (const hook of [
    'selectedJobId',
    'selectedJob',
    'selectJob',
    'loadSequence',
    'requestId !== loadSequence',
    'job-browser',
    'job-list-column',
    'job-detail-column',
    'job-detail-drawer',
  ]) {
    assert.match(page, new RegExp(hook))
  }

  for (const content of [
    '职位描述',
    '任职要求',
    '企业信息',
    '企业暂未填写职位描述',
    'companyName',
    'industry',
    'companySize',
  ]) {
    assert.match(detail, new RegExp(content))
  }

  assert.doesNotMatch(page, /热门企业/)
  assert.doesNotMatch(page, /职位类别<\/div>/)
  assert.match(page, /title="岗位详情"/)
  assert.doesNotMatch(page, /:with-header="false"/)
  assert.match(page, /color:\s*#f97316/)
  assert.match(detail, /color:\s*#f97316/)
})
