<template>
  <nav class="bg-app-primary shadow-sm fixed w-full z-30">
    <div class="container mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-20">
        <!-- Left side: Logo and Title -->
        <div class="flex items-center">
          <div class="flex-shrink-0 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-auto text-app-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h1 class="text-2xl font-bold text-app-tertiary ml-3">Scraper</h1>
          </div>
        </div>

        <!-- Center: Desktop Navigation -->
        <div class="hidden sm:ml-6 sm:flex sm:items-center sm:space-x-2">
          <router-link v-for="item in navigation" :key="item.name" :to="item.href" 
            :class="[
              route.path === item.href 
                ? 'bg-app-secondary text-app-accent'
                : 'text-app-tertiary hover:bg-app-secondary/60 hover:text-app-accent',
              'px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center'
            ]"
          >
            <component :is="item.icon" class="h-5 w-5 mr-2" />
            {{ item.name }}
          </router-link>
        </div>

        <!-- Right side: Mobile menu button -->
        <div class="flex items-center sm:hidden">
          <button @click="isMobileMenuOpen = !isMobileMenuOpen" class="inline-flex items-center justify-center p-2 rounded-md text-app-tertiary hover:bg-app-secondary focus:outline-none">
            <span class="sr-only">Open main menu</span>
            <Bars3Icon v-if="!isMobileMenuOpen" class="block h-6 w-6" aria-hidden="true" />
            <XMarkIcon v-else class="block h-6 w-6" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile menu -->
    <div v-show="isMobileMenuOpen" class="sm:hidden bg-app-primary border-t border-app-secondary">
      <div class="px-2 pt-2 pb-3 space-y-1">
        <router-link v-for="item in navigation" :key="item.name" :to="item.href" 
          @click="isMobileMenuOpen = false"
          :class="[
            route.path === item.href 
              ? 'bg-app-secondary text-app-accent' 
              : 'text-app-tertiary hover:bg-app-secondary/60 hover:text-app-accent',
            'block px-3 py-2 rounded-md text-base font-medium flex items-center'
          ]"
        >
          <component :is="item.icon" class="h-6 w-6 mr-3" />
          {{ item.name }}
        </router-link>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Bars3Icon,
  XMarkIcon,
  HomeIcon,
  DocumentTextIcon,
  CircleStackIcon,
  ChartBarIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/vue/24/outline'

const route = useRoute()
const isMobileMenuOpen = ref(false)

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Scraping', href: '/scraping', icon: DocumentTextIcon },
  { name: 'Data', href: '/data', icon: CircleStackIcon },
  { name: 'Yielder', href: '/yielder', icon: ChartBarIcon },
  { name: 'Chat', href: '/chat', icon: ChatBubbleLeftRightIcon },
]
</script>