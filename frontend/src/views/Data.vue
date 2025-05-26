<template>
  <div class="space-y-2">
    <!-- Page header -->
    <div class="flex items-center justify-between pb-1 border-b border-gray-200">
      <h2 class="text-base font-medium text-gray-900">Data View</h2>
    </div>
    <!-- Loading state -->
    <div v-if="loading" class="flex justify-center items-center py-4">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 border-l-4 border-red-400 p-2 text-xs">
      <div class="flex items-center">
        <div class="flex-shrink-0">
          <svg class="h-3 w-3 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-1.5">
          <p class="text-red-700">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Data tabs -->
    <div v-else class="bg-white shadow-sm rounded border border-gray-200">
      <!-- Tab navigation -->
      <div class="flex border-b border-gray-200 bg-gray-50 rounded-t">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            activeTab === tab.id
              ? 'border-indigo-500 text-indigo-600 bg-white'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
            'flex-1 py-1 px-2 text-center border-b-2 text-[11px] font-medium transition-colors duration-200 ease-in-out'
          ]"
        >
          {{ tab.name }}
        </button>
      </div>

      <!-- Tab content -->
      <div class="p-2">
        <!-- PMS Raw Inventory -->
        <div v-if="activeTab === 'pms-raw'" class="space-y-1">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-xs font-medium text-gray-900 inline">PMS Inventory Raw</h3>
              <span class="text-[10px] text-gray-500 ml-1">Raw inventory data from PMS system</span>
            </div>
            <div class="flex space-x-1">
              <button
                @click="exportData('pms-raw', 'csv')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export CSV"
              >
                <i class="fas fa-file-csv"></i>
              </button>
              <button
                @click="exportData('pms-raw', 'excel')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export Excel"
              >
                <i class="fas fa-file-excel"></i>
              </button>
              <button
                @click="exportData('pms-raw', 'json')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export JSON"
              >
                <i class="fas fa-file-code"></i>
              </button>
            </div>
          </div>
          <div v-if="pmsRawData.length === 0" class="text-center py-8 text-sm text-gray-500">
            No PMS raw inventory data available. Please run the scraper first.
          </div>
          <div v-else class="border border-gray-200 rounded">
            <div class="h-[calc(100vh-200px)] overflow-auto">
              <table class="min-w-full divide-y divide-gray-200 text-[11px] relative table-fixed">
                <thead class="bg-indigo-50 sticky top-0 z-10">
                  <tr>
                    <th v-for="header in pmsRawHeaders" 
                        :key="header" 
                        class="relative h-[60px] align-bottom bg-indigo-50 group border-r border-indigo-200 text-center cursor-pointer hover:bg-indigo-100"
                        :title="header"
                        @click="pmsRawData = sortData(pmsRawData, header)">
                      <div class="absolute bottom-0 left-0 ml-2 mb-1 origin-bottom-left -rotate-45 whitespace-nowrap text-[10px] font-bold text-indigo-700 uppercase tracking-wider overflow-hidden text-ellipsis max-w-[100px]">
                        {{ header }} {{ getSortIndicator(header) }}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(row, index) in pmsRawData" :key="index" class="hover:bg-gray-50">
                    <td v-for="header in pmsRawHeaders" 
                        :key="header" 
                        class="px-0.5 py-0.5 whitespace-nowrap text-gray-600 overflow-hidden text-ellipsis min-w-[40px] max-w-[60px] border-r border-gray-200 text-center"
                        :title="header.toLowerCase().includes('date') ? formatDate(row[header]) : row[header]"
                        :style="getCellStyle(row[header])">
                      {{ header.toLowerCase().includes('date') ? formatDate(row[header]) : row[header] }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- PMS Processed Inventory -->
        <div v-if="activeTab === 'pms-processed'" class="space-y-1">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-xs font-medium text-gray-900 inline">PMS Inventory Processed</h3>
              <span class="text-[10px] text-gray-500 ml-1">Processed inventory data from PMS system</span>
            </div>
            <div class="flex space-x-1">
              <button
                @click="exportData('pms-processed', 'csv')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export CSV"
              >
                <i class="fas fa-file-csv"></i>
              </button>
              <button
                @click="exportData('pms-processed', 'excel')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export Excel"
              >
                <i class="fas fa-file-excel"></i>
              </button>
              <button
                @click="exportData('pms-processed', 'json')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export JSON"
              >
                <i class="fas fa-file-code"></i>
              </button>
            </div>
          </div>
          <div v-if="pmsProcessedData.length === 0" class="text-center py-8 text-sm text-gray-500">
            No PMS processed inventory data available. Please run the scraper first.
          </div>
          <div v-else class="border border-gray-200 rounded">
            <div class="h-[calc(100vh-200px)] overflow-auto">
              <table class="min-w-full divide-y divide-gray-200 text-[11px] relative table-fixed">
                <thead class="bg-indigo-50 sticky top-0 z-10">
                  <tr>
                    <th v-for="header in pmsProcessedHeaders" 
                        :key="header" 
                        class="relative h-[60px] align-bottom bg-indigo-50 group border-r border-indigo-200 text-center cursor-pointer hover:bg-indigo-100"
                        :title="header"
                        @click="pmsProcessedData = sortData(pmsProcessedData, header)">
                      <div class="absolute bottom-0 left-0 ml-2 mb-1 origin-bottom-left -rotate-45 whitespace-nowrap text-[10px] font-bold text-indigo-700 uppercase tracking-wider overflow-hidden text-ellipsis max-w-[100px]">
                        {{ header }} {{ getSortIndicator(header) }}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(row, index) in pmsProcessedData" :key="index" class="hover:bg-gray-50">
                    <td v-for="header in pmsProcessedHeaders" 
                        :key="header" 
                        class="px-0.5 py-0.5 whitespace-nowrap text-gray-600 overflow-hidden text-ellipsis min-w-[40px] max-w-[60px] border-r border-gray-200 text-center"
                        :title="header.toLowerCase().includes('date') ? formatDate(row[header]) : row[header]"
                        :style="getCellStyle(row[header])">
                      {{ header.toLowerCase().includes('date') ? formatDate(row[header]) : row[header] }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Combined Inventory -->
        <div v-if="activeTab === 'combined'" class="space-y-1">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-xs font-medium text-gray-900 inline">Combined Inventory</h3>
              <span class="text-[10px] text-gray-500 ml-1">Combined inventory data from all sources</span>
            </div>
            <div class="flex space-x-1">
              <button
                @click="exportData('combined', 'csv')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export CSV"
              >
                <i class="fas fa-file-csv"></i>
              </button>
              <button
                @click="exportData('combined', 'excel')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export Excel"
              >
                <i class="fas fa-file-excel"></i>
              </button>
              <button
                @click="exportData('combined', 'json')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export JSON"
              >
                <i class="fas fa-file-code"></i>
              </button>
            </div>
          </div>
          <div v-if="combinedData.length === 0" class="text-center py-8 text-sm text-gray-500">
            No combined inventory data available. Please run the combine inventory process first.
          </div>
          <div v-else class="border border-gray-200 rounded">
            <div class="h-[calc(100vh-200px)] overflow-auto">
              <table class="min-w-full divide-y divide-gray-200 text-[11px] relative table-fixed">
                <thead class="bg-indigo-50 sticky top-0 z-10">
                  <tr>
                    <th v-for="header in combinedHeaders" 
                        :key="header" 
                        class="relative align-middle bg-indigo-50 group border-r border-indigo-200 text-center cursor-pointer hover:bg-indigo-100"
                        :title="tooltipMappingsRef[header] || header"
                        @click="combinedData = sortData(combinedData, header)">
                      <div class="text-center whitespace-nowrap text-[10px] font-bold text-indigo-700 uppercase tracking-wider overflow-hidden text-ellipsis max-w-[100px]">
                        {{ header }} {{ getSortIndicator(header) }}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(row, index) in combinedData" :key="index" class="hover:bg-gray-50">
                    <td v-for="header in combinedHeaders" 
                        :key="header" 
                        class="px-0.5 py-0.5 whitespace-nowrap text-gray-600 overflow-hidden text-ellipsis min-w-[40px] max-w-[60px] border-r border-gray-200 text-center"
                        :title="header.toLowerCase().includes('date') ? formatDate(row[header]) : row[header]"
                        :style="getCellStyle(row[header])">
                      {{ header.toLowerCase().includes('date') ? formatDate(row[header]) : row[header] }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Inventory Allocation -->
        <div v-if="activeTab === 'allocation'" class="space-y-1">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-xs font-medium text-gray-900 inline">Inventory Allocation</h3>
              <span class="text-[10px] text-gray-500 ml-1">Daily inventory allocation data</span>
            </div>
            <div class="flex space-x-1">
              <button
                @click="exportData('allocation', 'csv')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export CSV"
              >
                <i class="fas fa-file-csv"></i>
              </button>
              <button
                @click="exportData('allocation', 'excel')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export Excel"
              >
                <i class="fas fa-file-excel"></i>
              </button>
              <button
                @click="exportData('allocation', 'json')"
                class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                title="Export JSON"
              >
                <i class="fas fa-file-code"></i>
              </button>
            </div>
          </div>
          <div v-if="allocationData.length === 0" class="text-center py-8 text-sm text-gray-500">
            No inventory allocation data available. Please run the yield calculation first.
          </div>
          <div v-else class="border border-gray-200 rounded">
            <div class="h-[calc(100vh-200px)] overflow-auto">
              <table class="min-w-full divide-y divide-gray-200 text-[11px] relative table-fixed">
                <thead class="bg-indigo-50 sticky top-0 z-10">
                  <tr>
                    <th v-for="header in allocationHeaders" 
                        :key="header" 
                        class="relative h-[60px] align-bottom bg-indigo-50 group border-r border-indigo-200 text-center cursor-pointer hover:bg-indigo-100"
                        :title="header"
                        @click="allocationData = sortData(allocationData, header)">
                      <div class="absolute bottom-0 left-0 ml-2 mb-1 origin-bottom-left -rotate-45 whitespace-nowrap text-[10px] font-bold text-indigo-700 uppercase tracking-wider overflow-hidden text-ellipsis max-w-[100px]">
                        {{ header }} {{ getSortIndicator(header) }}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(row, index) in allocationData" :key="index" class="hover:bg-gray-50">
                    <td v-for="header in allocationHeaders" 
                        :key="header" 
                        class="px-0.5 py-0.5 whitespace-nowrap text-gray-600 overflow-hidden text-ellipsis min-w-[40px] max-w-[60px] border-r border-gray-200 text-center"
                        :title="header.toLowerCase().includes('date') ? formatDate(row[header]) : row[header]"
                        :style="getCellStyle(row[header])">
                      {{ header.toLowerCase().includes('date') ? formatDate(row[header]) : row[header] }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from '../plugins/axios'
import * as XLSX from 'xlsx'
import '@fortawesome/fontawesome-free/css/all.css'

// Scraping state
const isScraping = ref(false)
const showScrapingModal = ref(false)
const scrapingError = ref('')
const scrapingMessages = ref<string[]>([])
const scrapingSteps = ref([
  { name: 'Login', status: 'pending', message: '' },
  { name: 'Select Brand', status: 'pending', message: '' },
  { name: 'Navigate to Room Availability', status: 'pending', message: '' },
  { name: 'Load Table Data', status: 'pending', message: '' },
  { name: 'Process Data', status: 'pending', message: '' }
])

// Data refs
const pmsRawData = ref<any[]>([])
const pmsProcessedData = ref<any[]>([])
const combinedData = ref<any[]>([])
const allocationData = ref<any[]>([])

// Headers refs
const pmsRawHeaders = ref<string[]>([])
const pmsProcessedHeaders = ref<string[]>([])
const combinedHeaders = ref<string[]>([])
const allocationHeaders = ref<string[]>([])

// Loading and error states
const loading = ref(true)
const error = ref('')

// Tab management
const tabs = [
  { id: 'pms-raw', name: 'PMS Raw' },
  { id: 'pms-processed', name: 'PMS Processed' },
  { id: 'combined', name: 'Combined' },
  { id: 'allocation', name: 'Allocation' }
]
const activeTab = ref('pms-raw')

// Add this near the top of the script with other refs
const tooltipMappingsRef = ref<Record<string, string>>({})

// Add these refs after the existing refs
const sortColumn = ref('')
const sortDirection = ref<'asc' | 'desc'>('asc')

function formatDate(value: string) {
  if (!value) return ''
  // Try to parse as date
  const d = new Date(value)
  if (isNaN(d.getTime())) return value
  const day = d.getDate().toString().padStart(2, '0')
  const month = d.toLocaleString('en-US', { month: 'short' })
  const year = d.getFullYear().toString().slice(-2)
  return `${day}-${month}-${year}`
}

function getCellStyle(value: any) {
  // Check if the value is a number
  const num = Number(value)
  if (isNaN(num)) return {}
  
  if (num >= 1 && num <= 5) {
    return { 
      color: '#854D0E', // yellow-800
      backgroundColor: '#FEF3C7', // yellow-100
      fontWeight: '500'
    }
  } else if (num === 0) {
    return { 
      color: '#9A3412', // orange-800
      backgroundColor: '#FFEDD5', // orange-100
      fontWeight: '500'
    }
  } else if (num < 0) {
    return { 
      color: '#991B1B', // red-800
      backgroundColor: '#FEE2E2', // red-100
      fontWeight: '500'
    }
  }
  return {}
}

// Scraping functions
const startScraping = async () => {
  isScraping.value = true
  showScrapingModal.value = true
  scrapingError.value = ''
  scrapingMessages.value = []
  scrapingSteps.value = scrapingSteps.value.map(step => ({ ...step, status: 'pending', message: '' }))

  try {
    // Start scraping
    const response = await axios.post('/api/scrape')
    if (response.data.status === 'success') {
      // Set up SSE connection for progress updates
      const eventSource = new EventSource('/api/scrape/stream')
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('Received SSE message:', data) // Debug log
          
          // Add message to the log
          if (data.message) {
            scrapingMessages.value.push(data.message)
          }
          
          // Update step status based on message content
          if (data.message?.includes('Login credentials entered')) {
            updateStepStatus(0, 'completed', data.message)
          } else if (data.message?.includes('Successfully selected brand')) {
            updateStepStatus(1, 'completed', data.message)
          } else if (data.message?.includes('Clicked Room Availability')) {
            updateStepStatus(2, 'completed', data.message)
          } else if (data.message?.includes('Table loaded successfully')) {
            updateStepStatus(3, 'completed', data.message)
          } else if (data.message?.includes('Processed data saved')) {
            updateStepStatus(4, 'completed', data.message)
          }

          // Handle completion
          if (data.status === 'complete') {
            console.log('Scraping completed') // Debug log
            eventSource.close()
            setTimeout(() => {
              closeScrapingModal()
              fetchData() // Refresh data after successful scraping
            }, 1000)
          }

          // Handle errors
          if (data.status === 'error') {
            console.error('Scraping error:', data.message) // Debug log
            scrapingError.value = data.message
            eventSource.close()
            isScraping.value = false
          }
        } catch (err) {
          console.error('Error parsing SSE message:', err)
        }
      }

      eventSource.onerror = (err) => {
        console.error('SSE connection error:', err)
        eventSource.close()
        scrapingError.value = 'Connection to server lost'
        isScraping.value = false
      }
    }
  } catch (err: any) {
    console.error('Error starting scrape:', err)
    scrapingError.value = err.response?.data?.message || 'Failed to start scraping process'
    isScraping.value = false
  }
}

const updateStepStatus = (index: number, status: 'pending' | 'in-progress' | 'completed', message: string) => {
  // Update current step
  scrapingSteps.value[index].status = status
  scrapingSteps.value[index].message = message
  
  // Set next step to in-progress if available
  if (status === 'completed' && index < scrapingSteps.value.length - 1) {
    scrapingSteps.value[index + 1].status = 'in-progress'
  }
}

const closeScrapingModal = () => {
  if (!isScraping.value) {
    showScrapingModal.value = false
    scrapingMessages.value = []
    scrapingError.value = ''
    isScraping.value = false
  }
}

// Fetch data from APIs
const fetchData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // Fetch PMS Raw Inventory
    const pmsRawResponse = await axios.get('/api/db/pms-inventory-raw')
    if (pmsRawResponse.data.status === 'success') {
      pmsRawData.value = pmsRawResponse.data.data
      if (pmsRawData.value.length > 0) {
        pmsRawHeaders.value = Object.keys(pmsRawData.value[0])
      }
    }

    // Fetch PMS Processed Inventory
    const pmsProcessedResponse = await axios.get('/api/db/pms-inventory-processed')
    if (pmsProcessedResponse.data.status === 'success') {
      pmsProcessedData.value = pmsProcessedResponse.data.data
      if (pmsProcessedData.value.length > 0) {
        pmsProcessedHeaders.value = Object.keys(pmsProcessedData.value[0])
      }
    }

    // Fetch Combined Inventory
    const combinedResponse = await axios.get('/api/db/combined-inventory')
    if (combinedResponse.data.status === 'success') {
      // Log all headers from the first row to see what we're working with
      if (combinedResponse.data.data.length > 0) {
        const firstRow = combinedResponse.data.data[0]
        console.log('Original first row:', firstRow)
        console.log('Original keys:', Object.keys(firstRow))
      }
      combinedData.value = combinedResponse.data.data.map((row: Record<string, any>) => {
        // Create a new row object starting with Date
        const newRow: Record<string, any> = {}
        
        // First, find and set the date
        const dateKey = Object.keys(row).find(key => key.toLowerCase().includes('date'))
        if (dateKey) {
          newRow['Date'] = row[dateKey]
        }

        // Room type mappings
        const roomMappings: Record<string, string> = {
          // Occupancy field
          'Occupancy': 'Occ%',
          'occupancy': 'Occ%',
          'OCCUPANCY': 'Occ%',
          
          // Anvaya Rooms
          'The Anvaya Villa': 'AVP',
          'The Anvaya Suite Whirpool': 'ASW',
          'The Anvaya Suite With Pool': 'ASP',
          'The Anvaya Suite No Pool': 'AVS',
          'The Anvaya Residence': 'AVR',
          
          // Beach Front
          'Beach Front Private Suite Room': 'BFS',
          
          // Deluxe Rooms
          'Deluxe Room': 'DLX',
          'Deluxe Pool Access': 'DLP',
          'Deluxe Suite Room': 'DLS',
          
          // Premiere Rooms
          'Premiere Room': 'PRE',
          'Premiere Room Lagoon Access': 'PKL',
          'Premiere Suite Room': 'PRS',
          'Family Premiere Room': 'FPK'
        }

        // Create reverse mapping for tooltips
        const tooltipMappings: Record<string, string> = {}
        Object.entries(roomMappings).forEach(([original, shortened]) => {
          tooltipMappings[shortened] = original
        })
        // Add special cases
        tooltipMappings['Date'] = 'Date'
        tooltipMappings['Occ%'] = 'Occupancy'

        // Process each field in the row
        Object.keys(row).forEach(key => {
          // Skip the date field as we've already handled it
          if (key.toLowerCase().includes('date')) return
          
          // Check if the key matches any of our mappings
          const newKey = roomMappings[key]
          if (newKey) {
            newRow[newKey] = row[key]
          }
        })

        return newRow
      })
      if (combinedData.value.length > 0) {
        // Define the desired column order
        const columnOrder = [
          'Date',
          'Occ%',
          'DLX',
          'PRE',
          'DLP',
          'PKL',
          'FPK',
          'DLS',
          'PRS',
          'AVS',
          'ASW',
          'BFS',
          'ASP',
          'AVR',
          'AVP'
        ]
        
        // Sort the headers according to the desired order
        combinedHeaders.value = columnOrder.filter(header => 
          Object.keys(combinedData.value[0]).includes(header)
        )
        
        // Create and store tooltip mappings
        const tooltipMappings: Record<string, string> = {}
        const roomMappings: Record<string, string> = {
          // Occupancy field
          'Occupancy': 'Occ%',
          'occupancy': 'Occ%',
          'OCCUPANCY': 'Occ%',
          
          // Anvaya Rooms
          'The Anvaya Villa': 'AVP',
          'The Anvaya Suite Whirpool': 'ASW',
          'The Anvaya Suite With Pool': 'ASP',
          'The Anvaya Suite No Pool': 'AVS',
          'The Anvaya Residence': 'AVR',
          
          // Beach Front
          'Beach Front Private Suite Room': 'BFS',
          
          // Deluxe Rooms
          'Deluxe Room': 'DLX',
          'Deluxe Pool Access': 'DLP',
          'Deluxe Suite Room': 'DLS',
          
          // Premiere Rooms
          'Premiere Room': 'PRE',
          'Premiere Room Lagoon Access': 'PKL',
          'Premiere Suite Room': 'PRS',
          'Family Premiere Room': 'FPK'
        }
        Object.entries(roomMappings).forEach(([original, shortened]) => {
          tooltipMappings[shortened] = original
        })
        tooltipMappings['Date'] = 'Date'
        tooltipMappings['Occ%'] = 'Occupancy'
        tooltipMappingsRef.value = tooltipMappings
      }
    }

    // Fetch Inventory Allocation
    const allocationResponse = await axios.get('/api/db/inventory-allocation')
    if (allocationResponse.data.status === 'success') {
      allocationData.value = allocationResponse.data.data
      if (allocationData.value.length > 0) {
        allocationHeaders.value = Object.keys(allocationData.value[0])
      }
    }
  } catch (err: any) {
    console.error('Error fetching data:', err)
    error.value = 'Failed to fetch data. Please make sure the backend server is running.'
  } finally {
    loading.value = false
  }
}

