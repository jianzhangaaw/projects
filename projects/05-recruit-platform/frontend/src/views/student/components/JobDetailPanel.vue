<script setup lang="ts">
import { computed } from 'vue'
import { Briefcase, Location, OfficeBuilding, School, View } from '@element-plus/icons-vue'

import type { Job } from '@/types/api'

const props = defineProps<{
  job: Job | null
}>()

const emit = defineEmits<{
  apply: [job: Job]
}>()

const companyInitial = computed(() => {
  return (props.job?.companyName || props.job?.jobName || '企').charAt(0)
})

const skillTags = computed(() => {
  return (props.job?.skillRequirement || '')
    .split(/[,，、]/)
    .map((item) => item.trim())
    .filter(Boolean)
})
</script>

<template>
  <section v-if="job" class="job-detail-panel">
    <header class="detail-header">
      <div class="detail-heading">
        <div class="detail-title-row">
          <h2>{{ job.jobName || '未命名职位' }}</h2>
          <strong>{{ job.salaryRange || '薪资面议' }}</strong>
        </div>
        <p>{{ job.companyName || '优质企业' }}</p>
      </div>
      <el-tag type="success" effect="light" round>正在招聘</el-tag>
    </header>

    <div class="detail-meta" aria-label="岗位基本信息">
      <span><el-icon><Location /></el-icon>{{ job.city || '城市不限' }}</span>
      <span><el-icon><Briefcase /></el-icon>{{ job.jobType || '类别不限' }}</span>
      <span><el-icon><School /></el-icon>{{ job.educationRequirement || '学历不限' }}</span>
      <span><el-icon><View /></el-icon>{{ job.viewCount || 0 }} 次浏览</span>
    </div>

    <div class="detail-content">
      <section class="detail-section">
        <div class="section-heading">
          <span>01</span>
          <h3>职位描述</h3>
        </div>
        <p class="job-description">{{ job.description?.trim() || '企业暂未填写职位描述' }}</p>
      </section>

      <section class="detail-section">
        <div class="section-heading">
          <span>02</span>
          <h3>任职要求</h3>
        </div>
        <div class="requirement-grid">
          <article class="requirement-item">
            <small>专业要求</small>
            <strong>{{ job.majorRequirement || '专业不限' }}</strong>
          </article>
          <article class="requirement-item">
            <small>学历要求</small>
            <strong>{{ job.educationRequirement || '学历不限' }}</strong>
          </article>
        </div>
        <div class="skill-block">
          <small>技能要求</small>
          <div v-if="skillTags.length" class="skill-tags">
            <el-tag v-for="tag in skillTags" :key="tag" effect="plain">{{ tag }}</el-tag>
          </div>
          <p v-else>暂未填写技能要求</p>
        </div>
      </section>

      <section class="detail-section company-section">
        <div class="section-heading">
          <span>03</span>
          <h3>企业信息</h3>
        </div>
        <div class="company-profile">
          <div class="company-logo" aria-hidden="true">{{ companyInitial }}</div>
          <div class="company-copy">
            <strong>{{ job.companyName || '优质企业' }}</strong>
            <p>
              <span><el-icon><OfficeBuilding /></el-icon>{{ job.industry || '行业暂未填写' }}</span>
              <span>{{ job.companySize || '规模暂未填写' }}</span>
            </p>
          </div>
        </div>
      </section>
    </div>

    <footer class="detail-footer">
      <div>
        <strong>对这个岗位感兴趣？</strong>
        <span>选择你的简历，向企业发起投递</span>
      </div>
      <el-button type="primary" size="large" @click="emit('apply', job)">立即投递</el-button>
    </footer>
  </section>

  <section v-else class="job-detail-empty">
    <el-empty description="请选择左侧岗位查看招聘详情" />
  </section>
</template>

<style scoped>
.job-detail-panel,
.job-detail-empty {
  border: 1px solid var(--rp-border);
  border-radius: var(--rp-radius-md);
  background: var(--rp-surface);
}

