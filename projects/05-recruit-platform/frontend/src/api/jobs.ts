import http from './http'
import type { Job, PageResult } from '@/types/api'

export interface JobQuery {
  current?: number
  size?: number
  keyword?: string
  city?: string
  jobType?: string
}

export function listJobs(params: JobQuery = {}) {
  return http.get<unknown, PageResult<Job>>('/jobs', { params })
}

export function listPublishedJobs(params: JobQuery = {}) {
  return http.get<unknown, PageResult<Job>>('/jobs/published', { params })
}

export function listJobsByCompany(companyId: number) {
  return http.get<unknown, Job[]>('/jobs/by-company', { params: { companyId } })
}

export function createJob(data: Job) {
  return http.post<unknown, Job>('/jobs', data)
}

export function updateJob(id: number, data: Job) {
  return http.put<unknown, Job>(`/jobs/${id}`, data)
}

export function deleteJob(id: number) {
  return http.delete<unknown, void>(`/jobs/${id}`)
}

export function updateJobStatus(id: number, status: string) {
  return http.patch<unknown, void>(`/jobs/${id}/status`, null, { params: { status } })
}
