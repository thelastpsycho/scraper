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
</style>
