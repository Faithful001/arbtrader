import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { arbitrageApi } from '../api/arbitrage.api'
import { toast } from 'sonner'

export function useOpportunities(params?: {
  skip?: number
  limit?: number
  min_profit?: number
  sort_by?: string
}) {
  return useQuery({
    queryKey: ['opportunities', params],
    queryFn: () => arbitrageApi.getFeed(params),
    refetchInterval: 60_000,
  })
}

export function useOpportunity(id: string) {
  return useQuery({
    queryKey: ['opportunity', id],
    queryFn: () => arbitrageApi.getOpportunity(id),
    enabled: !!id,
  })
}

export function useOpportunityByCard(cardId: string) {
  return useQuery({
    queryKey: ['opportunity-by-card', cardId],
    queryFn: () => arbitrageApi.getOpportunityByCard(cardId),
    enabled: !!cardId,
  })
}

export function useRecalculate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: arbitrageApi.triggerRecalculate,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['opportunities'] })
      toast.success("Cross-market spreads synced successfully!")
    },
  })
}

