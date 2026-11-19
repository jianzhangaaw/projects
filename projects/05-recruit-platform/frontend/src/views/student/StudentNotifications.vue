<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { listNotifications, markAllNotificationsRead, markNotificationRead } from '@/api/notifications'
import type { Notification } from '@/types/api'

const loading = ref(false)
const notifications = ref<Notification[]>([])
const total = ref(0)
const current = ref(1)
const size = ref(10)

const typeLabel: Record<string, string> = {
  REVIEW: '审核通知',
  APPLICATION: '投递通知',
}

const typeTag: Record<string, 'warning' | 'primary' | ''> = {
  REVIEW: 'warning',
  APPLICATION: 'primary',
}

async function fetchNotifications() {
  loading.value = true
  try {
    const result = await listNotifications({ current: current.value, size: size.value })
    notifications.value = result.records
    total.value = result.total
  } finally {
    loading.value = false
  }
}

async function handleMarkRead(id: number) {
  await markNotificationRead(id)
  ElMessage.success('已标记为已读')
  fetchNotifications()
}

async function handleMarkAllRead() {
  await markAllNotificationsRead()
  ElMessage.success('全部已标记为已读')
  fetchNotifications()
}

function onPageChange(page: number) {
  current.value = page
  fetchNotifications()
}

onMounted(fetchNotifications)
</script>

<template>
  <div class="notifications-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon><Bell /></el-icon>
        消息通知
      </h2>
      <el-button text type="primary" :disabled="!notifications.length" @click="handleMarkAllRead">
        全部标为已读
      </el-button>
    </div>

    <el-table v-loading="loading" :data="notifications" stripe class="notify-table">
      <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
      <el-table-column prop="content" label="内容" min-width="280" show-overflow-tooltip />
      <el-table-column label="类型" width="110">
        <template #default="{ row }">
          <el-tag :type="typeTag[row.type] || 'info'" size="small">
            {{ typeLabel[row.type] || row.type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="时间" width="170">
        <template #default="{ row }">
          {{ row.createdAt?.replace('T', ' ').substring(0, 19) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.isRead ? 'info' : 'danger'" size="small">
            {{ row.isRead ? '已读' : '未读' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button v-if="!row.isRead" text type="primary" size="small" @click="handleMarkRead(row.id!)">
            标为已读
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="total > size" class="pagination-wrap">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="size"
        v-model:current-page="current"
        @current-change="onPageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.notifications-page {
  max-width: 1100px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 20px;
  font-weight: 650;
}

.notify-table {
  border-radius: 10px;
  overflow: hidden;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 22px;
}
</style>
