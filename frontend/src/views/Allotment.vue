<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-8">Allotment Update</h1>
    
    <!-- Status Card -->
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold mb-2">Update Status</h2>
          <p class="text-gray-600" v-if="!isUpdating">
            {{ statusMessage }}
          </p>
          <div v-else class="flex items-center space-x-2">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
            <span class="text-gray-600">Updating allotment...</span>
          </div>
        </div>
        <button
          @click="triggerUpdate"
          :disabled="isUpdating"
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {{ isUpdating ? 'Updating...' : 'Update Allotment' }}
        </button>
        <button
          @click="triggerDomUpdate"
          :disabled="isUpdating"
          class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors ml-2"
        >
          {{ isUpdating ? 'Updating...' : 'Update Allotment (DOM)' }}
        </button>
      </div>
    </div>

    <!-- Process Log Card -->
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-semibold">Process Log</h2>
        <button
          @click="clearLogs"
          class="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
          :disabled="isUpdating"
        >
          Clear Logs
        </button>
      </div>
      <div class="bg-gray-50 rounded-lg p-4 h-96 overflow-y-auto">
        <div v-if="logs.length === 0" class="text-gray-500 text-center py-8">
          No logs available. Start the update process to see logs.
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="(log, index) in logs"
            :key="index"
            class="flex items-start space-x-2"
            :class="{
              'text-blue-600': log.type === 'info',
              'text-green-600': log.type === 'success',
              'text-red-600': log.type === 'error'
            }"
          >
            <span class="text-gray-500 text-sm">{{ formatTime(log.timestamp) }}</span>
            <span class="flex-1">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Credentials Card -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-xl font-semibold mb-4">Credentials</h2>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input
            v-model="username"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            :disabled="isUpdating"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
            v-model="password"
            type="password"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            :disabled="isUpdating"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const isUpdating = ref(false)
const statusMessage = ref('Ready to update allotment')
const username = ref('krisnatha')
const password = ref('Nasibungkus13')
const logs = ref<Array<{message: string, type: 'info' | 'success' | 'error', timestamp: Date}>>([])

const formatTime = (date: Date) => {
  return date.toLocaleTimeString()
}

const addLog = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
  logs.value.push({
    message,
    type,
    timestamp: new Date()
  })
  // Auto scroll to bottom
  setTimeout(() => {
    const logContainer = document.querySelector('.overflow-y-auto')
    if (logContainer) {
      logContainer.scrollTop = logContainer.scrollHeight
    }
  }, 100)
}

const clearLogs = () => {
  logs.value = []
}

const triggerUpdate = async () => {
  try {
    isUpdating.value = true
    statusMessage.value = 'Updating allotment...'
    addLog('Starting allotment update process...', 'info')

    // Create EventSource for real-time updates
    const eventSource = new EventSource('/api/update-allotment/stream')
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      addLog(data.message, data.type)
      
      if (data.type === 'success' || data.type === 'error') {
        eventSource.close()
        isUpdating.value = false
        statusMessage.value = data.type === 'success' 
          ? 'Allotment updated successfully!' 
          : `Error: ${data.message}`
      }
    }

    eventSource.onerror = (error) => {
      addLog('Connection error occurred', 'error')
      eventSource.close()
      isUpdating.value = false
      statusMessage.value = 'Error: Connection lost'
    }

    // Send credentials to start the process
    await axios.post('/api/update-allotment', {
      username: username.value,
      password: password.value
    })

  } catch (error: any) {
    addLog(`Error: ${error.response?.data?.message || error.message}`, 'error')
    statusMessage.value = `Error: ${error.response?.data?.message || error.message}`
    isUpdating.value = false
  }
}

const triggerDomUpdate = async () => {
  try {
    isUpdating.value = true
    statusMessage.value = 'Updating allotment via DOM...'
    addLog('Starting DOM-based allotment update process...', 'info')

    // Create EventSource for real-time updates
    const eventSource = new EventSource('/api/update-allotment/stream')
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      addLog(data.message, data.type)
      
      if (data.type === 'success' || data.type === 'error') {
        eventSource.close()
        isUpdating.value = false
        statusMessage.value = data.type === 'success' 
          ? 'Allotment updated successfully (DOM)!' 
          : `Error: ${data.message}`
      }
    }

    eventSource.onerror = (error) => {
      addLog('Connection error occurred', 'error')
      eventSource.close()
      isUpdating.value = false
      statusMessage.value = 'Error: Connection lost'
    }

    // Send credentials to start the DOM-based process
    await axios.post('/api/update-allotment-dom', {
      username: username.value,
      password: password.value
    })

  } catch (error: any) {
    addLog(`Error: ${error.response?.data?.message || error.message}`, 'error')
    statusMessage.value = `Error: ${error.response?.data?.message || error.message}`
    isUpdating.value = false
  }
}
</script>

<style scoped>
.container {
  max-width: 1200px;
}

.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: #CBD5E0 #F7FAFC;
}

.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #F7FAFC;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: #CBD5E0;
  border-radius: 4px;
}
</style> 