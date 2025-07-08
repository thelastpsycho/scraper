import { defineStore } from 'pinia'

// Define a main store for the application
export const useMainStore = defineStore('main', {
  state: () => ({
    isLoading: false,
    error: null as string | null,
  }),
  actions: {
    setLoading(status: boolean) {
      this.isLoading = status
    },
    setError(error: string | null) {
      this.error = error
    },
    clearError() {
      this.error = null
    }
  }
})

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [] as { role: string; content: string }[],
  }),
  actions: {
    loadFromSession() {
      const saved = sessionStorage.getItem('chatMessages');
      if (saved) {
        this.messages = JSON.parse(saved);
      }
    },
    saveToSession() {
      sessionStorage.setItem('chatMessages', JSON.stringify(this.messages));
    },
    addMessage(msg: { role: string; content: string }) {
      this.messages.push(msg);
      this.saveToSession();
    },
    setMessages(msgs: { role: string; content: string }[]) {
      this.messages = msgs;
      this.saveToSession();
    },
    clearMessages() {
      this.messages = [];
      this.saveToSession();
    }
  }
}); 