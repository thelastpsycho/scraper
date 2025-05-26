<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header Section -->
      <div class="mb-8">
        <div class="md:flex md:items-center md:justify-between">
          <div class="min-w-0 flex-1">
            <h2 class="text-3xl font-bold text-gray-900">Data Management</h2>
            <p class="mt-1 text-sm text-gray-500">Manage and process your inventory data</p>
          </div>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Left Column: File Operations -->
        <div class="space-y-6">
          <!-- File Upload Card -->
          <div class="bg-white shadow rounded-lg p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">File Operations</h3>
            <div class="space-y-4">
              <div class="flex flex-col space-y-2">
                <label class="block text-sm font-medium text-gray-700">Upload CM Excel</label>
                <div class="flex items-center space-x-4">
                  <input 
                    type="file" 
                    accept=".xlsx" 
                    @change="onFileChange" 
                    :disabled="uploading"
                    class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                  />
                  <button
                    @click="uploadFile"
                    :disabled="!selectedFile || uploading"
                    class="inline-flex items-center px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded hover:bg-indigo-700 disabled:opacity-50"
                  >
                    <span v-if="uploading" class="animate-spin mr-2 h-4 w-4 border-b-2 border-white rounded-full"></span>
                    Upload
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Action Buttons Card -->
          <div class="bg-white shadow rounded-lg p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Data Processing</h3>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <!-- Add date input -->
              <div class="sm:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                <input 
                  type="date" 
                  v-model="startDate"
                  class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <button
                type="button"
                @click="startScraping"
                :disabled="isScraping"
                class="inline-flex items-center justify-center px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded hover:bg-indigo-700 disabled:opacity-50 sm:col-span-2"
              >
                <svg v-if="isScraping" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ isScraping ? 'Scraping in Progress...' : 'Start Scraping' }}
              </button>
              <button
                @click="openModal"
                :disabled="loadingProcessCM"
                class="inline-flex items-center justify-center px-4 py-2 bg-yellow-600 text-white text-sm font-medium rounded hover:bg-yellow-700 disabled:opacity-50 sm:col-span-2"
              >
                <span v-if="loadingProcessCM" class="animate-spin mr-2 h-4 w-4 border-b-2 border-white rounded-full"></span>
                Process CM
              </button>
              <button
                @click="triggerCombine"
                :disabled="loadingCombine"
                class="inline-flex items-center justify-center px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                <span v-if="loadingCombine" class="animate-spin mr-2 h-4 w-4 border-b-2 border-white rounded-full"></span>
                Combine Inventory
              </button>
              <button
                @click="triggerYield"
                :disabled="loadingYield"
                class="inline-flex items-center justify-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded hover:bg-green-700 disabled:opacity-50"
              >
                <span v-if="loadingYield" class="animate-spin mr-2 h-4 w-4 border-b-2 border-white rounded-full"></span>
                Calculate Yield
              </button>
            </div>
          </div>
        </div>

        <!-- Right Column: Status and Instructions -->
        <div class="space-y-6">
          <!-- Status Messages Card -->
          <div class="bg-white shadow rounded-lg p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Status</h3>
            <div class="space-y-4">
              <div v-if="message" :class="['p-4 rounded-md', messageType === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800']">
                {{ message }}
              </div>
              <div v-if="error" class="p-4 bg-red-50 text-red-800 rounded-md">
                {{ error }}
              </div>
              <div v-if="success" class="p-4 bg-green-50 text-green-800 rounded-md">
                {{ success }}
              </div>
            </div>
          </div>

          <!-- Instructions Card -->
          <div class="bg-white shadow rounded-lg p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Instructions</h3>
            <div class="prose prose-sm text-gray-500">
              <p>Click the "Start Scraping" button to begin the data scraping process. This will:</p>
              <ul class="mt-2 list-disc list-inside space-y-1">
                <li>Scrape inventory data from the PMS system</li>
                <li>Process and clean the data</li>
                <li>Save the results to the database</li>
              </ul>
              <p class="mt-4 text-sm text-gray-500">
                Note: The scraping process may take a few minutes to complete. Please do not close the browser window during this time.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal for file upload -->
    <div v-if="showModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex min-h-screen items-center justify-center p-4 text-center sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="closeModal"></div>
        <div class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
          <div class="absolute right-0 top-0 pr-4 pt-4">
            <button @click="closeModal" class="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none">
              <span class="sr-only">Close</span>
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="sm:flex sm:items-start">
            <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
              <h3 class="text-lg font-semibold leading-6 text-gray-900 mb-4">Upload CM Excel File</h3>
              <div class="mt-2">
                <input 
                  type="file" 
                  accept=".xlsx" 
                  @change="onFileChange" 
                  :disabled="uploading || processingCM"
                  class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                />
                <button
                  @click="uploadAndProcessCM"
                  :disabled="!selectedFile || uploading || processingCM"
                  class="mt-4 w-full inline-flex items-center justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
                >
                  <span v-if="uploading || processingCM" class="animate-spin mr-2 h-4 w-4 border-b-2 border-white rounded-full"></span>
                  Upload & Process
                </button>
                <div v-if="modalStatus" :class="['mt-4 p-3 rounded-md text-center', modalStatusType === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800']">
                  {{ modalStatus }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Scraping Process Modal -->
    <div v-if="isScraping" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex min-h-screen items-center justify-center p-4 text-center sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
        <div class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
          <div class="absolute right-0 top-0 pr-4 pt-4">
            <button 
              @click="closeScrapingModal"
              class="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none"
            >
              <span class="sr-only">Close</span>
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="sm:flex sm:items-start">
            <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-medium text-gray-900">Scraping Progress</h3>
                <div class="flex items-center">
                  <div class="animate-spin rounded-full h-5 w-5 border-2 border-indigo-600 border-t-transparent mr-2"></div>
                  <span class="text-sm text-gray-500">In Progress</span>
                </div>
              </div>
              
              <!-- Current Operation -->
              <div v-if="currentOperation" class="mb-4 text-sm font-medium text-indigo-700 bg-indigo-50 py-2 px-3 rounded">
                {{ currentOperation }}
              </div>
              
              <!-- Progress Log -->
              <div class="space-y-2 max-h-64 overflow-y-auto border border-gray-100 rounded p-3">
                <div v-for="(log, index) in scrapingLogs" :key="index" 
                     class="text-sm py-1 px-2 rounded my-1"
                     :class="{
                       'bg-green-50/60 text-green-700': typeof log === 'string' && (log.includes('successfully') || log.includes('completed')),
                       'bg-blue-50/60 text-blue-700': typeof log === 'string' && (log.includes('Starting') || log.includes('Processing')),
                       'bg-gray-50/60 text-gray-700': typeof log === 'string' && !log.includes('successfully') && !log.includes('completed') && !log.includes('Starting') && !log.includes('Processing')
                     }">
                  {{ typeof log === 'object' ? JSON.stringify(log) : log }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from '../plugins/axios'

const isScraping = ref(false)
const error = ref('')
const success = ref('')
const scrapingLogs = ref<(string | object)[]>([])
const currentOperation = ref('')
let eventSource: EventSource | null = null
const loadingCombine = ref(false)
const loadingYield = ref(false)
const loadingProcessCM = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const startDate = ref(new Date().toISOString().split('T')[0]) // Initialize with today's date

const selectedFile = ref<File|null>(null)
const uploading = ref(false)
const uploadStatus = ref('')
const uploadStatusType = ref<'success'|'error'>('success')
const cmUploaded = ref(false)

// Modal state
const showModal = ref(false)
const processingCM = ref(false)
const modalStatus = ref('')
const modalStatusType = ref<'success'|'error'>('success')

const startScraping = async () => {
  isScraping.value = true
  error.value = ''
  success.value = ''
  scrapingLogs.value = []
  currentOperation.value = 'Starting scraping process...'

  try {
    // First make a POST request to start the scraping with date parameter
    console.log('Starting scraping process...')
    const response = await axios.post('/api/scrape', {
      startDate: startDate.value // Use the selected date
    })
    console.log('Scraping start response:', response.data)
    
    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to start scraping')
    }
    
    // Then create EventSource for Server-Sent Events
    console.log('Establishing SSE connection...')
    eventSource = new EventSource('/api/scrape/stream')
    
    // Add connection opened handler
    eventSource.onopen = () => {
      console.log('SSE connection opened')
      scrapingLogs.value.push('Connected to server...')
    }
    
    eventSource.onmessage = (event) => {
      console.log('Received message:', event.data)
      
      // Make sure scraping state is true
      isScraping.value = true
      
      if (event.data === '[DONE]') {
        console.log('Scraping completed')
        eventSource?.close()
        success.value = 'Scraping completed successfully!'
        currentOperation.value = 'Scraping completed!'
      }
      
      if (event.data.startsWith('Error:')) {
        console.error('Scraping error:', event.data)
        error.value = event.data
        eventSource?.close()
        return
      }
      
      // Parse and handle message data
      try {
        const messageData = JSON.parse(event.data);
        
        // Handle pending status specially
        if (messageData.status === "pending") {
          // Skip adding repetitive pending messages to the logs
          return;
        }
        
        // For complete or success status, update currentOperation
        if (messageData.status === "success" || messageData.status === "complete") {
          currentOperation.value = messageData.message || 'Operation completed';
        }
        
        scrapingLogs.value.push(messageData);
      } catch (e) {
        // Not JSON or parsing failed, treat as regular message
        // Update the current operation text for meaningful string messages
        if (typeof event.data === 'string' && 
            !event.data.includes('{') && 
            !event.data.includes('pending')) {
          currentOperation.value = event.data;
        }
        
        scrapingLogs.value.push(event.data);
      }
    }
    
    eventSource.onerror = (err) => {
      console.error('EventSource error:', err)
      // Only show error if we're still in scraping state
      // This prevents showing error when connection closes normally after completion
      if (isScraping.value) {
        error.value = 'Connection to server lost. Please try again.'
        eventSource?.close()
      }
    }
  } catch (err: any) {
    console.error('Error during scraping:', err)
    error.value = err.response?.data?.message || 'Failed to start scraping. Please try again.'
    setTimeout(() => {
      isScraping.value = false
    }, 3000)
  }
}

