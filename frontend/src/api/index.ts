import axios from 'axios'
import type { OverviewStats, CallListResponse, CategoryCount, CallResponse, CallIngestRequest, CallFilters } from '../types'

const api = axios.create({
  baseURL: '/api',
})

const getErrorMessage = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }

  return 'Request failed. Please try again.'
}

export const fetchOverview = async (): Promise<OverviewStats> => {
  const { data } = await api.get<OverviewStats>('/analytics/overview')
  return data
}

export const fetchCalls = async (filters: CallFilters = {}): Promise<CallListResponse> => {
  const params: Record<string, string | number> = {}
  if (filters.page) params.page = filters.page
  if (filters.page_size) params.page_size = filters.page_size
  if (filters.date_from) params.date_from = filters.date_from
  if (filters.date_to) params.date_to = filters.date_to
  if (filters.category) params.category = filters.category
  if (filters.sentiment) params.sentiment = filters.sentiment
  const { data } = await api.get<CallListResponse>('/calls', { params })
  return data
}

export const ingestCall = async (payload: CallIngestRequest): Promise<CallResponse> => {
  try {
    const { data } = await api.post<CallResponse>('/calls', payload)
    return data
  } catch (error) {
    throw new Error(getErrorMessage(error))
  }
}

export const fetchTopCategories = async (limit = 10): Promise<CategoryCount[]> => {
  const { data } = await api.get<CategoryCount[]>('/analytics/top-categories', { params: { limit } })
  return data
}

export const fetchCallById = async (id: string): Promise<CallResponse> => {
  const { data } = await api.get<CallResponse>(`/calls/${id}`)
  return data
}
