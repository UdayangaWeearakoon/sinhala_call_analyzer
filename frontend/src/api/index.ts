import axios from 'axios'
import type { OverviewStats, CallListResponse, CategoryCount, CallResponse, CallIngestRequest } from '../types'

const api = axios.create({
  baseURL: '/api',
})

export const fetchOverview = async (): Promise<OverviewStats> => {
  const { data } = await api.get<OverviewStats>('/analytics/overview')
  return data
}

export const fetchCalls = async (page = 1, page_size = 10): Promise<CallListResponse> => {
  const { data } = await api.get<CallListResponse>('/calls', { params: { page, page_size } })
  return data
}

export const ingestCall = async (payload: CallIngestRequest): Promise<CallResponse> => {
  const { data } = await api.post<CallResponse>('/calls', payload)
  return data
}

export const fetchTopCategories = async (limit = 10): Promise<CategoryCount[]> => {
  const { data } = await api.get<CategoryCount[]>('/analytics/top-categories', { params: { limit } })
  return data
}
