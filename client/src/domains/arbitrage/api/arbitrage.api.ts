import { apiClient } from '@/api/client'
import type { OpportunityFeedResponse } from '../types'

export const arbitrageApi = {
  getFeed: async (params?: {
    skip?: number
    limit?: number
    min_profit?: number
    sort_by?: string
  }): Promise<OpportunityFeedResponse> => {
    const { data } = await apiClient.get('/arbitrage/feed', { params })
    return data
  },

  getOpportunity: async (id: string) => {
    const { data } = await apiClient.get(`/arbitrage/${id}`)
    return data
  },

  getOpportunityByCard: async (cardId: string) => {
    const { data } = await apiClient.get(`/arbitrage/card/${cardId}`)
    return data
  },

  triggerRecalculate: async () => {
    const { data } = await apiClient.post('/arbitrage/recalculate')
    return data
  },
}
