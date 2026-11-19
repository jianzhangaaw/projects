<script setup lang="ts">
defineProps<{
  columns: string[]
}>()
</script>

<template>
  <el-table :data="[]" border height="360">
    <el-table-column v-for="column in columns" :key="column" :prop="column" :label="column" />
    <template #empty>
      <el-empty description="暂无数据" />
    </template>
  </el-table>
</template>
