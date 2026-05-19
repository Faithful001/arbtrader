import { apiClient } from '@/api/client'

export const cardsApi = {
  getCard: async (id: string) => {
    const { data } = await apiClient.get(`/cards/${id}`)
    return data
  },
  getPriceHistory: async (cardId: string, marketId: string, limit: number = 30) => {
    const { data } = await apiClient.get(`/pricing/history/${cardId}/${marketId}`, {
      params: { limit }
    })
    return data
  }
}
