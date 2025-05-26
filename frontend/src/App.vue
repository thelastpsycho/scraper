<script setup lang="ts">
import DashboardLayout from './components/DashboardLayout.vue'
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <nav class="bg-white shadow-md">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex justify-between h-16">
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <router-link to="/" class="text-xl font-bold text-red-500">Belia Scraper</router-link>
            </div>
            <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <router-link to="/" class="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700">Home</router-link>
              <router-link to="/scraping" class="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700">Scraping</router-link>
              <router-link to="/yielder" class="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700">Yielder</router-link>
              <router-link to="/data" class="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700">Data</router-link>
              <router-link to="/allotment" class="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700">Allotment</router-link>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <main>
      <router-view></router-view>
    </main>
  </div>
</template>

<style>
@tailwind base;
@tailwind components;
@tailwind utilities;

.router-link-active {
  color: #3b82f6;
  border-bottom: 2px solid #3b82f6;
}
</style>
