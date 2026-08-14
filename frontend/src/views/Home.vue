<template>
  <div class="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6 lg:px-10">
    <!-- Header (inlined minimal — isolated from the shared neumorphic PageHeader) -->
    <header class="flex flex-col gap-5 border-b border-slate-200 pb-8 sm:flex-row sm:items-end sm:justify-between">
      <div class="min-w-0">
        <p class="text-xs font-medium uppercase tracking-widest text-slate-400">Revenue Console</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-tight text-slate-900">Dashboard</h1>
        <p class="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
          Hotel revenue-management pipeline — scrape inventory, run the yield matrix, push allotments back to the PMS.
        </p>
      </div>
      <router-link
        to="/scraping"
        class="inline-flex flex-shrink-0 items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700 cursor-pointer"
      >
        <BoltIcon class="h-4 w-4" />
        Start scraping
      </router-link>
    </header>

    <!-- Pipeline stages -->
    <section class="mt-12">
      <h2 class="text-xs font-medium uppercase tracking-widest text-slate-400">Pipeline</h2>
      <div class="mt-5 grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <router-link
          v-for="(stage, index) in stages"
          :key="stage.title"
          :to="stage.href"
          class="group flex flex-col bg-white p-6 transition-colors hover:bg-slate-50 cursor-pointer"
        >
          <div class="flex items-center justify-between">
            <component :is="stage.icon" class="h-5 w-5 text-slate-400 transition-colors group-hover:text-slate-900" />
            <span class="text-xs tabular-nums text-slate-300">0{{ index + 1 }}</span>
          </div>
          <h3 class="mt-6 text-sm font-medium text-slate-900">{{ stage.title }}</h3>
          <p class="mt-1.5 flex-1 text-xs leading-relaxed text-slate-500">{{ stage.description }}</p>
          <span class="mt-4 inline-flex items-center gap-1 text-xs font-medium text-slate-400 transition-colors group-hover:text-slate-900">
            Open
            <ArrowRightIcon class="h-3.5 w-3.5" />
          </span>
        </router-link>
      </div>
    </section>

    <!-- How it works + outputs -->
    <div class="mt-12 grid grid-cols-1 gap-8 lg:grid-cols-3">
      <div class="lg:col-span-2">
        <h2 class="text-xs font-medium uppercase tracking-widest text-slate-400">How the pipeline works</h2>
        <p class="mt-2 text-sm text-slate-500">Each stage reads the previous stage's output — run them in order.</p>
        <ol class="mt-6 space-y-5">
          <li v-for="(step, i) in workflow" :key="step" class="flex items-start gap-4">
            <span class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border border-slate-300 text-xs font-medium tabular-nums text-slate-500">
              {{ i + 1 }}
            </span>
            <p class="pt-0.5 text-sm leading-relaxed text-slate-600" v-html="step" />
          </li>
        </ol>
      </div>

      <div>
        <h2 class="text-xs font-medium uppercase tracking-widest text-slate-400">Data outputs</h2>
        <p class="mt-2 text-sm text-slate-500">Inspect every stage's table.</p>
        <div class="mt-6 divide-y divide-slate-200 border-y border-slate-200">
          <router-link
            v-for="output in outputs"
            :key="output.label"
            :to="output.href"
            class="group flex items-center gap-3 py-3.5 transition-colors cursor-pointer"
          >
            <component :is="output.icon" class="h-4 w-4 text-slate-400 transition-colors group-hover:text-slate-900" />
            <span class="text-sm text-slate-600 transition-colors group-hover:text-slate-900">{{ output.label }}</span>
            <ArrowRightIcon class="ml-auto h-3.5 w-3.5 text-slate-300 transition-colors group-hover:text-slate-500" />
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  DocumentTextIcon,
  CircleStackIcon,
  ArrowsRightLeftIcon,
  ChartBarIcon,
  ArchiveBoxIcon,
  ArrowRightIcon,
  BoltIcon,
  TableCellsIcon,
  CalculatorIcon,
} from '@heroicons/vue/24/outline'

const stages = [
  { title: 'Scrape PMS', description: 'Pull room availability out of the hospitality PMS via Selenium.', href: '/scraping', icon: DocumentTextIcon },
  { title: 'Process data', description: 'Clean PMS + Channel Manager inventory into normalized tables.', href: '/data', icon: CircleStackIcon },
  { title: 'Combine', description: 'Merge processed PMS and CM inventory into one dataset.', href: '/data', icon: ArrowsRightLeftIcon },
  { title: 'Yield', description: 'Apply the demand/threshold matrix to allocate inventory & BAR.', href: '/yielder', icon: ChartBarIcon },
  { title: 'Allotment', description: 'Push the calculated allotment changes back into the PMS.', href: '/allotment', icon: ArchiveBoxIcon },
]

const workflow = [
  'Enter PMS credentials and a start date, then run <strong class="font-medium text-slate-900">Scraping</strong> to capture raw inventory.',
  'Upload the Channel Manager Excel and run <strong class="font-medium text-slate-900">Process CM</strong>, then <strong class="font-medium text-slate-900">Combine Inventory</strong>.',
  'Open <strong class="font-medium text-slate-900">Yielder</strong> to run the demand matrix — tune thresholds and room caps if needed.',
  'Review results in <strong class="font-medium text-slate-900">Data</strong>, then push changes from <strong class="font-medium text-slate-900">Allotment</strong>.',
]

const outputs = [
  { label: 'PMS Raw & Processed', href: '/data', icon: TableCellsIcon },
  { label: 'Combined Inventory', href: '/data', icon: ArrowsRightLeftIcon },
  { label: 'Inventory Allocation', href: '/yielder', icon: CalculatorIcon },
]
</script>
