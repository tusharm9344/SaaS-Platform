import api from './api'

export async function getContainers() {
  const response = await api.get('/containers/')
  return response.data
}