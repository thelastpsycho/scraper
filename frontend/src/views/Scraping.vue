<template>
  <div class="min-h-screen bg-app-primary text-app-tertiary">
    <!-- Header -->
    <header class="py-6">
      <div class="container mx-auto px-4 text-center">
        <h1 class="text-4xl font-bold text-app-tertiary">Data Scraper</h1>
        <p class="text-lg text-gray-600 mt-1">Your automated inventory management assistant</p>
      </div>
    </header>

    <!-- Main Content -->
    <main class="container mx-auto px-4 pb-12">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Left Column: Actions -->
        <section class="lg:col-span-2 space-y-6">
          <!-- Main Scraping Card -->
          <div class="bg-white rounded-xl shadow-md p-6">
            <h2 class="text-2xl font-bold text-app-tertiary mb-1">Start a New Scraping Task</h2>
            <p class="text-gray-500 mb-4">Begin by selecting a start date and initiating the process.</p>

            <div class="mb-4">
              <label for="startDate" class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                id="startDate"
                v-model="startDate"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-app-accent bg-gray-50 text-app-tertiary"
              />
            </div>

            <button
              @click="startScraping"
              :disabled="isScraping"
              class="w-full flex items-center justify-center bg-app-accent text-white py-3 px-5 rounded-md hover:bg-opacity-90 transition-all disabled:opacity-50 font-bold text-base shadow"
            >
              <svg v-if="isScraping" class="animate-spin -ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              {{ isScraping ? 'Scraping in Progress...' : 'Start Scraping Now' }}
            </button>
          </div>

          <!-- Other Actions Card -->
          <div class="bg-white rounded-xl shadow-md p-6">
            <h2 class="text-2xl font-bold text-app-tertiary mb-4">Additional Tools</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button @click="openModal" :disabled="loadingProcessCM" class="group flex flex-col items-center justify-center bg-app-secondary/50 text-app-tertiary p-3 rounded-md hover:bg-app-secondary/80 transition-all disabled:opacity-50">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                <span class="font-semibold text-xs">Process CM</span>
              </button>
              <button @click="triggerCombine" :disabled="loadingCombine" class="group flex flex-col items-center justify-center bg-app-secondary/50 text-app-tertiary p-3 rounded-md hover:bg-app-secondary/80 transition-all disabled:opacity-50">
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
                <span class="font-semibold text-xs">Combine Inventory</span>
              </button>
              <button @click="triggerYield" :disabled="loadingYield" class="group flex flex-col items-center justify-center bg-app-secondary/50 text-app-tertiary p-3 rounded-md hover:bg-app-secondary/80 transition-all disabled:opacity-50">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                <span class="font-semibold text-xs">Calculate Yield</span>
              </button>
            </div>
          </div>
        </section>

        <!-- Right Column: Status & Instructions -->
        <aside class="lg:col-span-1 space-y-6">
          <!-- Status Card -->
          <div class="bg-white rounded-xl shadow-md p-5">
            <h3 class="text-xl font-bold text-app-tertiary mb-3 flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              Status
            </h3>
            <div class="space-y-2">
              <div v-if="message" :class="['p-2.5 rounded-md text-xs font-medium', messageType === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                {{ message }}
              </div>
              <div v-if="error" class="p-2.5 bg-red-100 text-red-800 rounded-md text-xs font-medium">
                {{ error }}
              </div>
              <div v-if="success" class="p-2.5 bg-green-100 text-green-800 rounded-md text-xs font-medium">
                {{ success }}
              </div>
              <div v-if="!message && !error && !success" class="text-gray-500 text-sm">
                No new notifications. System is ready.
              </div>
            </div>
          </div>

          <!-- Instructions Card -->
          <div class="bg-app-secondary/20 rounded-xl p-5">
             <h3 class="text-xl font-bold text-app-tertiary mb-3 flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
              How it Works
            </h3>
            <ul class="space-y-2 text-gray-600 text-sm">
              <li class="flex items-start">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 mt-0.5 text-app-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                <span>Select a <strong class="font-semibold text-app-tertiary">start date</strong> for the data scrape.</span>
              </li>
              <li class="flex items-start">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 mt-0.5 text-app-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                <span>Click <strong class="font-semibold text-app-tertiary">"Start Scraping"</strong> to begin the process.</span>
              </li>
              <li class="flex items-start">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 mt-0.5 text-app-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                <span>Use the <strong class="font-semibold text-app-tertiary">additional tools</strong> for processing and analysis.</span>
              </li>
               <li class="flex items-start">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 mt-0.5 text-app-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                <span>Monitor the progress in the <strong class="font-semibold text-app-tertiary">scraping modal.</strong></span>
              </li>
            </ul>
          </div>
        </aside>

      </div>
    </main>

    <!-- Modal for file upload -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
      <div class="relative bg-white rounded-xl shadow-xl w-full max-w-md p-6 m-4">
        <button @click="closeModal" class="absolute top-3 right-3 text-gray-400 hover:text-gray-600">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
        <h3 class="text-xl font-bold text-app-tertiary mb-4">Upload and Process CM File</h3>
        
        <div class="border-2 border-dashed border-gray-300 rounded-md p-4 text-center mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1"><path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
          <input
            type="file"
            accept=".xlsx"
            @change="onFileChange"
            :disabled="uploading || processingCM"
            class="mt-2 block w-full text-xs text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-app-accent file:text-white hover:file:bg-opacity-90"
          />
        </div>

        <button
          @click="uploadAndProcessCM"
          :disabled="!selectedFile || uploading || processingCM"
          class="w-full flex items-center justify-center bg-app-accent text-white py-2.5 px-4 rounded-md hover:bg-opacity-90 transition-all disabled:opacity-50 font-bold text-sm"
        >
          <span v-if="uploading || processingCM" class="animate-spin mr-2 h-4 w-4 border-b-2 border-white rounded-full"></span>
          {{ uploading ? 'Uploading...' : (processingCM ? 'Processing...' : 'Upload & Process') }}
        </button>
        <div v-if="modalStatus" :class="['mt-3 p-2.5 rounded-md text-center text-xs', modalStatusType === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
          {{ modalStatus }}
        </div>
      </div>
    </div>

    <!-- Scraping Process Modal -->
    <div v-if="isScraping" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
       <div class="relative bg-white rounded-xl shadow-xl w-full max-w-xl p-6 m-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-bold text-app-tertiary flex items-center">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-app-accent mr-3"></div>
            Scraping in Progress
          </h3>
          <button @click="closeScrapingModal" class="text-gray-400 hover:text-gray-600">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <div class="bg-app-secondary/50 p-3 rounded-md mb-3">
          <p class="font-semibold text-app-tertiary text-sm">Current Operation:</p>
          <p class="text-app-tertiary font-mono text-xs">{{ currentOperation }}</p>
        </div>

        <div class="h-72 overflow-y-auto bg-gray-50 rounded-md p-3 border border-gray-200">
          <div v-for="(log, index) in scrapingLogs" :key="index" class="font-mono text-xs py-1 border-b border-gray-100 last:border-b-0">
            <span :class="{
              'text-green-600': typeof log === 'string' && (log.includes('successfully') || log.includes('completed')),
              'text-blue-600': typeof log === 'string' && (log.includes('Starting') || log.includes('Processing')),
              'text-gray-600': typeof log !== 'string' || (!log.includes('successfully') && !log.includes('completed') && !log.includes('Starting') && !log.includes('Processing'))
            }">
              {{ typeof log === 'object' ? JSON.stringify(log) : log }}
            </span>
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