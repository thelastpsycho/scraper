import axios from 'axios'

const instance = axios.create({
  baseURL: 'http://127.0.0.1:5666',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  withCredentials: true
})

export default instance 