function sortData(data: any[], column: string) {
  if (sortColumn.value === column) {
    // Toggle direction if clicking the same column
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    // Set new column and default to ascending
    sortColumn.value = column
    sortDirection.value = 'asc'
  }

  return [...data].sort((a, b) => {
    let valueA = a[column]
    let valueB = b[column]

    // Handle date sorting
    if (column.toLowerCase().includes('date')) {
      valueA = new Date(valueA).getTime()
      valueB = new Date(valueB).getTime()
    }
    // Handle number sorting
    else if (!isNaN(Number(valueA)) && !isNaN(Number(valueB))) {
      valueA = Number(valueA)
      valueB = Number(valueB)
    }

    if (valueA < valueB) return sortDirection.value === 'asc' ? -1 : 1
    if (valueA > valueB) return sortDirection.value === 'asc' ? 1 : -1
    return 0
  })
}

function getSortIndicator(header: string) {
  if (sortColumn.value !== header) return ''
  return sortDirection.value === 'asc' ? '↑' : '↓'
}

// Export functionality
const exportData = async (type: string, format: 'csv' | 'excel' | 'json') => {
  let data: any[] = []
  let filename = ''

  // Get the appropriate data based on type
  switch (type) {
    case 'pms-raw':
      data = pmsRawData.value
      filename = 'pms_raw_inventory'
      break
    case 'pms-processed':
      data = pmsProcessedData.value
      filename = 'pms_processed_inventory'
      break
    case 'combined':
      data = combinedData.value
      filename = 'combined_inventory'
      break
    case 'allocation':
      data = allocationData.value
      filename = 'inventory_allocation'
      break
    default:
      return
  }

  if (data.length === 0) {
    alert('No data available to export')
    return
  }

  try {
    switch (format) {
      case 'csv':
        // Convert data to CSV
        const csvContent = data.map(row => 
          Object.values(row).map(value => 
            typeof value === 'string' ? `"${value}"` : value
          ).join(',')
        ).join('\n')
        const csvHeaders = Object.keys(data[0]).join(',')
        const csv = `${csvHeaders}\n${csvContent}`
        
        // Create and download CSV file
        const csvBlob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const csvUrl = URL.createObjectURL(csvBlob)
        const csvLink = document.createElement('a')
        csvLink.href = csvUrl
        csvLink.download = `${filename}.csv`
        csvLink.click()
        URL.revokeObjectURL(csvUrl)
        break

      case 'excel':
        // Convert data to Excel
        const worksheet = XLSX.utils.json_to_sheet(data)
        const workbook = XLSX.utils.book_new()
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Data')
        XLSX.writeFile(workbook, `${filename}.xlsx`)
        break

      case 'json':
        // Convert data to JSON
        const jsonContent = JSON.stringify(data, null, 2)
        const jsonBlob = new Blob([jsonContent], { type: 'application/json' })
        const jsonUrl = URL.createObjectURL(jsonBlob)
        const jsonLink = document.createElement('a')
        jsonLink.href = jsonUrl
        jsonLink.download = `${filename}.json`
        jsonLink.click()
        URL.revokeObjectURL(jsonUrl)
        break
    }
  } catch (error) {
    console.error('Error exporting data:', error)
    alert('Error exporting data. Please try again.')
  }
}

onMounted(() => {
  fetchData()
})
</script> 