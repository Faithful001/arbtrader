import { apiClient } from '@/api/client'

export const portfolioApi = {
  getHoldings: async () => {
    const { data } = await apiClient.get('/portfolio/')
    return data
  },
  getPnl: async () => {
    const { data } = await apiClient.get('/portfolio/pnl')
    return data
  },
  addHolding: async (payload: any) => {
    const { data } = await apiClient.post('/portfolio/', payload)
    return data
  },
  removeHolding: async (id: string) => {
    const { data } = await apiClient.delete(`/portfolio/${id}`)
    return data
  }
}
