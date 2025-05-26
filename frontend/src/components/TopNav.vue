<template>
  <nav class="bg-white border-b border-gray-200 fixed w-full z-30">
    <div class="w-full px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <!-- Left side -->
        <div class="flex items-center">
          <div class="flex-shrink-0 flex items-center">
            <h1 class="text-xl font-bold text-gray-800">Scraper Dashboard</h1>
          </div>
          <!-- Desktop Navigation -->
          <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
            <router-link 
              to="/" 
              class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              active-class="border-indigo-500 text-gray-900"
            >
              Dashboard
            </router-link>
            <router-link 
              to="/scraping" 
              class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              active-class="border-indigo-500 text-gray-900"
            >
              Scraping
            </router-link>
            <router-link 
              to="/data" 
              class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              active-class="border-indigo-500 text-gray-900"
            >
              Data
            </router-link>
            <router-link 
              to="/yielder" 
              class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              active-class="border-indigo-500 text-gray-900"
            >
              Yielder
            </router-link>
          </div>
        </div>

        <!-- Right side -->
        <div class="flex items-center">
          <!-- Mobile menu button -->
          <button 
            @click="isMobileMenuOpen = !isMobileMenuOpen"
            class="sm:hidden inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
          >
            <span class="sr-only">Open main menu</span>
            <Bars3Icon v-if="!isMobileMenuOpen" class="block h-6 w-6" aria-hidden="true" />
            <XMarkIcon v-else class="block h-6 w-6" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile menu -->
    <div 
      v-show="isMobileMenuOpen" 
      class="sm:hidden"
    >
      <div class="pt-2 pb-3 space-y-1">
        <router-link 
          to="/" 
          class="block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
          :class="[route.path === '/' ? 'border-indigo-500 text-indigo-700 bg-indigo-50' : 'border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700']"
        >
          Dashboard
        </router-link>
        <router-link 
          to="/scraping" 
          class="block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
          :class="[route.path === '/scraping' ? 'border-indigo-500 text-indigo-700 bg-indigo-50' : 'border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700']"
        >
          Scraping
        </router-link>
        <router-link 
          to="/data" 
          class="block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
          :class="[route.path === '/data' ? 'border-indigo-500 text-indigo-700 bg-indigo-50' : 'border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700']"
        >
          Data
        </router-link>
        <router-link 
          to="/yielder" 
          class="block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
          :class="[route.path === '/yielder' ? 'border-indigo-500 text-indigo-700 bg-indigo-50' : 'border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700']"
        >
          Yielder
        </router-link>
      </div>
      <div class="pt-4 pb-3 border-t border-gray-200">
        <div class="px-4">
          <button class="w-full bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium">
            Start Scraping
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { Bars3Icon, XMarkIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const isMobileMenuOpen = ref(false)
</script> 