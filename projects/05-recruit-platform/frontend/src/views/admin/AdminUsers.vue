<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { listUsers, updateUserStatus, type UserListParams } from '@/api/admin'
import ModuleCard from '@/components/ModuleCard.vue'
import type { Role, UserAccount } from '@/types/api'

const loading = ref(false)
const users = ref<UserAccount[]>([])
const total = ref(0)

const roleOptions: { label: string; value: Role }[] = [
  { label: '全部角色', value: '' as Role },
  { label: '管理员', value: 'ADMIN' },
  { label: '企业', value: 'COMPANY' },
  { label: '学生', value: 'STUDENT' },
]

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '启用', value: 'ENABLED' },
  { label: '禁用', value: 'DISABLED' },
]

const filters = reactive<UserListParams>({
  current: 1,
  size: 10,
  username: '',
  role: '',
  status: '',
})

async function load() {
  loading.value = true
  try {
    const page = await listUsers({
      current: filters.current,
      size: filters.size,
      username: filters.username || undefined,
      role: filters.role || undefined,
      status: filters.status || undefined,
    })
    users.value = page.records || []
    total.value = page.total || 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  filters.current = 1
  load()
}

function onReset() {
  filters.username = ''
  filters.role = ''
  filters.status = ''
  filters.current = 1
  load()
}

function onPageChange(current: number) {
  filters.current = current
  load()
}

function onSizeChange(size: number) {
  filters.size = size
  filters.current = 1
  load()
}

type StatusTag = { type: 'success' | 'info' | 'danger'; text: string }

function statusTag(status?: string): StatusTag {
  if (status === 'ENABLED') return { type: 'success', text: '启用' }
  if (status === 'DISABLED') return { type: 'danger', text: '禁用' }
  return { type: 'info', text: status || '未知' }
}

const roleText: Record<Role, string> = {
  ADMIN: '管理员',
  COMPANY: '企业',
  STUDENT: '学生',
}

async function toggleStatus(row: UserAccount, target: 'ENABLED' | 'DISABLED') {
  if (!row.id) return
  const actionText = target === 'DISABLED' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确定要${actionText}账号「${row.username}」吗？`,
      `${actionText}确认`,
      { type: 'warning', confirmButtonText: actionText, cancelButtonText: '取消' },
    )
  } catch {
    return // 用户取消
  }
  await updateUserStatus(row.id, target)
  ElMessage.success(`已${actionText}账号「${row.username}」`)
  load()
}

onMounted(load)
</script>

<template>
  <ModuleCard title="用户管理" subtitle="查看和管理用户账号">
    <template #actions>
      <el-button type="primary" @click="load">刷新</el-button>
    </template>

    <el-form :inline="true" :model="filters" class="filter-bar" @submit.prevent>
      <el-form-item label="用户名">
        <el-input v-model="filters.username" placeholder="支持模糊搜索" clearable @keyup.enter="onSearch" />
      </el-form-item>
      <el-form-item label="角色">
        <el-select v-model="filters.role" placeholder="全部角色" clearable style="width: 140px">
          <el-option v-for="opt in roleOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 140px">
          <el-option v-for="opt in statusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="users" border height="420">
      <el-table-column prop="username" label="用户名" min-width="160" />
      <el-table-column label="关联对象" min-width="200">
        <template #default="{ row }">
          <template v-if="row.associatedName">{{ row.associatedName }}</template>
          <span v-else style="color:#94a3b8">未完善</span>
        </template>
      </el-table-column>
      <el-table-column label="角色" width="120">
        <template #default="{ row }">{{ roleText[row.role as Role] || row.role }}</template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status).type">{{ statusTag(row.status).text }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
      <el-table-column prop="createdAt" label="创建时间" min-width="160" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status !== 'ENABLED'"
            type="primary"
            link
            @click="toggleStatus(row, 'ENABLED')"
          >启用</el-button>
          <el-button
            v-else
            type="danger"
            link
            @click="toggleStatus(row, 'DISABLED')"
          >禁用</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      :current-page="filters.current"
      :page-size="filters.size"
      :page-sizes="[10, 20, 50]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      background
      @current-change="onPageChange"
      @size-change="onSizeChange"
    />
  </ModuleCard>
</template>

<style scoped>
.filter-bar {
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
