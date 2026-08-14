<template>
  <div class="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-5 transition-colors hover:border-slate-300">
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <dt class="truncate text-xs font-medium uppercase tracking-widest text-slate-400">{{ title }}</dt>
        <dd class="mt-3 flex items-baseline gap-2">
          <span class="text-2xl font-semibold tracking-tight text-slate-900">{{ value }}</span>
          <span
            v-if="change !== undefined"
            :class="[
              change >= 0 ? 'text-emerald-600' : 'text-rose-600',
              'inline-flex items-center text-sm font-medium',
            ]"
          >
            <component :is="change >= 0 ? ArrowUpRightIcon : ArrowDownRightIcon" class="h-4 w-4" />
            {{ Math.abs(change) }}%
          </span>
        </dd>
      </div>
      <component :is="icon" class="h-5 w-5 flex-shrink-0 text-slate-400" aria-hidden="true" />
    </div>
    <div v-if="footer" class="mt-4 border-t border-slate-100 pt-3">
      <a :href="footerLink" class="inline-flex items-center gap-1 text-sm font-medium text-slate-600 hover:text-slate-900">
        {{ footer }}
        <ArrowRightIcon class="h-3.5 w-3.5" />
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowUpRightIcon, ArrowDownRightIcon, ArrowRightIcon } from '@heroicons/vue/24/outline'

defineProps<{
  title: string
  value: string | number
  icon: any
  change?: number
  footer?: string
  footerLink?: string
}>()
</script>
