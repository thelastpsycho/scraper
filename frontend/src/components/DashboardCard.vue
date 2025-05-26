<template>
  <div class="bg-white overflow-hidden shadow rounded-lg w-full h-full">
    <div class="p-5">
      <div class="flex items-center">
        <div class="flex-shrink-0">
          <component 
            :is="icon" 
            class="h-6 w-6 text-gray-400" 
            aria-hidden="true"
          />
        </div>
        <div class="ml-5 w-0 flex-1">
          <dl>
            <dt class="text-sm font-medium text-gray-500 truncate">
              {{ title }}
            </dt>
            <dd class="flex items-baseline">
              <div class="text-2xl font-semibold text-gray-900">
                {{ value }}
              </div>
              <div 
                v-if="change" 
                :class="[
                  change > 0 ? 'text-green-600' : 'text-red-600',
                  'ml-2 flex items-baseline text-sm font-semibold'
                ]"
              >
                {{ change > 0 ? '↑' : '↓' }} {{ Math.abs(change) }}%
              </div>
            </dd>
          </dl>
        </div>
      </div>
    </div>
    <div v-if="footer" class="bg-gray-50 px-5 py-3">
      <div class="text-sm">
        <a :href="footerLink" class="font-medium text-indigo-600 hover:text-indigo-500">
          {{ footer }}
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  icon: any
  change?: number
  footer?: string
  footerLink?: string
}>()
</script> 