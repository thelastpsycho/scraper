<script setup lang="ts">
import DashboardLayout from './components/DashboardLayout.vue'
import AuthGate from './components/AuthGate.vue'
</script>

<template>
  <AuthGate>
    <DashboardLayout>
      <router-view />
    </DashboardLayout>
  </AuthGate>
</template>

<style>
@tailwind base;
@tailwind components;
@tailwind utilities;
</style>
