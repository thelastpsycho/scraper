<template>
  <div class="flex h-[calc(100dvh-4rem)] flex-col p-4 sm:p-6 lg:h-screen lg:p-8">
    <div class="mx-auto flex h-full w-full max-w-3xl flex-col overflow-hidden rounded-xl bg-app-primary shadow-neu">
      <!-- Header -->
      <header class="flex flex-shrink-0 items-center gap-3 border-b border-slate-200 px-5 py-4">
        <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-app-primary text-app-accent shadow-neu-sm">
          <ChatBubbleLeftRightIcon class="h-5 w-5" />
        </span>
        <div class="leading-tight">
          <h1 class="font-semibold text-sm text-app-tertiary">Room availability assistant</h1>
          <p class="text-xs text-slate-500">Ask about inventory by room type and date</p>
        </div>
      </header>

      <!-- Chat Messages -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6" ref="chatContainer">
        <div v-for="(msg, idx) in chatStore.messages.filter(m => m.role !== 'system')" :key="idx" class="flex items-start gap-3" :class="{'justify-end': msg.role === 'user'}">
          <!-- Assistant Avatar -->
          <div v-if="msg.role === 'assistant'" class="w-9 h-9 rounded-full bg-app-primary text-app-accent flex items-center justify-center flex-shrink-0 shadow-neu-sm">
            <SparklesIcon class="h-5 w-5" />
          </div>

          <!-- Message Content -->
          <div class="max-w-lg">
            <div class="rounded-xl px-4 py-3 text-sm" :class="msg.role === 'user' ? 'bg-app-accent text-white shadow-neu-sm' : 'bg-app-primary text-slate-700 shadow-neu-sm'">
              <div v-if="msg.role === 'assistant'" class="prose prose-sm max-w-none" v-html="renderMarkdown(msg.content)"></div>
              <p v-else>{{ msg.content }}</p>
            </div>
          </div>

          <!-- User Avatar -->
          <div v-if="msg.role === 'user'" class="w-9 h-9 rounded-full bg-app-primary text-app-accent flex items-center justify-center flex-shrink-0 shadow-neu-sm">
            <UserIcon class="h-5 w-5" />
          </div>
        </div>
        <div v-if="loading" class="flex items-start gap-3">
          <div class="w-9 h-9 rounded-full bg-app-primary text-app-accent flex items-center justify-center flex-shrink-0 shadow-neu-sm">
            <SparklesIcon class="h-5 w-5" />
          </div>
          <div class="max-w-lg">
            <div class="rounded-xl px-4 py-3 bg-app-primary shadow-neu-sm">
              <div class="flex items-center space-x-1">
                <span class="h-1.5 w-1.5 bg-app-accent rounded-full animate-bounce" style="animation-delay: 0s;"></span>
                <span class="h-1.5 w-1.5 bg-app-accent rounded-full animate-bounce" style="animation-delay: 0.1s;"></span>
                <span class="h-1.5 w-1.5 bg-app-accent rounded-full animate-bounce" style="animation-delay: 0.2s;"></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Form -->
      <footer class="flex-shrink-0 border-t border-slate-200 p-4">
        <form @submit.prevent="sendMessage" class="flex items-center gap-3">
          <input
            v-model="input"
            class="w-full flex-1 rounded-full bg-app-primary px-5 py-2.5 text-sm text-app-tertiary shadow-neu-inset-sm transition placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-app-accent/40"
            placeholder="e.g. 'dlx and pre for next 3 days'"
          />
          <button
            type="submit"
            class="flex-shrink-0 rounded-full bg-app-accent p-3 text-white shadow-neu-sm transition-all hover:brightness-110 active:shadow-neu-inset-sm disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
            :disabled="loading || !input"
          >
            <PaperAirplaneIcon class="h-5 w-5" />
          </button>
        </form>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue';
import axios from '../plugins/axios';
import { marked } from 'marked';
import { useChatStore } from '../stores';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  UserIcon,
  SparklesIcon
} from '@heroicons/vue/24/outline'

const chatStore = useChatStore();
const inventory = ref<any[]>([]);
const loading = ref(false);
const input = ref('');
const chatContainer = ref<HTMLElement | null>(null);

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

