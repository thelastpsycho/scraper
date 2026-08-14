import axios from 'axios'

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