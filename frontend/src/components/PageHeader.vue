<template>
  <div class="flex flex-col gap-4 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
    <div class="min-w-0">
      <h1 class="text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
        {{ title }}
      </h1>
      <p v-if="subtitle" class="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="flex flex-shrink-0 items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>
