<script setup lang="ts">
import DashboardLayout from './components/DashboardLayout.vue'
</script>

<template>
  <DashboardLayout>
    <router-view />
  </DashboardLayout>
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