.job-detail-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.job-detail-empty {
  display: grid;
  min-height: 240px;
  place-items: center;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 24px 26px 20px;
  background: #f7faff;
}

.detail-heading {
  min-width: 0;
}

.detail-title-row {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 12px 18px;
}

.detail-title-row h2 {
  margin: 0;
  color: var(--rp-navy-strong);
  font-size: 24px;
  line-height: 1.35;
}

.detail-title-row strong {
  color: #f97316;
  font-size: 21px;
  white-space: nowrap;
}

.detail-heading p {
  margin: 9px 0 0;
  color: var(--rp-muted);
  font-size: 14px;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 22px;
  padding: 14px 26px;
  border-top: 1px solid #eaf0f8;
  border-bottom: 1px solid var(--rp-border);
  color: #52647d;
  background: #fbfdff;
  font-size: 13px;
}

.detail-meta span,
.company-copy p span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.detail-meta .el-icon,
.company-copy .el-icon {
  color: var(--rp-primary);
}

.detail-content {
  flex: 1;
  padding: 8px 26px 24px;
  overflow-y: auto;
}

.detail-section {
  padding: 22px 0;
}

.detail-section + .detail-section {
  border-top: 1px solid #e8eef6;
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.section-heading span {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 7px;
  color: var(--rp-primary);
  background: var(--rp-primary-soft);
  font-size: 11px;
  font-weight: 800;
}

.section-heading h3 {
  margin: 0;
  color: var(--rp-navy-strong);
  font-size: 17px;
}

.job-description {
  margin: 0;
  color: #3d4f68;
  font-size: 14px;
  line-height: 1.9;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.requirement-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.requirement-item,
.skill-block {
  border: 1px solid #e4ebf5;
  border-radius: var(--rp-radius-sm);
  background: var(--rp-surface-muted);
}

.requirement-item {
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 14px;
}

.requirement-item small,
.skill-block > small {
  color: var(--rp-muted);
  font-size: 12px;
}

.requirement-item strong {
  color: #273b59;
  font-size: 14px;
}

.skill-block {
  padding: 14px;
  margin-top: 12px;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.skill-block p {
  margin: 8px 0 0;
  color: #52647d;
  font-size: 14px;
}

.company-profile {
  display: flex;
  align-items: center;
  gap: 14px;
}

.company-logo {
  display: grid;
  width: 52px;
  height: 52px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 12px;
  color: #fff;
  background: var(--rp-primary);
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.18);
  font-size: 20px;
  font-weight: 800;
}

.company-copy {
  min-width: 0;
}

.company-copy > strong {
  color: var(--rp-navy-strong);
  font-size: 16px;
}

.company-copy p {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin: 8px 0 0;
  color: var(--rp-muted);
  font-size: 13px;
}

.detail-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px 26px;
  border-top: 1px solid var(--rp-border);
  background: #fff;
  box-shadow: 0 -10px 24px rgba(16, 42, 86, 0.05);
}

.detail-footer > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.detail-footer strong {
  color: var(--rp-navy-strong);
  font-size: 14px;
}

.detail-footer span {
  color: var(--rp-muted);
  font-size: 12px;
}

.detail-footer .el-button {
  min-width: 120px;
}

@media (max-width: 640px) {
  .job-detail-panel,
  .job-detail-empty {
    min-height: calc(100vh - 24px);
    border: 0;
  }

  .detail-header,
  .detail-content,
  .detail-meta,
  .detail-footer {
    padding-right: 18px;
    padding-left: 18px;
  }

  .detail-title-row h2 {
    font-size: 21px;
  }

  .requirement-grid {
    grid-template-columns: 1fr;
  }

  .detail-footer {
    position: sticky;
    bottom: 0;
  }

  .detail-footer > div {
    display: none;
  }

  .detail-footer .el-button {
    width: 100%;
  }
}
</style>
