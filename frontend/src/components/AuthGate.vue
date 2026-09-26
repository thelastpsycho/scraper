<template>
  <div v-if="loading" class="flex min-h-screen items-center justify-center bg-slate-100 text-slate-700">
    Checking access…
  </div>
  <div v-else-if="!authenticated" class="flex min-h-screen items-center justify-center bg-slate-100 p-5">
    <form class="w-full max-w-sm space-y-5 rounded-2xl bg-white p-7 shadow-xl" @submit.prevent="login">
      <h1 class="text-xl font-semibold text-slate-900">Revenue Console</h1>
      <p v-if="!configured" class="text-sm text-amber-800" role="alert">
        API authentication is not configured. Set APP_ACCESS_PIN and APP_SESSION_SECRET on the backend.
      </p>
      <template v-else>
        <label for="access-pin" class="block text-sm font-medium text-slate-700">6-digit PIN</label>
        <input id="access-pin" v-model="pin" type="password" inputmode="numeric" pattern="\d{6}" maxlength="6"
          autocomplete="off" required
          class="w-full rounded-lg border border-slate-300 px-3 py-2 tracking-widest" />
        <p v-if="error" class="text-sm text-red-700" role="alert">{{ error }}</p>
        <button type="submit" :disabled="pin.length !== 6 || submitting"
          class="rounded-lg bg-slate-900 px-4 py-2 text-white disabled:opacity-50">
          {{ submitting ? 'Signing in…' : 'Sign in' }}
        </button>
      </template>
    </form>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import axios, { setCsrfToken } from '../plugins/axios'

const loading = ref(true)
const submitting = ref(false)
const configured = ref(false)
const authenticated = ref(false)
const pin = ref('')
const error = ref('')

function expireSession() {
  authenticated.value = false
  setCsrfToken(null)
  error.value = 'Your session expired. Please sign in again.'
}

async function refresh() {
  try {
    const { data } = await axios.get('/api/auth/status')
    configured.value = !!data.configured || !!data.dev_mode
    authenticated.value = !!data.authenticated
    setCsrfToken(data.csrf_token || null)
    error.value = ''
  } catch {
    configured.value = false
    authenticated.value = false
    error.value = 'Cannot reach the backend.'
  } finally {
    loading.value = false
  }
}

async function login() {
  if (pin.value.length !== 6 || submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const { data } = await axios.post('/api/auth/login', { pin: pin.value })
    setCsrfToken(data.csrf_token)
    authenticated.value = true
    pin.value = ''
  } catch {
    error.value = 'Could not sign in. Check your PIN and backend configuration.'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  window.addEventListener('operator-session-expired', expireSession)
  void refresh()
})
onUnmounted(() => window.removeEventListener('operator-session-expired', expireSession))
</script>
