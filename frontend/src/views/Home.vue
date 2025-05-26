<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div class="md:flex md:items-center md:justify-between">
      <div class="min-w-0 flex-1">
        <h2 class="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
          Dashboard
        </h2>
      </div>
      <div class="mt-4 flex md:ml-4 md:mt-0">
        <button
          type="button"
          class="w-full md:w-auto inline-flex items-center justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
        >
          New Scraping Job
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <DashboardCard
        title="Total Scraped Items"
        value="1,234"
        :change="12"
        :icon="DocumentIcon"
        footer="View all items"
        footerLink="#"
        class="h-full"
      />
      <DashboardCard
        title="Active Jobs"
        value="3"
        :change="-2"
        :icon="ClockIcon"
        footer="View active jobs"
        footerLink="#"
        class="h-full"
      />
      <DashboardCard
        title="Success Rate"
        value="98.5%"
        :change="0.5"
        :icon="ChartBarIcon"
        footer="View statistics"
        footerLink="#"
        class="h-full"
      />
      <DashboardCard
        title="Processing Time"
        value="2.5s"
        :change="-0.3"
        :icon="ClockIcon"
        footer="View performance"
        footerLink="#"
        class="h-full"
      />
    </div>

    <!-- Recent Activity -->
    <div class="bg-white shadow rounded-lg overflow-x-auto">
      <div class="px-2 py-5 sm:px-4 flex justify-between items-center">
        <h3 class="text-lg font-medium leading-6 text-gray-900">Recent Activity</h3>
        <button class="text-sm text-indigo-600 hover:text-indigo-500">View all</button>
      </div>
      <div class="border-t border-gray-200">
        <ul role="list" class="divide-y divide-gray-200">
          <li v-for="(activity, index) in recentActivities" :key="index" class="px-2 py-4 sm:px-4">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-indigo-600 truncate">{{ activity.title }}</p>
                <p class="mt-1 text-sm text-gray-500">{{ activity.description }}</p>
              </div>
              <div class="mt-2 sm:mt-0 sm:ml-4 flex flex-col sm:items-end">
                <div class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" 
                  :class="[
                    activity.status === 'Completed' ? 'bg-green-100 text-green-800' : 
                    activity.status === 'In Progress' ? 'bg-yellow-100 text-yellow-800' : 
                    'bg-gray-100 text-gray-800'
                  ]"
                >
                  {{ activity.status }}
                </div>
                <p class="mt-1 text-sm text-gray-500">{{ activity.time }}</p>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { DocumentIcon, ClockIcon, ChartBarIcon } from '@heroicons/vue/24/outline'
import DashboardCard from '../components/DashboardCard.vue'

const recentActivities = [
  {
    title: 'PMS Inventory Scraping',
    status: 'Completed',
    description: 'Successfully scraped 500 items',
    time: '2 hours ago'
  },
  {
    title: 'CM Inventory Update',
    status: 'In Progress',
    description: 'Processing 300 items',
    time: '4 hours ago'
  },
  {
    title: 'Data Export',
    status: 'Completed',
    description: 'Exported data to CSV format',
    time: '1 day ago'
  }
]
</script> 