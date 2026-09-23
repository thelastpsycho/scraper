import { reactive, ref } from 'vue'
import axios from '../plugins/axios'

export interface PipelineLogEntry { step: string | null; type: 'info' | 'success' | 'error' | 'skipped'; message: string; timestamp: Date }
export interface PipelineStepDef { id: string; label: string }
export interface StepState { id: string; label: string; status: 'pending' | 'running' | 'success' | 'error' | 'skipped'; logs: PipelineLogEntry[] }

export function usePipelineStream(steps: PipelineStepDef[]) {
  const stepStates = reactive<StepState[]>(steps.map(s => ({ id: s.id, label: s.label, status: 'pending', logs: [] })))
  // Flat, chronological feed of every message across all steps - mirrors the
  // single "Process log" panel already used by Allotment.vue, so the pipeline
  // page can show one continuous live stream instead of per-step boxes.
  const logs = ref<PipelineLogEntry[]>([])
  const isRunning = ref(false)
  const overallError = ref<string | null>(null)
  const overallSuccess = ref(false)
  let es: EventSource | null = null

  function start(startUrl: string, payload: any, streamUrl = '/api/pipeline/stream'): Promise<void> {
    return new Promise((resolve, reject) => {
      isRunning.value = true
      overallError.value = null
      overallSuccess.value = false
      logs.value = []
      stepStates.forEach(s => { s.status = 'pending'; s.logs = [] })

      // Open the stream BEFORE the POST so no early log lines are missed —
      // same ordering used by the existing Scraping.vue "Scrape CM" flow.
      es = new EventSource(streamUrl)

      es.onmessage = (event) => {
        const data = JSON.parse(event.data)
        const entry: PipelineLogEntry = { step: data.step, type: data.type, message: data.message, timestamp: new Date() }
        logs.value.push(entry)
        if (data.step === null) {
          isRunning.value = false
          es?.close()
          if (data.type === 'success') { overallSuccess.value = true; resolve() }
          else { overallError.value = data.message; reject(new Error(data.message)) }
          return
        }
        const step = stepStates.find(s => s.id === data.step)
        if (step) {
          step.logs.push(entry)
          if (data.type === 'info' && step.status === 'pending') step.status = 'running'
          if (data.type === 'success') step.status = 'success'
          if (data.type === 'error') step.status = 'error'
          if (data.type === 'skipped') step.status = 'skipped'
        }
      }

      es.onerror = () => {
        overallError.value = 'Connection to server lost'
        isRunning.value = false
        es?.close()
        reject(new Error('Connection lost'))
      }

      axios.post(startUrl, payload).catch(err => {
        overallError.value = err?.response?.data?.message || 'Failed to start pipeline'
        isRunning.value = false
        es?.close()
        reject(err)
      })
    })
  }

  function stop() { es?.close(); isRunning.value = false }

  return { stepStates, logs, isRunning, overallError, overallSuccess, start, stop }
}
