import axios from 'axios'

const instance = axios.create({
  // baseURL: '', // Removed to use relative URLs for Vite proxy
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  withCredentials: true
})

export default instance 