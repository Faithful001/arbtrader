import { apiClient } from '@/api/client'

export const marketsApi = {
  getListings: async (limit: number = 50) => {
    const { data } = await apiClient.get('/pricing/listings', { params: { limit } })
    return data
  }
}
