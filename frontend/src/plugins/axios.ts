import axios from 'axios'

let csrfToken: string | null = null
export function setCsrfToken(value: string | null) { csrfToken = value }

const instance = axios.create({
  // Relative baseURL keeps API calls same-origin so they flow through the Vite
  // dev proxy (/api -> backend). This lets the app work over the LAN without
  // pointing remote browsers at their own 127.0.0.1.
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  withCredentials: true
})

export default instance 
instance.interceptors.request.use(config => {
  if (csrfToken && config.method && !['get', 'head', 'options'].includes(config.method.toLowerCase())) {
    config.headers.set('X-CSRF-Token', csrfToken)
  }
  return config
})

instance.interceptors.response.use(undefined, error => {
  if (error.response?.status === 401 && !error.config?.url?.endsWith('/api/auth/login')) {
    setCsrfToken(null)
    window.dispatchEvent(new Event('operator-session-expired'))
  }
  return Promise.reject(error)
})
