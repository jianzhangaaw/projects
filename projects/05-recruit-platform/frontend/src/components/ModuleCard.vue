<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<template>
  <section class="page module-card">
    <div class="page-header module-card__header">
      <div>
        <h1 class="page-title">{{ title }}</h1>
        <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="module-card__actions">
        <slot name="actions" />
      </div>
    </div>
    <div class="panel module-card__panel">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.module-card__header { padding: 2px 2px 0; }
.module-card__actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 10px; }
.module-card__panel { min-width: 0; }

@media (max-width: 768px) {
  .module-card__actions { width: 100%; justify-content: stretch; }
  .module-card__actions :deep(.el-button) { flex: 1 1 auto; }
}
</style>
