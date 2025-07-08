<template>
  <div class="h-screen bg-app-primary text-app-tertiary p-4 flex flex-col">
    <div class="w-full h-full flex flex-col bg-white rounded-xl shadow-md overflow-hidden">
      <!-- Loading state -->
      <div v-if="loading" class="flex-1 flex flex-col items-center justify-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-app-accent"></div>
        <p class="mt-4 text-app-tertiary font-semibold">Loading data...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="p-6">
        <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-md" role="alert">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <p class="font-medium">{{ error }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Data Content -->
      <template v-else>
        <!-- Compact Header & Tabs -->
        <div class="p-4 border-b border-gray-200 flex-shrink-0">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 class="text-xl font-bold text-app-tertiary">Data Overview</h1>
              <p class="text-sm text-gray-500">Explore your scraped and processed inventory data.</p>
            </div>
            <div class="bg-gray-100 p-1.5 rounded-lg flex space-x-1">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="activeTab = tab.id"
                :class="[
                  activeTab === tab.id
                    ? 'bg-white text-app-accent shadow-sm'
                    : 'text-gray-600 hover:bg-white/60 hover:text-gray-800',
                  'whitespace-nowrap py-2 px-3 rounded-md font-medium text-xs transition-all duration-200 ease-in-out flex items-center'
                ]"
              >
                <component :is="tab.icon" class="h-4 w-4 mr-1.5" />
                <span>{{ tab.name }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Tab content -->
        <div class="p-6 flex-1 flex flex-col overflow-hidden">
          <div v-for="tab in tabs" :key="`${tab.id}-content`" class="h-full">
            <div v-if="activeTab === tab.id" class="h-full flex flex-col">
              <div class="flex flex-wrap items-center justify-between gap-4 mb-4 flex-shrink-0">
                <div>
                  <h3 class="text-lg font-semibold text-app-tertiary">{{ tab.name }}</h3>
                  <p class="text-sm text-gray-500">{{ tab.description }}</p>
                </div>
                <div class="flex items-center space-x-2">
                   <button @click="exportData(tab.id, 'csv')" class="p-2 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors" title="Export CSV">
                    <DocumentArrowDownIcon class="h-5 w-5" />
                  </button>
                  <button @click="exportData(tab.id, 'excel')" class="p-2 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors" title="Export Excel">
                    <TableCellsIcon class="h-5 w-5" />
                  </button>
                  <button @click="exportData(tab.id, 'json')" class="p-2 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors" title="Export JSON">
                    <CodeBracketIcon class="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div v-if="getDataForTab(tab.id).length === 0" class="flex-1 flex flex-col items-center justify-center text-gray-500">
                <p>No data available for this view.</p>
                <p class="text-sm">Please ensure the required data processing steps have been completed.</p>
              </div>

              <div v-else class="flex-1 overflow-y-auto border border-gray-200 rounded-lg">
                <table class="min-w-full divide-y divide-gray-200 text-sm">
                  <thead class="bg-gray-50 sticky top-0 z-10">
                    <tr>
                      <th v-for="header in getHeadersForTab(tab.id)" :key="header" scope="col" class="py-3.5 px-4 text-left font-semibold text-gray-900 cursor-pointer hover:bg-gray-100 group" @click="sortTab(tab.id, header)">
                        <div class="flex items-center space-x-2">
                          <span>{{ header.replace(/_/g, ' ') }}</span>
                          <span v-if="sortColumn === header">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-200 bg-white">
                    <tr v-for="(row, index) in getDataForTab(tab.id)" :key="index" class="hover:bg-gray-50 transition-colors">
                      <td v-for="header in getHeadersForTab(tab.id)" :key="header" class="whitespace-nowrap px-4 py-3 font-mono" :class="getCellClass(row[header])">
                        {{ formatValue(row[header], header) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from '../plugins/axios'
import * as XLSX from 'xlsx'
import {
  TableCellsIcon,
  AdjustmentsHorizontalIcon,
  ArrowsRightLeftIcon,
  CalculatorIcon,
  DocumentArrowDownIcon,
  CodeBracketIcon,
} from '@heroicons/vue/24/outline'

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
  { id: 'pms-raw', name: 'PMS Raw', icon: TableCellsIcon, description: 'Raw inventory data from the PMS system.' },
  { id: 'pms-processed', name: 'PMS Processed', icon: AdjustmentsHorizontalIcon, description: 'Processed and cleaned inventory data from the PMS system.' },
  { id: 'combined', name: 'Combined', icon: ArrowsRightLeftIcon, description: 'Combined inventory from all available sources.' },
  { id: 'allocation', name: 'Allocation', icon: CalculatorIcon, description: 'Calculated daily inventory allocation and BAR rates.' }
]
const activeTab = ref('pms-raw')

// Sorting refs
const sortColumn = ref('')
const sortDirection = ref<'asc' | 'desc'>('asc')

const tooltipMappingsRef = ref<Record<string, string>>({})

// Data Accessors
const getDataForTab = (tabId: string) => {
  switch (tabId) {
    case 'pms-raw': return pmsRawData.value;
    case 'pms-processed': return pmsProcessedData.value;
    case 'combined': return combinedData.value;
    case 'allocation': return allocationData.value;
    default: return [];
  }
}

const getHeadersForTab = (tabId: string) => {
  switch (tabId) {
    case 'pms-raw': return pmsRawHeaders.value;
    case 'pms-processed': return pmsProcessedHeaders.value;
    case 'combined': return combinedHeaders.value;
    case 'allocation': return allocationHeaders.value;
    default: return [];
  }
}

// Formatting functions
const formatValue = (value: any, key: string) => {
  if (value === null || value === undefined) return '-'
  if (key && key.toLowerCase().includes('date')) {
    const d = new Date(value)
    if (isNaN(d.getTime())) return value
    const day = d.getDate().toString().padStart(2, '0')
    const month = d.toLocaleString('en-US', { month: 'short' })
    const year = d.getFullYear().toString().slice(-2)
    return `${day}-${month}-${year}`
  }
  return value
}

const getCellClass = (value: any) => {
  const num = Number(value)
  if (isNaN(num)) return 'text-gray-700'
  
  if (num < 0) return 'text-red-600 font-semibold'
  if (num === 0) return 'text-orange-600 font-semibold'
  if (num >= 1 && num <= 5) return 'text-yellow-600'
  
  return 'text-gray-800'
}

// Sorting logic
const sortTab = (tabId: string, column: string) => {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortDirection.value = 'asc'
  }

  const sortable = getDataForTab(tabId);
  sortable.sort((a, b) => {
    let valA = a[column];
    let valB = b[column];

    if (column.toLowerCase().includes('date')) {
      valA = new Date(valA).getTime();
      valB = new Date(valB).getTime();
    }

    const numA = Number(valA);
    const numB = Number(valB);
    if (!isNaN(numA) && !isNaN(numB)) {
      valA = numA;
      valB = numB;
    }

    if (valA < valB) return sortDirection.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortDirection.value === 'asc' ? 1 : -1;
    return 0;
  });
}

// Fetch data from APIs
const fetchData = async () => {
  loading.value = true
  error.value = ''
  try {
    const responses = await Promise.allSettled([
      axios.get('/api/db/pms-inventory-raw'),
      axios.get('/api/db/pms-inventory-processed'),
      axios.get('/api/db/combined-inventory'),
      axios.get('/api/db/inventory-allocation')
    ]);

    if (responses[0].status === 'fulfilled' && responses[0].value.data.status === 'success') {
      pmsRawData.value = responses[0].value.data.data;
      if (pmsRawData.value.length > 0) pmsRawHeaders.value = Object.keys(pmsRawData.value[0]);
    }

    if (responses[1].status === 'fulfilled' && responses[1].value.data.status === 'success') {
      pmsProcessedData.value = responses[1].value.data.data;
      if (pmsProcessedData.value.length > 0) pmsProcessedHeaders.value = Object.keys(pmsProcessedData.value[0]);
    }

    if (responses[2].status === 'fulfilled' && responses[2].value.data.status === 'success') {
      const rawData = responses[2].value.data.data;
      const roomMappings: Record<string, string> = {
        'Occupancy': 'Occ%', 'occupancy': 'Occ%', 'OCCUPANCY': 'Occ%',
        'The Anvaya Villa': 'AVP', 'The Anvaya Suite Whirpool': 'ASW',
        'The Anvaya Suite With Pool': 'ASP', 'The Anvaya Suite No Pool': 'AVS',
        'The Anvaya Residence': 'AVR', 'Beach Front Private Suite Room': 'BFS',
        'Deluxe Room': 'DLX', 'Deluxe Pool Access': 'DLP', 'Deluxe Suite Room': 'DLS',
        'Premiere Room': 'PRE', 'Premiere Room Lagoon Access': 'PKL',
        'Premiere Suite Room': 'PRS', 'Family Premiere Room': 'FPK'
      };

      const processedData = rawData.map((row: Record<string, any>) => {
        const newRow: Record<string, any> = {};
        for (const key in row) {
          const newKey = roomMappings[key] || key;
          newRow[newKey] = row[key];
        }
        if (newRow['DLX'] !== undefined && newRow['PRE'] !== undefined) {
          newRow['DLX+Pre'] = (Number(newRow['DLX']) || 0) + (Number(newRow['PRE']) || 0);
        }
        return newRow;
      });
      
      combinedData.value = processedData;

      if (processedData.length > 0) {
        const columnOrder = [
          'Date', 'Occ%', 'DLX', 'PRE', 'DLX+Pre', 'DLP', 'PKL', 'FPK',
          'DLS', 'PRS', 'AVS', 'ASW', 'BFS', 'ASP', 'AVR', 'AVP'
        ];
        const firstRowKeys = Object.keys(processedData[0]);
        combinedHeaders.value = columnOrder.filter(header => firstRowKeys.includes(header));
      } else {
        combinedHeaders.value = [];
      }
    }

    if (responses[3].status === 'fulfilled' && responses[3].value.data.status === 'success') {
      allocationData.value = responses[3].value.data.data;
      if (allocationData.value.length > 0) allocationHeaders.value = Object.keys(allocationData.value[0]);
    }

  } catch (err: any) {
    console.error('Error fetching data:', err)
    error.value = 'Failed to fetch data. Please make sure the backend server is running.'
  } finally {
    loading.value = false
  }
}

// Export functionality
const exportData = async (type: string, format: 'csv' | 'excel' | 'json') => {
  let data: any[] = getDataForTab(type);
  let filename = type.replace(/-/g, '_');

  if (data.length === 0) {
    alert('No data available to export');
    return;
  }

  try {
    switch (format) {
      case 'csv':
        const csvHeaders = Object.keys(data[0]).join(',');
        const csvContent = data.map(row => Object.values(row).map(value => typeof value === 'string' ? `"${value}"` : value).join(',')).join('\n');
        const csv = `${csvHeaders}\n${csvContent}`;
        const csvBlob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const csvUrl = URL.createObjectURL(csvBlob);
        const csvLink = document.createElement('a');
        csvLink.href = csvUrl;
        csvLink.download = `${filename}.csv`;
        csvLink.click();
        URL.revokeObjectURL(csvUrl);
        break;

      case 'excel':
        const worksheet = XLSX.utils.json_to_sheet(data);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Data');
        XLSX.writeFile(workbook, `${filename}.xlsx`);
        break;

      case 'json':
        const jsonContent = JSON.stringify(data, null, 2);
        const jsonBlob = new Blob([jsonContent], { type: 'application/json' });
        const jsonUrl = URL.createObjectURL(jsonBlob);
        const jsonLink = document.createElement('a');
        jsonLink.href = jsonUrl;
        jsonLink.download = `${filename}.json`;
        jsonLink.click();
        URL.revokeObjectURL(jsonUrl);
        break;
    }
  } catch (error) {
    console.error('Error exporting data:', error);
    alert('Error exporting data. Please try again.');
  }
}

onMounted(() => {
  // fetchData();
});
</script>