<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-semibold text-gray-900">Yield Management</h1>
        <div class="flex space-x-4">
          <button
            @click="showCustomConfig = !showCustomConfig"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            {{ showCustomConfig ? 'Hide Custom Config' : 'Show Custom Config' }}
          </button>
          <button
            @click="calculateYield"
            :disabled="isLoading"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              v-if="isLoading"
              class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            {{ isLoading ? 'Calculating...' : 'Calculate Yield' }}
          </button>
        </div>
      </div>

      <!-- Custom Configuration Form -->
      <div v-if="showCustomConfig" class="mb-4 bg-white shadow sm:rounded-lg">
        <div class="px-2 py-2 sm:p-3">
          <!-- Configuration Header -->
          <div class="flex justify-between items-center mb-2">
            <h4 class="text-xs font-medium text-gray-700">Configuration Settings</h4>
            <button
              @click="resetToDefault"
              class="inline-flex items-center px-2 py-1 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Reset to Default
            </button>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-1">
            <!-- Demand Configuration -->
            <div class="col-span-2 md:col-span-4">
              <h4 class="text-xs font-medium text-gray-700 mb-0.5">Demand Configuration</h4>
              <div class="grid grid-cols-2 gap-1">
                <div>
                  <label class="block text-xs font-medium text-gray-700">Demand Bins</label>
                  <input
                    v-model="customConfig.demand_bins"
                    type="text"
                    class="mt-0.5 block w-full border border-gray-300 rounded-md shadow-sm py-0.5 px-2 text-xs focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="[0, 70, 85, 100]"
                  />
                  <p class="mt-0.5 text-xs text-gray-500 font-mono">Thresholds for demand levels (e.g., [0,70,85,100] for Low/Medium/High)</p>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-700">Demand Labels</label>
                  <input
                    v-model="customConfig.demand_labels"
                    type="text"
                    class="mt-0.5 block w-full border border-gray-300 rounded-md shadow-sm py-0.5 px-2 text-xs focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="['Low', 'Medium', 'High']"
                  />
                  <p class="mt-0.5 text-xs text-gray-500 font-mono">Labels for each demand level (e.g., ['Low','Medium','High'])</p>
                </div>
              </div>
            </div>

            <!-- Separator -->
            <div class="col-span-2 md:col-span-4">
              <div class="border-t border-gray-200 my-2"></div>
            </div>

            <!-- Threshold Configuration -->
            <div class="col-span-2 md:col-span-4">
              <h4 class="text-xs font-medium text-gray-700 mb-0.5">Threshold Configuration</h4>
              <div class="grid grid-cols-2 gap-1">
                <div>
                  <label class="block text-xs font-medium text-gray-700">Very Low (%)</label>
                  <input
                    v-model.number="customConfig.very_low_threshold_pct"
                    type="number"
                    step="0.01"
                    class="mt-0.5 block w-full border border-gray-300 rounded-md shadow-sm py-0.5 px-2 text-xs focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <p class="mt-0.5 text-xs text-gray-500 font-mono">Percentage threshold for very low inventory level</p>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-700">Low (%)</label>
                  <input
                    v-model.number="customConfig.low_threshold_pct"
                    type="number"
                    step="0.01"
                    class="mt-0.5 block w-full border border-gray-300 rounded-md shadow-sm py-0.5 px-2 text-xs focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <p class="mt-0.5 text-xs text-gray-500 font-mono">Percentage threshold for low inventory level</p>
                </div>
              </div>
            </div>

            <!-- Separator -->
            <div class="col-span-2 md:col-span-4">
              <div class="border-t border-gray-200 my-2"></div>
            </div>

            <!-- Room Capacity Configuration -->
            <div class="col-span-2 md:col-span-4">
              <h4 class="text-xs font-medium text-gray-700 mb-0.5">Room Capacity</h4>
              <div class="grid grid-cols-2 gap-1">
                <div>
                  <label class="block text-xs font-medium text-gray-700">Deluxe Room Cap</label>
                  <input
                    v-model.number="customConfig.room_caps['Deluxe Room']"
                    type="number"
                    class="mt-0.5 block w-full border border-gray-300 rounded-md shadow-sm py-0.5 px-2 text-xs focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <p class="mt-0.5 text-xs text-gray-500 font-mono">Maximum number of Deluxe rooms available</p>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-700">Premiere Room Cap</label>
                  <input
                    v-model.number="customConfig.room_caps['Premiere Room']"
                    type="number"
                    class="mt-0.5 block w-full border border-gray-300 rounded-md shadow-sm py-0.5 px-2 text-xs focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <p class="mt-0.5 text-xs text-gray-500 font-mono">Maximum number of Premiere rooms available</p>
                </div>
              </div>
            </div>

            <!-- Separator -->
            <div class="col-span-2 md:col-span-4">
              <div class="border-t border-gray-200 my-2"></div>
            </div>

            <!-- Deluxe Override Configuration -->
            <div class="col-span-2 md:col-span-4">
              <h4 class="text-xs font-medium text-gray-700 mb-0.5">Deluxe Override</h4>
              <div class="grid grid-cols-3 gap-1">
                <div>
                  <label class="block text-xs font-medium text-gray-700">Occupancy (%)</label>
                  <input
                    v-model.number="customConfig.deluxe_override_occupancy"
                    type="number"
                    class="mt-0.5 block w-full border border-gray-300 rounded-md shadow-sm py-0.5 px-2 text-xs focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <p class="mt-0.5 text-xs text-gray-500 font-mono">Occupancy percentage threshold for Deluxe override</p>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-700">Premiere</label>
                  <input
                    v-model.number="customConfig.deluxe_override_premiere"
                    type="number"
                    class="mt-0.5 block w-full border border-gray-300 rounded-md shadow-sm py-0.5 px-2 text-xs focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <p class="mt-0.5 text-xs text-gray-500 font-mono">Premiere threshold for Deluxe override</p>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-700">Amount</label>
                  <input
                    v-model.number="customConfig.deluxe_override_amount"
                    type="number"
                    class="mt-0.5 block w-full border border-gray-300 rounded-md shadow-sm py-0.5 px-2 text-xs focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <p class="mt-0.5 text-xs text-gray-500 font-mono">Number of Deluxe rooms to override</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="mb-6 bg-red-50 border-l-4 border-red-400 p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Data Table -->
      <div v-if="allocationData.length > 0" class="mt-8 flex flex-col">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-medium text-gray-900">Inventory Allocation Data</h3>
          <div class="flex space-x-1">
            <button
              @click="exportData('csv')"
              class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
              title="Export CSV"
            >
              <i class="fas fa-file-csv"></i>
            </button>
            <button
              @click="exportData('excel')"
              class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
              title="Export Excel"
            >
              <i class="fas fa-file-excel"></i>
            </button>
            <button
              @click="exportData('json')"
              class="inline-flex items-center justify-center w-8 h-8 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
              title="Export JSON"
            >
              <i class="fas fa-file-code"></i>
            </button>
          </div>
        </div>
        <div class="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div class="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <div class="max-h-[600px] overflow-y-auto">
                <table class="min-w-full divide-y divide-gray-300">
                  <thead class="bg-indigo-50 sticky top-0 z-10">
                    <tr>
                      <th
                        v-for="header in tableHeaders"
                        :key="header"
                        scope="col"
                        class="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-indigo-700 sm:pl-6 bg-indigo-50 cursor-pointer hover:bg-indigo-100"
                        @click="allocationData = sortData(allocationData, header)"
                      >
                        <div class="flex items-center justify-between">
                          <span>{{ header }} {{ getSortIndicator(header) }}</span>
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-200 bg-white">
                    <tr v-for="(row, index) in allocationData" :key="index">
                      <td
                        v-for="header in tableHeaders"
                        :key="header"
                        class="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6"
                        :class="getCellStyle(row[header], header)"
                      >
                        {{ formatValue(row[header]) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- No Data Message -->
      <div v-else-if="!isLoading" class="text-center py-12">
        <svg
          class="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
          />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No data available</h3>
        <p class="mt-1 text-sm text-gray-500">Click the "Calculate Yield" button to generate inventory allocation data.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from '../plugins/axios'
import * as XLSX from 'xlsx'
import '@fortawesome/fontawesome-free/css/all.css'

const isLoading = ref(false)
const error = ref<string | null>(null)
const allocationData = ref<any[]>([])
const showCustomConfig = ref(false)

interface CustomConfig {
  demand_bins: number[] | string;
  demand_labels: string[] | string;
  very_low_threshold_pct: number;
  low_threshold_pct: number;
  room_caps: {
    'Deluxe Room': number;
    'Premiere Room': number;
  };
  deluxe_override_occupancy: number;
  deluxe_override_premiere: number;
  deluxe_override_amount: number;
}

const defaultConfig: CustomConfig = {
  demand_bins: [0, 70, 85, 100],
  demand_labels: ['Low', 'Medium', 'High'],
  very_low_threshold_pct: 5,
  low_threshold_pct: 20,
  room_caps: {
    'Deluxe Room': 160,
    'Premiere Room': 260
  },
  deluxe_override_occupancy: 70,
  deluxe_override_premiere: 61,
  deluxe_override_amount: 2
}

const customConfig = ref<CustomConfig>({ ...defaultConfig })

const tableHeaders = [
  'Date',
  'DayOfWeek',
  'Season',
  'Occupancy',
  'DemandLevel',
  'Deluxe Remaining Inventory',
  'Deluxe Online Inventory',
  'Deluxe BAR Rate',
  'Premiere Remaining Inventory',
  'Premiere Online Inventory',
  'Premiere BAR Rate'
]

const calculateYield = async () => {
  isLoading.value = true
  error.value = null
  console.log('Starting yield calculation...')

  try {
    // Parse demand bins and labels from string input
    let parsedConfig
    try {
      // Helper function to parse array input
      const parseArrayInput = (input: string | any[]): any[] => {
        if (Array.isArray(input)) return input
        const str = input.toString().trim()
        // Try parsing as JSON first
        try {
          return JSON.parse(str.replace(/'/g, '"'))
        } catch {
          // If JSON parsing fails, try splitting by comma
          return str.split(',').map(item => item.trim())
        }
      }

      // Validate room_caps
      const roomCaps = customConfig.value.room_caps
      if (!roomCaps['Deluxe Room'] || !roomCaps['Premiere Room']) {
        throw new Error('Room capacities must be specified for both Deluxe Room and Premiere Room')
      }

      parsedConfig = {
        ...customConfig.value,
        demand_bins: parseArrayInput(customConfig.value.demand_bins).map(Number),
        demand_labels: parseArrayInput(customConfig.value.demand_labels),
        room_caps: {
          'Deluxe Room': Number(roomCaps['Deluxe Room']),
          'Premiere Room': Number(roomCaps['Premiere Room'])
        }
      }

      // Validate numeric values
      if (isNaN(parsedConfig.very_low_threshold_pct) || 
          isNaN(parsedConfig.low_threshold_pct) || 
          isNaN(parsedConfig.deluxe_override_occupancy) || 
          isNaN(parsedConfig.deluxe_override_premiere) || 
          isNaN(parsedConfig.deluxe_override_amount)) {
        throw new Error('All numeric values must be valid numbers')
      }

      console.log('Parsed config:', parsedConfig)
    } catch (parseError) {
      console.error('Error parsing config:', parseError)
      error.value = parseError instanceof Error ? parseError.message : 'Invalid configuration format'
      return
    }

    // Trigger yield calculation
    console.log('Sending POST request to /api/custom-yield with config:', parsedConfig)
    const response = await axios.post('/api/custom-yield', parsedConfig)
    console.log('Yield calculation response:', response.data)
    
    // Fetch the allocation data
    console.log('Fetching inventory allocation data...')
    const dataResponse = await axios.get('/api/db/inventory-allocation')
    console.log('Raw inventory allocation data:', dataResponse.data)
    if (dataResponse.data.status === 'success' && Array.isArray(dataResponse.data.data)) {
      console.log('Number of records:', dataResponse.data.data.length)
      console.log('First record:', dataResponse.data.data[0])
      allocationData.value = dataResponse.data.data
    } else {
      console.error('Unexpected data format:', dataResponse.data)
      error.value = 'Received data in unexpected format'
    }
  } catch (err: any) {
    console.error('Full error object:', err)
    console.error('Error response:', err.response)
    const errorMessage = err.response?.data?.message || 'Failed to calculate yield'
    if (errorMessage.includes('Combined inventory database not found')) {
      error.value = 'Please run the "Combine Inventory" process first. This requires both PMS and CM inventory data to be processed.'
    } else if (errorMessage.includes('Failed to create inventory allocation database')) {
      error.value = 'Failed to create the inventory allocation database. Please check if you have write permissions in the data directory.'
    } else if (errorMessage.includes('No data was written')) {
      error.value = 'No data was written to the inventory allocation database. Please check if the combined inventory data is valid.'
    } else {
      error.value = errorMessage
    }
    console.error('Error calculating yield:', err)
  } finally {
    isLoading.value = false
  }
}

const formatValue = (value: any) => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') {
    if (value % 1 === 0) return value.toLocaleString()
    return value.toFixed(2)
  }
  if (value instanceof Date || (typeof value === 'string' && !isNaN(Date.parse(value)))) {
    const date = new Date(value)
    const day = date.getDate().toString().padStart(2, '0')
    const month = date.toLocaleString('en-US', { month: 'short' })
    const year = date.getFullYear().toString().slice(-2)
    return `${day} ${month} '${year}`
  }
  return value
}

const getCellStyle = (value: any, header: string) => {
  if (typeof value === 'number') {
    if (header.includes('Occupancy')) {
      if (value >= 70) return 'text-green-600'
      if (value >= 50) return 'text-yellow-600'
      return 'text-red-600'
    }
    if (header.includes('Room')) {
      if (value > 0) return 'text-green-600'
      if (value < 0) return 'text-red-600'
    }
  }
  if (header.includes('BAR')) {
    return 'font-mono'
  }
  return ''
}

const resetToDefault = () => {
  customConfig.value = {
    demand_bins: Array.isArray(defaultConfig.demand_bins) ? [...defaultConfig.demand_bins] : defaultConfig.demand_bins,
    demand_labels: Array.isArray(defaultConfig.demand_labels) ? [...defaultConfig.demand_labels] : defaultConfig.demand_labels,
    very_low_threshold_pct: defaultConfig.very_low_threshold_pct,
    low_threshold_pct: defaultConfig.low_threshold_pct,
    room_caps: {
      'Deluxe Room': defaultConfig.room_caps['Deluxe Room'],
      'Premiere Room': defaultConfig.room_caps['Premiere Room']
    },
    deluxe_override_occupancy: defaultConfig.deluxe_override_occupancy,
    deluxe_override_premiere: defaultConfig.deluxe_override_premiere,
    deluxe_override_amount: defaultConfig.deluxe_override_amount
  }
}

onMounted(async () => {
  console.log('Yielder component mounted')
  try {
    console.log('Fetching initial inventory allocation data...')
    const response = await axios.get('/api/db/inventory-allocation')
    console.log('Initial data response:', response.data)
    if (response.data.status === 'success' && Array.isArray(response.data.data)) {
      console.log('Number of records:', response.data.data.length)
      console.log('First record:', response.data.data[0])
      allocationData.value = response.data.data
    } else {
      console.error('Unexpected data format:', response.data)
    }
  } catch (err: any) {
    console.error('Error fetching initial data:', err)
    console.error('Error response:', err.response)
  }
})

// Add these refs for sorting
const sortColumn = ref('')
const sortDirection = ref<'asc' | 'desc'>('asc')

// Add sorting function
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

// Update export function to maintain column order
const exportData = async (format: 'csv' | 'excel' | 'json') => {
  if (allocationData.value.length === 0) {
    alert('No data available to export')
    return
  }

  try {
    // Create ordered data array
    const orderedData = allocationData.value.map(row => {
      const orderedRow: Record<string, any> = {}
      tableHeaders.forEach(header => {
        orderedRow[header] = row[header]
      })
      return orderedRow
    })

    switch (format) {
      case 'csv':
        // Convert data to CSV with ordered columns
        const csvContent = orderedData.map(row => 
          tableHeaders.map(header => {
            const value = row[header]
            return typeof value === 'string' ? `"${value}"` : value
          }).join(',')
        ).join('\n')
        const csvHeaders = tableHeaders.join(',')
        const csv = `${csvHeaders}\n${csvContent}`
        
        // Create and download CSV file
        const csvBlob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const csvUrl = URL.createObjectURL(csvBlob)
        const csvLink = document.createElement('a')
        csvLink.href = csvUrl
        csvLink.download = 'inventory_allocation.csv'
        csvLink.click()
        URL.revokeObjectURL(csvUrl)
        break

      case 'excel':
        // Convert data to Excel with ordered columns
        const worksheet = XLSX.utils.json_to_sheet(orderedData)
        const workbook = XLSX.utils.book_new()
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Data')
        XLSX.writeFile(workbook, 'inventory_allocation.xlsx')
        break

      case 'json':
        // Convert data to JSON with ordered columns
        const jsonContent = JSON.stringify(orderedData, null, 2)
        const jsonBlob = new Blob([jsonContent], { type: 'application/json' })
        const jsonUrl = URL.createObjectURL(jsonBlob)
        const jsonLink = document.createElement('a')
        jsonLink.href = jsonUrl
        jsonLink.download = 'inventory_allocation.json'
        jsonLink.click()
        URL.revokeObjectURL(jsonUrl)
        break
    }
  } catch (error) {
    console.error('Error exporting data:', error)
    alert('Error exporting data. Please try again.')
  }
}
</script> 