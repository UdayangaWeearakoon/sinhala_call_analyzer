import { useQuery } from '@tanstack/react-query'
import { fetchOverview, fetchCalls, fetchTopCategories } from '../api'
import type { CallFilters } from '../types'

export function useOverview() {
  return useQuery({
    queryKey: ['overview'],
    queryFn: fetchOverview,
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}

export function useCalls(filters: CallFilters = {}) {
  return useQuery({
    queryKey: ['calls', filters],
    queryFn: () => fetchCalls(filters),
    staleTime: 30_000,
  })
}

export function useTopCategories(limit = 10) {
  return useQuery({
    queryKey: ['top-categories', limit],
    queryFn: () => fetchTopCategories(limit),
    staleTime: 60_000,
  })
}