const systemPrompt = `
You are an assistant that helps users check room availability.
The latest room inventory data will always be provided as JSON.

- Always answer with a clean, well-formatted Markdown table for room availability.
- Use the abbreviations below for room types in the table.
- If a value is negative, just show the number. Do not add any text like (Overbooked).
- Never use code blocks.
- Only answer about the data provided.
- if the answer comes with multiple room types, always put deluxe room first and then premiere room.
- If the user's question is outside the topic of room availability or the provided inventory data, simply answer: "I can only answer questions about room availability based on the data I have. Please ask a question about room types and dates."

Room Type Abbreviations:

| Full Name                        | Abbreviation |
|----------------------------------|--------------|
| Beach Front Private Suite Room   | BFS          |
| Deluxe Pool Access               | DLP          |
| Deluxe Room                      | DLX          |
| Deluxe Suite Room                | DLS          |
| Family Premiere Room             | FPK          |
| Premiere Room                    | PRE          |
| Premiere Room Lagoon Access      | PKL          |
| Premiere Suite Room              | PRS          |
| The Anvaya Residence             | AVR          |
| The Anvaya Suite No Pool         | AVS          |
| The Anvaya Suite Whirpool        | ASW          |
| The Anvaya Suite With Pool       | ASP          |
| The Anvaya Villa                 | AVP          |
| DLX+Pre (DLX + PRE combined)     | DLX+Pre      |

Example output:

Here's the availability for **September 2–5, 2025**:

| Room Type | Sep 2, 2025 | Sep 3, 2025 | Sep 4, 2025 | Sep 5, 2025 |
|-----------|-------------|-------------|-------------|-------------|
| BFS       | 6           | 6           | 7           | 7           |
| DLP       | 4           | 4           | 0           | -1          |
| DLX       | 63          | 56          | 59          | -25         |
| ...       | ...         | ...         | ...         | ...         |
| DLX+Pre   | 296         | 280         | 284         | 94          |

Let me know if you'd like to check other dates or room types!
`;

const defaultMessages: { role: string; content: string }[] = [
  { role: 'system', content: systemPrompt }
];

// Helper to parse AI response for table data
function parseTableFromAIResponse(text: string) {
  const tableRegex = /\|(.+\|)+\n\|([\s\S]+?)\n(?=\n|$)/;
  const match = text.match(tableRegex);
  if (!match) return null;
  const lines = match[0].trim().split('\n');
  if (lines.length < 2) return null;
  const headers = lines[0].split('|').map(h => h.trim()).filter(Boolean);
  const rows = lines.slice(2).map(line =>
    line.split('|').map(cell => cell.trim()).filter(Boolean)
  ).filter(row => row.length === headers.length);
  return { headers, rows };
}

function renderMarkdown(text: string) {
  text = text.replace(/\s*\(Overbooked\)/g, ''); // Remove all (Overbooked)
  const tableData = parseTableFromAIResponse(text);
  if (tableData) {
    const tableRegex = /\|(.+\|)+\n\|([\s\S]+?)\n(?=\n|$)/;
    const match = text.match(tableRegex);
    let before = '', after = '';
    if (match) {
      const idx = text.indexOf(match[0]);
      before = text.slice(0, idx).trim();
      after = text.slice(idx + match[0].length).trim();
    }
    let html = '<table class="ai-chat-table"><thead><tr>';
    tableData.headers.forEach(h => {
      const dateMatch = h.match(/^[A-Za-z]+\s(\d{1,2}),\s\d{4}$/);
      const displayHeader = dateMatch ? dateMatch[1] : h;
      html += `<th>${displayHeader}</th>`;
    });
    html += '</tr></thead><tbody>';
    tableData.rows.forEach(row => {
      html += '<tr>';
      row.forEach(cell => {
        const isNegative = /^-?\d+/.test(cell.trim());
        html += `<td${isNegative ? ' class="negative-value"' : ''}>${cell}</td>`;
      });
      html += '</tr>';
    });
    html += '</tbody></table>';
    return `
      ${before ? `<div style="margin-bottom:0.5em">${marked.parseInline(before)}</div>` : ''}
      <div style="margin: 0.5em 0;">${html}</div>
      ${after ? `<div style="margin-top:0.5em">${marked.parseInline(after)}</div>` : ''}
    `;
  }
  const html = marked.parse(text, { breaks: true }) as string;
  return html;
}

