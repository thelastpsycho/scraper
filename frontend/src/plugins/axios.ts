import axios from 'axios'

const instance = axios.create({
  baseURL: 'http://10.201.59.16:5000',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  withCredentials: true
})

export default instance 