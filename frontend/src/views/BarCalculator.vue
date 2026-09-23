<template>
  <div class="mx-auto w-full max-w-3xl space-y-3 p-3 sm:p-4">
    <PageHeader
      title="BAR Calculator"
      subtitle="Pick a BAR level and a discount %, and see the resulting rate for every room type."
    />

    <div v-if="loadError" class="neu-card p-4 text-sm text-rose-700">
      {{ loadError }}
    </div>

    <template v-else>
      <!-- Controls -->
      <div class="neu-card space-y-2 p-3">
        <div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <div>
            <label class="mb-1 block text-[11px] font-semibold text-slate-500">BAR level</label>
            <select v-model="selectedLevel" class="neu-input py-1.5 text-sm">
              <option v-for="level in levels" :key="level" :value="level">{{ level }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-[11px] font-semibold text-slate-500">Discount (%)</label>
            <input ref="discountInputEl" type="number" step="0.5" v-model.number="discountPct" placeholder="32" class="neu-input py-1.5 text-sm" />
          </div>
          <div>
            <label class="mb-1 block text-[11px] font-semibold text-slate-500">Additional (%)</label>
            <input type="number" step="0.5" v-model.number="discount2Pct" placeholder="10" class="neu-input py-1.5 text-sm" />
          </div>
          <div>
            <label class="mb-1 block text-[11px] font-semibold text-slate-500">Combine mode</label>
            <div class="flex gap-1 rounded-lg bg-app-secondary p-1">
              <button
                @click="combineMode = 'accumulative'"
                :class="[
                  combineMode === 'accumulative'
                    ? 'bg-app-primary text-app-accent shadow-neu-sm'
                    : 'text-slate-500 hover:text-app-tertiary',
                  'flex-1 rounded-md px-1.5 py-1 text-[11px] font-semibold transition-all duration-200 cursor-pointer',
                ]"
              >
                Accum.
              </button>
              <button
                @click="combineMode = 'stack'"
                :class="[
                  combineMode === 'stack'
                    ? 'bg-app-primary text-app-accent shadow-neu-sm'
                    : 'text-slate-500 hover:text-app-tertiary',
                  'flex-1 rounded-md px-1.5 py-1 text-[11px] font-semibold transition-all duration-200 cursor-pointer',
                ]"
              >
                Stack
              </button>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-1.5">
          <span class="text-[11px] font-semibold text-slate-500">Presets:</span>
          <button
            v-for="preset in DISCOUNT_PRESETS"
            :key="preset.label"
            @click="discountPct = preset.value"
            :class="chipClass(discountPct === preset.value)"
          >
            {{ preset.label }}
          </button>
          <button @click="discountInputEl?.focus()" :class="chipClass(!isPresetValue(discountPct))">
            Custom
          </button>
        </div>

        <div v-if="discount2Pct" class="rounded-md bg-app-secondary px-2.5 py-1.5 text-[11px] text-slate-600">
          Total discount: <span class="font-semibold text-slate-800">{{ formatPercent(totalDiscountPct) }}</span>
          <span class="text-slate-400">
            ({{ combineMode === 'accumulative'
              ? `${discountPct}% then ${discount2Pct}% compounded`
              : `${discountPct}% + ${discount2Pct}% added directly` }})
          </span>
        </div>
      </div>

      <!-- Result table -->
      <div class="neu-card p-3" v-if="roomTypes.length">
        <div class="overflow-auto rounded-lg bg-app-primary shadow-neu-inset">
          <table class="min-w-full divide-y divide-slate-200 text-xs">
            <thead class="bg-app-primary">
              <tr>
                <th class="px-3 py-2 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">Room type</th>
                <th class="px-3 py-2 text-right text-[10px] font-bold uppercase tracking-wider text-slate-500">{{ selectedLevel || 'Rate' }}</th>
                <th class="px-3 py-2 text-right text-[10px] font-bold uppercase tracking-wider text-slate-500">Disc. ({{ formatPercent(totalDiscountPct) }})</th>
                <th class="px-3 py-2 text-right text-[10px] font-bold uppercase tracking-wider text-slate-500">Final rate</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="room in roomTypes" :key="room" class="hover:bg-app-secondary/50">
                <td class="whitespace-nowrap px-3 py-1.5 font-medium text-slate-700">{{ room }}</td>
                <td class="px-3 py-1.5 text-right font-mono text-slate-600">{{ formatCurrency(baseRate(room)) }}</td>
                <td class="px-3 py-1.5 text-right font-mono text-rose-600">-{{ formatCurrency(discountAmount(room)) }}</td>
                <td class="px-3 py-1.5 text-right font-mono font-semibold text-slate-800">{{ formatCurrency(finalRate(room)) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else class="neu-card flex flex-col items-center justify-center gap-2 p-6 text-center text-slate-500">
        <CircleStackIcon class="h-8 w-8 text-slate-300" />
        <p class="text-sm font-semibold text-slate-600">Loading BAR rates…</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import axios from '../plugins/axios'
import PageHeader from '../components/PageHeader.vue'
import { CircleStackIcon } from '@heroicons/vue/24/outline'

interface BarRateRow {
  room_type: string
  level: string
  discount_pct: number | null
  rate: number
}

const LEVEL_ORDER = ['Publish', ...Array.from({ length: 10 }, (_, i) => `BAR${i + 1}`), 'MyValue']

// Generic Promotion discounts from the "6. Rate Simulation" sheet - quick presets
// so common promos don't need to be typed/remembered each time.
const DISCOUNT_PRESETS = [
  { label: 'Staycation', value: 32 },
  { label: 'Flex Staycation', value: 27 },
  { label: 'EBO 60', value: 35 },
]

const loadError = ref('')
const roomTypes = ref<string[]>([])
const levels = ref<string[]>([])
const rates = reactive<Record<string, Record<string, number>>>({})

const selectedLevel = ref('')
const discountPct = ref(0)
const discount2Pct = ref(0)
const combineMode = ref<'accumulative' | 'stack'>('accumulative')
const discountInputEl = ref<HTMLInputElement | null>(null)

function isPresetValue(value: number): boolean {
  return DISCOUNT_PRESETS.some(preset => preset.value === value)
}
function chipClass(active: boolean) {
  return [
    active
      ? 'border-slate-900 bg-slate-900 text-white'
      : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:text-slate-900',
    'rounded-full border px-1.5 py-0.5 text-[10px] font-semibold transition-colors cursor-pointer',
  ]
}

async function fetchBarRates() {
  loadError.value = ''
  try {
    const res = await axios.get('/api/db/bar-rates')
    if (res.data.status !== 'success') {
      loadError.value = res.data.message || 'Failed to load BAR rates.'
      return
    }
    const rows: BarRateRow[] = res.data.data

    Object.keys(rates).forEach(key => delete rates[key])
    const roomOrder: string[] = []
    const levelSet = new Set<string>()

    for (const row of rows) {
      if (!roomOrder.includes(row.room_type)) roomOrder.push(row.room_type)
      levelSet.add(row.level)
      if (!rates[row.room_type]) rates[row.room_type] = {}
      rates[row.room_type][row.level] = row.rate
    }

    roomTypes.value = roomOrder
    levels.value = LEVEL_ORDER.filter(l => levelSet.has(l))
    if (!selectedLevel.value) {
      selectedLevel.value = levels.value.find(l => /^BAR\d+$/.test(l)) || levels.value[0] || ''
    }
  } catch (err: any) {
    console.error('Error fetching BAR rates:', err)
    loadError.value = err?.response?.data?.message || 'Failed to load BAR rates. Please make sure the backend server is running.'
  }
}

function baseRate(room: string): number {
  return rates[room]?.[selectedLevel.value] ?? 0
}

// Two discounts combine either by compounding (each applies to what's left after
// the previous one, e.g. 32% then 10% -> 1-(0.68*0.9) = 38.8%) or by stacking
// (added directly, e.g. 32% + 10% = 42%).
const totalDiscountFraction = computed(() => {
  const d1 = (discountPct.value || 0) / 100
  const d2 = (discount2Pct.value || 0) / 100
  return combineMode.value === 'stack' ? d1 + d2 : 1 - (1 - d1) * (1 - d2)
})
const totalDiscountPct = computed(() => totalDiscountFraction.value * 100)

function discountAmount(room: string): number {
  return baseRate(room) * totalDiscountFraction.value
}
function finalRate(room: string): number {
  return baseRate(room) - discountAmount(room)
}
function formatCurrency(value: number): string {
  if (!isFinite(value)) return '-'
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value)
}
function formatPercent(value: number): string {
  if (!isFinite(value)) return '-'
  return `${value.toFixed(1)}%`
}

fetchBarRates()
</script>