async function fetchInventory() {
  try {
    const res = await axios.get('/api/db/combined-inventory');
    const rawData = Array.isArray(res.data) ? res.data : (res.data?.data || []);
    const roomMappings = {
      'Occupancy': 'Occ%',
      'occupancy': 'Occ%',
      'OCCUPANCY': 'Occ%',
      'The Anvaya Villa': 'AVP',
      'The Anvaya Suite Whirpool': 'ASW',
      'The Anvaya Suite With Pool': 'ASP',
      'The Anvaya Suite No Pool': 'AVS',
      'The Anvaya Residence': 'AVR',
      'Beach Front Private Suite Room': 'BFS',
      'Deluxe Room': 'DLX',
      'Deluxe Pool Access': 'DLP',
      'Deluxe Suite Room': 'DLS',
      'Premiere Room': 'PRE',
      'Premiere Room Lagoon Access': 'PKL',
      'Premiere Suite Room': 'PRS',
      'Family Premiere Room': 'FPK'
    } as Record<string, string>;
    const processed = rawData.map((row: Record<string, any>) => {
      const newRow: Record<string, any> = {};
      const dateKey = Object.keys(row).find(key => key.toLowerCase().includes('date'));
      if (dateKey) newRow['Date'] = row[dateKey];
      Object.keys(row).forEach(key => {
        if (key.toLowerCase().includes('date')) return;
        const newKey = roomMappings[key];
        if (newKey) newRow[newKey] = row[key];
      });
      const dlx = Number(newRow['DLX']) || 0;
      const pre = Number(newRow['PRE']) || 0;
      newRow['DLX+Pre'] = dlx + pre;
      return newRow;
    });
    inventory.value = processed;
  } catch (e) {
    inventory.value = [];
  }
}

onMounted(async () => {
  chatStore.loadFromSession();
  if (!chatStore.messages.length) {
    chatStore.setMessages(defaultMessages);
  } else {
    if (chatStore.messages[0].role === 'system') {
      chatStore.messages[0].content = systemPrompt;
    } else {
      chatStore.messages.unshift({ role: 'system', content: systemPrompt });
    }
    chatStore.saveToSession();
  }
  await fetchInventory();
  scrollToBottom();
});

watch(() => chatStore.messages, () => {
  scrollToBottom();
});

async function sendMessage() {
  if (!input.value.trim()) return;
  chatStore.addMessage({ role: 'user', content: input.value });
  input.value = '';
  loading.value = true;
  const contextMessages = [
    { role: 'system', content: systemPrompt },
    { role: 'system', content: 'Here is the latest room inventory data as JSON: ' + JSON.stringify(inventory.value) },
    ...chatStore.messages.filter(m => m.role !== 'system')
  ];
  try {
    const response = await axios.post(
      'https://api.deepseek.com/v1/chat/completions',
      {
        model: 'deepseek-chat',
        messages: contextMessages.map(m => ({ role: m.role, content: m.content }))
      },
      {
        headers: {
          'Authorization': 'Bearer sk-8c0b9404dabb4da3a5fd92365f5c1f37',
          'Content-Type': 'application/json'
        }
      }
    );
    const aiMessage = response.data.choices?.[0]?.message?.content || 'No response from AI.';
    chatStore.addMessage({ role: 'assistant', content: aiMessage });
  } catch (err) {
    chatStore.addMessage({ role: 'assistant', content: 'Error contacting DeepSeek API.' });
  } finally {
    loading.value = false;
  }
}
</script>

<style>
.prose {
  color: #475569; /* slate-600 */
}
.prose a {
  color: #0f172a; /* slate-900 */
  text-decoration: underline;
  text-underline-offset: 2px;
}
.prose strong {
  color: #0f172a; /* slate-900 */
}

.ai-chat-table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.8125rem;
  color: #475569; /* slate-600 */
}
.ai-chat-table th, .ai-chat-table td {
  padding: 0.6rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid rgba(163, 177, 198, 0.4);
}
.ai-chat-table th {
  font-weight: 700;
  color: #0f172a; /* slate-900 */
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.6875rem;
}
.ai-chat-table tr:last-child td {
  border-bottom: none;
}
.ai-chat-table td.negative-value {
  color: #e11d48; /* rose-600 */
  font-weight: 700;
}
</style>