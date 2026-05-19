import { apiClient } from '@/api/client'

export const alertsApi = {
  getAlerts: async () => {
    const { data } = await apiClient.get('/alerts/')
    return data
  },
  createAlert: async (payload: any) => {
    const { data } = await apiClient.post('/alerts/', payload)
    return data
  },
  updateAlert: async (id: string, payload: any) => {
    const { data } = await apiClient.patch(`/alerts/${id}`, payload)
    return data
  },
  deleteAlert: async (id: string) => {
    const { data } = await apiClient.delete(`/alerts/${id}`)
    return data
  }
}