function onFileChange(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files && files.length > 0) {
    selectedFile.value = files[0]
    uploadStatus.value = ''
    cmUploaded.value = false
  }
}

async function uploadFile() {
  if (!selectedFile.value) return
  uploading.value = true
  uploadStatus.value = ''
  cmUploaded.value = false
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const res = await axios.post('/api/upload-cm-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    uploadStatus.value = res.data.message || 'File uploaded successfully.'
    uploadStatusType.value = 'success'
    cmUploaded.value = true
  } catch (err: any) {
    uploadStatus.value = err?.response?.data?.message || 'Failed to upload file.'
    uploadStatusType.value = 'error'
    cmUploaded.value = false
  } finally {
    uploading.value = false
  }
}

function openModal() {
  showModal.value = true
  selectedFile.value = null
  modalStatus.value = ''
}

function closeModal() {
  showModal.value = false
  selectedFile.value = null
  modalStatus.value = ''
}

async function uploadAndProcessCM() {
  if (!selectedFile.value) return
  uploading.value = true
  modalStatus.value = ''
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const uploadRes = await axios.post('/api/upload-cm-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    modalStatus.value = uploadRes.data.message || 'File uploaded successfully.'
    modalStatusType.value = 'success'
    // Now trigger process CM
    processingCM.value = true
    const processRes = await axios.post('/api/process-cm')
    modalStatus.value = processRes.data.message || 'Process CM completed.'
    modalStatusType.value = 'success'
  } catch (err: any) {
    modalStatus.value = err?.response?.data?.message || 'Failed to upload or process CM.'
    modalStatusType.value = 'error'
  } finally {
    uploading.value = false
    processingCM.value = false
  }
}

async function triggerCombine() {
  loadingCombine.value = true
  message.value = ''
  try {
    console.log('Starting combine inventory process...')
    const res = await axios.post('/api/combine-inventory')
    console.log('Combine inventory response:', res.data)
    message.value = res.data.message || 'Combine inventory completed.'
    messageType.value = 'success'
  } catch (err: any) {
    console.error('Error in combine inventory:', err)
    message.value = err?.response?.data?.message || 'Failed to combine inventory. Please check the console for details.'
    messageType.value = 'error'
  } finally {
    loadingCombine.value = false
  }
}

async function triggerYield() {
  loadingYield.value = true
  message.value = ''
  try {
    console.log('Starting yield calculation process...')
    const res = await axios.post('/api/yield')
    console.log('Yield calculation response:', res.data)
    message.value = res.data.message || 'Yield calculation completed.'
    messageType.value = 'success'
  } catch (err: any) {
    console.error('Error in yield calculation:', err)
    message.value = err?.response?.data?.message || 'Failed to calculate yield. Please check the console for details.'
    messageType.value = 'error'
  } finally {
    loadingYield.value = false
  }
}

function closeScrapingModal() {
  if (eventSource) {
    eventSource.close();
  }
  isScraping.value = false;
}
</script> 