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

              <div v-else class="flex-1 overflow-auto border border-gray-200 rounded-lg">
                <table class="min-w-full divide-y divide-gray-200" :class="tab.id === 'allocation' ? 'text-xs' : 'text-sm'">
                  <thead class="bg-gray-50 sticky top-0 z-10">
                    <tr>
                      <th
                        v-for="header in getHeadersForTab(tab.id)"
                        :key="header"
                        scope="col"
                        class="py-3.5 px-4 text-left font-semibold text-gray-900 cursor-pointer hover:bg-gray-100 group"
                        :class="getStickyClass(tab.id, header, true) || getRoomColorClass(tab.id, header, true)"
                        :style="getStickyStyle(tab.id, header)"
                        @click="sortTab(tab.id, header)"
                      >
                        <div class="flex items-center space-x-2">
                          <span>{{ header.replace(/_/g, ' ') }}</span>
                          <span v-if="sortColumn === header">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-200 bg-white">
                    <tr v-for="(row, index) in getDataForTab(tab.id)" :key="index" class="hover:bg-gray-50 transition-colors">
                      <td
                        v-for="header in getHeadersForTab(tab.id)"
                        :key="header"
                        class="whitespace-nowrap px-4 py-3 font-mono"
                        :class="[getCellClass(row[header]), getStickyClass(tab.id, header, false) || getRoomColorClass(tab.id, header, false)]"
                        :style="getStickyStyle(tab.id, header)"
                      >
                        {{ getDisplayValue(tab.id, row, header) }}
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

// Shared full-name -> short-code abbreviations for room types (Combined + Allocation tabs).
// The Allocation table's columns are built from yielder.py's output, which renames
// 'Deluxe Room'/'Premiere Room' down to just 'Deluxe'/'Premiere' - both spellings are
// mapped here so this table works against either source.
const roomTypeAbbreviations: Record<string, string> = {
  'Deluxe Room': 'DLX',
  'Deluxe': 'DLX',
  'Premiere Room': 'PRE',
  'Premiere': 'PRE',
  'Deluxe Pool Access': 'DLP',
  'Premiere Room Lagoon Access': 'PKL',
  'Family Premiere Room': 'FPK',
  'Deluxe Suite Room': 'DLS',
  'Premiere Suite Room': 'PRS',
  'The Anvaya Suite No Pool': 'AVS',
  'The Anvaya Suite Whirpool': 'ASW',
  'Beach Front Private Suite Room': 'BFS',
  'The Anvaya Suite With Pool': 'ASP',
  'The Anvaya Residence': 'AVR',
  'The Anvaya Villa': 'AVP',
}

// Display order for room-type column groups (Allocation tab)
const roomTypeOrder = ['DLX', 'PRE', 'DLP', 'PKL', 'FPK', 'DLS', 'PRS', 'AVS', 'ASW', 'BFS', 'ASP', 'AVR', 'AVP']

// One distinct pastel color per room-type abbreviation, applied to its header + cells
const roomTypeColors: Record<string, { header: string; cell: string }> = {
  DLX: { header: 'bg-blue-100 text-blue-800', cell: 'bg-blue-50' },
  PRE: { header: 'bg-purple-100 text-purple-800', cell: 'bg-purple-50' },
  DLP: { header: 'bg-cyan-100 text-cyan-800', cell: 'bg-cyan-50' },
  PKL: { header: 'bg-teal-100 text-teal-800', cell: 'bg-teal-50' },
  FPK: { header: 'bg-pink-100 text-pink-800', cell: 'bg-pink-50' },
  DLS: { header: 'bg-indigo-100 text-indigo-800', cell: 'bg-indigo-50' },
  PRS: { header: 'bg-violet-100 text-violet-800', cell: 'bg-violet-50' },
  AVS: { header: 'bg-amber-100 text-amber-800', cell: 'bg-amber-50' },
  ASW: { header: 'bg-sky-100 text-sky-800', cell: 'bg-sky-50' },
  BFS: { header: 'bg-emerald-100 text-emerald-800', cell: 'bg-emerald-50' },
  ASP: { header: 'bg-lime-100 text-lime-800', cell: 'bg-lime-50' },
  AVR: { header: 'bg-rose-100 text-rose-800', cell: 'bg-rose-50' },
  AVP: { header: 'bg-orange-100 text-orange-800', cell: 'bg-orange-50' },
}

// On the Allocation tab, Date and Season/Demand are pinned to the left (in this order) so
// they stay visible while scrolling horizontally. Fixed pixel widths are required so the
// second sticky column's offset lines up exactly with the first column's rendered width.
const STICKY_COLUMN_WIDTHS: Record<string, number> = {
  'Date': 170,
  'Season/Demand': 150,
}
const STICKY_COLUMN_ORDER = Object.keys(STICKY_COLUMN_WIDTHS)

