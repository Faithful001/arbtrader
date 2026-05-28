import { apiClient } from '@/api/client'

export const marketsApi = {
  getMarkets: async () => {
    const { data } = await apiClient.get('/markets/')
    return data
  },
  getListings: async (limit: number = 50) => {
    const { data } = await apiClient.get('/pricing/listings', { params: { limit } })
    return data
  },
  getExplorerCards: async (search?: string) => {
    const { data } = await apiClient.get('/cards/explorer', { params: { search } })
    return data
  }
}

