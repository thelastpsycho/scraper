<template>
  <div class="h-screen bg-app-primary text-app-tertiary p-4 flex flex-col">
    <div class="w-full h-full flex flex-col bg-white rounded-xl shadow-md overflow-hidden">
      <!-- Header & Controls -->
      <div class="p-4 border-b border-gray-200 flex-shrink-0">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 class="text-xl font-bold text-app-tertiary">Yield Management</h1>
            <p class="text-sm text-gray-500">Optimize inventory with custom strategies.</p>
          </div>
          <div class="flex items-center space-x-2 flex-shrink-0">
            <button
              @click="calculateYield"
              :disabled="isLoading"
              class="flex items-center justify-center bg-app-accent text-white py-2 px-4 rounded-md hover:bg-opacity-90 transition-all disabled:opacity-50 font-bold text-sm shadow-sm"
            >
              <svg v-if="isLoading" class="animate-spin -ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <CalculatorIcon v-else class="h-5 w-5 mr-1.5" />
              {{ isLoading ? 'Calculating...' : 'Calculate' }}
            </button>
            <button @click="showCustomConfig = !showCustomConfig" class="p-2 border border-gray-300 rounded-md text-gray-600 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-app-accent" :class="{'bg-gray-100': showCustomConfig}" title="Toggle Configuration">
              <AdjustmentsHorizontalIcon class="h-5 w-5" />
            </button>
            <button @click="resetToDefault" v-if="showCustomConfig" class="p-2 border border-gray-300 rounded-md text-gray-600 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-app-accent" title="Reset Configuration">
              <ArrowPathIcon class="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      <!-- Configuration Form (Collapsible) -->
      <div v-if="showCustomConfig" class="p-6 border-b border-gray-200 flex-shrink-0">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Left Column -->
          <div class="space-y-6">
            <!-- Demand Configuration -->
            <div>
              <h4 class="text-base font-semibold text-app-tertiary flex items-center">
                <SignalIcon class="h-5 w-5 mr-2 text-app-accent" />
                Demand Configuration
              </h4>
              <p class="text-xs text-gray-500 mt-1">Define how demand levels are calculated based on occupancy.</p>
              <div class="mt-3 space-y-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Demand Bins</label>
                  <input v-model="customConfig.demand_bins" type="text" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm focus:outline-none focus:ring-app-accent focus:border-app-accent" placeholder="[0, 70, 85, 100]">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">Demand Labels</label>
                  <input v-model="customConfig.demand_labels" type="text" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm focus:outline-none focus:ring-app-accent focus:border-app-accent" placeholder="['Low', 'Medium', 'High']">
                </div>
              </div>
            </div>

            <!-- Threshold Configuration -->
            <div>
              <h4 class="text-base font-semibold text-app-tertiary flex items-center">
                <ScaleIcon class="h-5 w-5 mr-2 text-app-accent" />
                Inventory Thresholds
              </h4>
              <p class="text-xs text-gray-500 mt-1">Set percentage thresholds for low inventory warnings.</p>
              <div class="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Very Low (%)</label>
                  <input v-model.number="customConfig.very_low_threshold_pct" type="number" step="0.01" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm focus:outline-none focus:ring-app-accent focus:border-app-accent">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">Low (%)</label>
                  <input v-model.number="customConfig.low_threshold_pct" type="number" step="0.01" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm focus:outline-none focus:ring-app-accent focus:border-app-accent">
                </div>
              </div>
            </div>
          </div>

          <!-- Right Column -->
          <div class="space-y-6">
            <!-- Room Capacity Configuration -->
            <div>
              <h4 class="text-base font-semibold text-app-tertiary flex items-center">
                <BuildingOffice2Icon class="h-5 w-5 mr-2 text-app-accent" />
                Room Capacity
              </h4>
              <p class="text-xs text-gray-500 mt-1">Specify the total number of rooms available for each type.</p>
              <div class="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Deluxe Rooms</label>
                  <input v-model.number="customConfig.room_caps['Deluxe Room']" type="number" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm focus:outline-none focus:ring-app-accent focus:border-app-accent">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">Premiere Rooms</label>
                  <input v-model.number="customConfig.room_caps['Premiere Room']" type="number" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm focus:outline-none focus:ring-app-accent focus:border-app-accent">
                </div>
              </div>
            </div>

            <!-- Deluxe Override Configuration -->
            <div>
              <h4 class="text-base font-semibold text-app-tertiary flex items-center">
                <WrenchScrewdriverIcon class="h-5 w-5 mr-2 text-app-accent" />
                Deluxe Override Rule
              </h4>
              <p class="text-xs text-gray-500 mt-1">Define rules to automatically adjust Deluxe inventory.</p>
              <div class="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Occupancy (%)</label>
                  <input v-model.number="customConfig.deluxe_override_occupancy" type="number" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm focus:outline-none focus:ring-app-accent focus:border-app-accent">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">Premiere Min</label>
                  <input v-model.number="customConfig.deluxe_override_premiere" type="number" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm focus:outline-none focus:ring-app-accent focus:border-app-accent">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">Amount</label>
                  <input v-model.number="customConfig.deluxe_override_amount" type="number" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm focus:outline-none focus:ring-app-accent focus:border-app-accent">
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Status/Error Message -->
      <div v-if="error" class="p-4 flex-shrink-0">
        <div class="bg-red-100 text-red-800 rounded-md text-sm font-medium flex items-start p-3">
          <ExclamationTriangleIcon class="h-5 w-5 mr-2 flex-shrink-0" />
          <span>{{ error }}</span>
        </div>
      </div>

      <!-- Data Table -->
      <div class="p-6 flex-1 flex flex-col overflow-hidden">
        <div v-if="allocationData.length > 0" class="h-full flex flex-col">
          <div class="flex flex-wrap items-center justify-between gap-4 mb-4 flex-shrink-0">
            <div>
              <h3 class="text-lg font-semibold text-app-tertiary">Inventory Allocation Data</h3>
              <p class="text-sm text-gray-500">Results from the yield calculation.</p>
            </div>
            <div class="flex items-center space-x-2">
              <p class="text-sm font-medium text-gray-600">Export:</p>
              <button @click="exportData('csv')" class="p-2 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors" title="Export CSV">
                <DocumentArrowDownIcon class="h-5 w-5" />
              </button>
              <button @click="exportData('excel')" class="p-2 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors" title="Export Excel">
                <TableCellsIcon class="h-5 w-5" />
              </button>
              <button @click="exportData('json')" class="p-2 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors" title="Export JSON">
                <CodeBracketIcon class="h-5 w-5" />
              </button>
            </div>
          </div>
          <div class="flex-1 overflow-y-auto border border-gray-200 rounded-lg">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th v-for="header in tableHeaders" :key="header.key" scope="col" class="py-3.5 pl-6 pr-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100 group" @click="allocationData = sortData(allocationData, header.key)">
                    <div class="flex items-center space-x-2">
                      <component :is="header.icon" class="h-4 w-4 text-gray-400 group-hover:text-app-accent" />
                      <span>{{ header.label }}</span>
                      <span v-if="sortColumn === header.key" class="text-xs">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white">
                <tr v-for="(row, index) in allocationData" :key="index" class="hover:bg-gray-50 transition-colors duration-150">
                  <td v-for="header in tableHeaders" :key="header.key" class="whitespace-nowrap py-4 pl-6 pr-3 text-sm" :class="getCellStyle(row[header.key], header.key)">
                    {{ formatValue(row[header.key], header.key) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else-if="!isLoading" class="flex-1 flex flex-col items-center justify-center text-gray-500">
          <DocumentMagnifyingGlassIcon class="mx-auto h-12 w-12" />
          <h3 class="mt-2 text-base font-medium">No Data Available</h3>
          <p class="mt-1 text-sm">Click "Calculate Yield" to generate inventory allocation data.</p>
        </div>
        <div v-if="isLoading" class="flex-1 flex flex-col items-center justify-center">
          <svg class="animate-spin mx-auto h-8 w-8 text-app-accent" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="mt-4 text-sm text-gray-600">Calculating yield, please wait...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, shallowRef } from 'vue'
import axios from '../plugins/axios'
import * as XLSX from 'xlsx'
import {
  CalculatorIcon,
  ArrowPathIcon,
  AdjustmentsHorizontalIcon,
  ExclamationTriangleIcon,
  DocumentArrowDownIcon,
  TableCellsIcon,
  CodeBracketIcon,
  DocumentMagnifyingGlassIcon,
  CalendarDaysIcon,
  SparklesIcon,
  SunIcon,
  ChartPieIcon,
  SignalIcon,
  BuildingOfficeIcon,
  BuildingStorefrontIcon,
  BanknotesIcon,
  WrenchScrewdriverIcon,
  ScaleIcon,
  BuildingOffice2Icon,
} from '@heroicons/vue/24/outline'

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

const tableHeaders = shallowRef([
  { key: 'Date', label: 'Date', icon: CalendarDaysIcon },
  { key: 'DayOfWeek', label: 'Day', icon: SparklesIcon },
  { key: 'Season', label: 'Season', icon: SunIcon },
  { key: 'Occupancy', label: 'Occupancy', icon: ChartPieIcon },
  { key: 'DemandLevel', label: 'Demand', icon: SignalIcon },
  { key: 'Deluxe Remaining Inventory', label: 'Deluxe Avail', icon: BuildingOfficeIcon },
  { key: 'Deluxe Online Inventory', label: 'Deluxe Online', icon: BuildingStorefrontIcon },
  { key: 'Deluxe BAR Rate', label: 'Deluxe BAR', icon: BanknotesIcon },
  { key: 'Premiere Remaining Inventory', label: 'Premiere Avail', icon: BuildingOfficeIcon },
  { key: 'Premiere Online Inventory', label: 'Premiere Online', icon: BuildingStorefrontIcon },
  { key: 'Premiere BAR Rate', label: 'Premiere BAR', icon: BanknotesIcon },
])

const calculateYield = async () => {
  isLoading.value = true
  error.value = null

  try {
    let parsedConfig;
    try {
      const parseArrayInput = (input: string | any[]): any[] => {
        if (Array.isArray(input)) return input
        const str = input.toString().trim()
        try {
          return JSON.parse(str.replace(/'/g, '"'))
        } catch {
          return str.split(',').map(item => item.trim())
        }
      }

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

      if (isNaN(parsedConfig.very_low_threshold_pct) || 
          isNaN(parsedConfig.low_threshold_pct) || 
          isNaN(parsedConfig.deluxe_override_occupancy) || 
          isNaN(parsedConfig.deluxe_override_premiere) || 
          isNaN(parsedConfig.deluxe_override_amount)) {
        throw new Error('All numeric values must be valid numbers')
      }
    } catch (parseError) {
      error.value = parseError instanceof Error ? parseError.message : 'Invalid configuration format'
      return
    }

    await axios.post('/api/custom-yield', parsedConfig)
    
    const dataResponse = await axios.get('/api/db/inventory-allocation')
    if (dataResponse.data.status === 'success' && Array.isArray(dataResponse.data.data)) {
      allocationData.value = dataResponse.data.data
    } else {
      error.value = 'Received data in unexpected format'
    }
  } catch (err: any) {
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
  } finally {
    isLoading.value = false
  }
}

const formatValue = (value: any, key: string) => {
  if (value === null || value === undefined) return '-'
  if (key.toLowerCase().includes('rate')) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(value);
  }
  if (typeof value === 'number') {
    if (key.toLowerCase().includes('occupancy')) return `${value.toFixed(1)}%`
    return value.toLocaleString()
  }
  if (key.toLowerCase().includes('date')) {
    const date = new Date(value)
    const day = date.getDate().toString().padStart(2, '0')
    const month = date.toLocaleString('en-US', { month: 'short' })
    return `${day} ${month}`
  }
  return value
}

const getCellStyle = (value: any, key: string) => {
  const styles: string[] = ['text-gray-800']
  if (typeof value === 'number') {
    if (key.toLowerCase().includes('occupancy')) {
      if (value >= 85) styles.push('text-green-600', 'font-semibold')
      else if (value >= 70) styles.push('text-yellow-600', 'font-semibold')
      else styles.push('text-red-600', 'font-semibold')
    }
    if (key.toLowerCase().includes('inventory')) {
      if (value > 10) styles.push('text-green-700')
      else if (value > 0) styles.push('text-yellow-700')
      else styles.push('text-red-700', 'font-bold')
    }
  }
  if (key.toLowerCase().includes('rate')) {
    styles.push('font-mono', 'text-sm')
  }
  return styles.join(' ')
}

const resetToDefault = () => {
  customConfig.value = { ...defaultConfig };
}

onMounted(async () => {
  try {
    const response = await axios.get('/api/db/inventory-allocation')
    if (response.data.status === 'success' && Array.isArray(response.data.data)) {
      allocationData.value = response.data.data
    }
  } catch (err: any) {
    // Silently fail on mount, let user trigger calculation
  }
})

const sortColumn = ref('Date')
const sortDirection = ref<'asc' | 'desc'>('asc')

function sortData(data: any[], column: string) {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortDirection.value = 'asc'
  }

  return [...data].sort((a, b) => {
    let valueA = a[column]
    let valueB = b[column]

    if (column.toLowerCase().includes('date')) {
      valueA = new Date(valueA).getTime()
      valueB = new Date(valueB).getTime()
    }
    else if (!isNaN(Number(valueA)) && !isNaN(Number(valueB))) {
      valueA = Number(valueA)
      valueB = Number(valueB)
    }

    if (valueA < valueB) return sortDirection.value === 'asc' ? -1 : 1
    if (valueA > valueB) return sortDirection.value === 'asc' ? 1 : -1
    return 0
  })
}

const exportData = async (format: 'csv' | 'excel' | 'json') => {
  if (allocationData.value.length === 0) {
    alert('No data available to export')
    return
  }

  try {
    const exportHeaders = tableHeaders.value.map(h => h.key);
    const orderedData = allocationData.value.map(row => {
      const orderedRow: Record<string, any> = {}
      exportHeaders.forEach(header => {
        orderedRow[header] = row[header]
      })
      return orderedRow
    })

    switch (format) {
      case 'csv':
        const csvContent = orderedData.map(row => 
          exportHeaders.map(header => {
            const value = row[header]
            return typeof value === 'string' ? `"${value}"` : value
          }).join(',')
        ).join('\n')
        const csvHeaders = exportHeaders.join(',')
        const csv = `${csvHeaders}\n${csvContent}`
        
        const csvBlob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const csvUrl = URL.createObjectURL(csvBlob)
        const csvLink = document.createElement('a')
        csvLink.href = csvUrl
        csvLink.download = 'inventory_allocation.csv'
        csvLink.click()
        URL.revokeObjectURL(csvUrl)
        break

      case 'excel':
        const worksheet = XLSX.utils.json_to_sheet(orderedData)
        const workbook = XLSX.utils.book_new()
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Data')
        XLSX.writeFile(workbook, 'inventory_allocation.xlsx')
        break

      case 'json':
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
    alert('Error exporting data. Please try again.')
  }
}
</script>