const getStickyOffset = (header: string) => {
  const index = STICKY_COLUMN_ORDER.indexOf(header)
  if (index <= 0) return 0
  return STICKY_COLUMN_ORDER.slice(0, index).reduce((sum, h) => sum + STICKY_COLUMN_WIDTHS[h], 0)
}

const getStickyStyle = (tabId: string, header: string) => {
  if (tabId !== 'allocation' || !(header in STICKY_COLUMN_WIDTHS)) return {}
  const width = `${STICKY_COLUMN_WIDTHS[header]}px`
  return { left: `${getStickyOffset(header)}px`, width, minWidth: width, maxWidth: width }
}

const getStickyClass = (tabId: string, header: string, isHeader: boolean) => {
  if (tabId !== 'allocation' || !(header in STICKY_COLUMN_WIDTHS)) return ''
  const bg = isHeader ? 'bg-gray-50' : 'bg-white'
  const z = isHeader ? 'z-20' : 'z-10'
  return `sticky ${z} ${bg} overflow-hidden text-ellipsis`
}

// Allocation tab's Date column shows "08Aug / 98.37%" (day+month, no year, plus occupancy)
const getAllocationDateDisplay = (row: Record<string, any>) => {
  const d = new Date(row['Date'])
  let dateLabel = row['Date']
  if (!isNaN(d.getTime())) {
    const day = d.getDate().toString().padStart(2, '0')
    const month = d.toLocaleString('en-US', { month: 'short' })
    dateLabel = `${day}${month}`
  }
  const occ = row['Occ%']
  return occ === undefined || occ === null ? dateLabel : `${dateLabel} / ${occ}%`
}

// Renders a cell's display value, handling the Allocation tab's virtual merged columns
// (Date+Occupancy, Season+Demand) before falling back to the generic formatValue
const getDisplayValue = (tabId: string, row: Record<string, any>, header: string) => {
  if (tabId === 'allocation') {
    if (header === 'Date') return getAllocationDateDisplay(row)
    if (header === 'Season/Demand') return `${row['Season'] ?? '-'}/${row['Demand'] ?? '-'}`
  }
  return formatValue(row[header], header)
}

// On the Allocation tab, looks up a header's room-type abbreviation (its first word, e.g.
// "DLX" from "DLX Rem") and returns the matching background color class. Scoped to the
// Allocation tab only - other tabs' raw column names (e.g. PMS Raw's "ASP"/"AVR"/"BFS")
// can coincidentally collide with these abbreviations without actually being related.
const getRoomColorClass = (tabId: string, header: string, isHeader: boolean) => {
  if (tabId !== 'allocation') return ''
  const abbrev = header.split(' ')[0]
  const colors = roomTypeColors[abbrev]
  if (!colors) return ''
  return isHeader ? colors.header : colors.cell
}

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
      const rawData = responses[3].value.data.data;

      const baseColumnRenames: Record<string, string> = {
        'Occupancy': 'Occ%',
        'DemandLevel': 'Demand',
      };
      const suffixRenames: [string, string][] = [
        [' Remaining Inventory', ' Rem'],
        [' Online Inventory', ' On'],
        [' BAR Rate', ' BAR'],
      ];

      const renameAllocationColumn = (key: string): string => {
        if (baseColumnRenames[key]) return baseColumnRenames[key];
        for (const [fullSuffix, shortSuffix] of suffixRenames) {
          if (key.endsWith(fullSuffix)) {
            const roomTypeName = key.slice(0, -fullSuffix.length);
            const abbrev = roomTypeAbbreviations[roomTypeName];
            if (abbrev) return `${abbrev}${shortSuffix}`;
          }
        }
        return key;
      };

      const processedData = rawData.map((row: Record<string, any>) => {
        const newRow: Record<string, any> = {};
        for (const key in row) {
          if (key === 'DayOfWeek') continue; // redundant with Date, drop from display
          newRow[renameAllocationColumn(key)] = row[key];
        }
        return newRow;
      });

      allocationData.value = processedData;

      if (processedData.length > 0) {
        // 'Season/Demand' and Date's occupancy suffix are virtual, computed columns (see
        // getDisplayValue) - Season/Demand isn't a literal row key, so it needs its own
        // availability check rather than the plain firstRowKeys.includes(header) below.
        const columnOrder = [
          'Date', 'Season/Demand',
          ...roomTypeOrder.flatMap(code => [`${code} Rem`, `${code} On`, `${code} BAR`])
        ];
        const firstRowKeys = Object.keys(processedData[0]);
        const isColumnAvailable = (header: string) => {
          if (header === 'Season/Demand') return firstRowKeys.includes('Season') && firstRowKeys.includes('Demand');
          return firstRowKeys.includes(header);
        };
        allocationHeaders.value = columnOrder.filter(isColumnAvailable);
      } else {
        allocationHeaders.value = [];
      }
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
  fetchData();
});
</script>