import { useQuery } from '@tanstack/react-query'
import { fetchOverview, fetchCalls, fetchTopCategories } from '../api'

export function useOverview() {
  return useQuery({
    queryKey: ['overview'],
    queryFn: fetchOverview,
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}

export function useCalls(page = 1, page_size = 10) {
  return useQuery({
    queryKey: ['calls', page, page_size],
    queryFn: () => fetchCalls(page, page_size),
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
