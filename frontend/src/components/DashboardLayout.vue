<template>
  <div class="min-h-screen bg-gray-50">
    <TopNav />
    <main class="pt-16">
      <div class="w-full px-2 sm:px-4 lg:px-8">
        <slot></slot>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import TopNav from './TopNav.vue'
</script> 