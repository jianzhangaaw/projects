import http from './http'
import type { Company, Job, PageResult, ResumeTemplate, UserAccount } from '@/types/api'

export interface UserListParams {
  current?: number
  size?: number
  username?: string
  role?: string
  status?: string
}

export function listUsers(params: UserListParams = {}) {
  return http.get<unknown, PageResult<UserAccount>>('/admin/users', { params })
}

export function updateUserStatus(id: number, status: string) {
  // 后端同时支持 PATCH 和 PUT
  return http.patch<unknown, void>(`/admin/users/${id}/status`, null, { params: { status } })
}

export function listPendingCompanies() {
  return http.get<unknown, Company[]>('/admin/reviews/companies')
}

export function approveCompany(id: number) {
  return http.patch<unknown, void>(`/admin/reviews/companies/${id}/approve`)
}

export function rejectCompany(id: number, reviewReason: string) {
  return http.patch<unknown, void>(
    `/admin/reviews/companies/${id}/reject`,
    null,
    { params: { reviewReason } },
  )
}

export function listPendingJobs() {
  return http.get<unknown, Job[]>('/admin/reviews/jobs')
}

export function approveJob(id: number) {
  return http.patch<unknown, void>(`/admin/reviews/jobs/${id}/approve`)
}

export function rejectJob(id: number, reviewReason: string) {
  return http.patch<unknown, void>(
    `/admin/reviews/jobs/${id}/reject`,
    null,
    { params: { reviewReason } },
  )
}

export function listResumeTemplatesForAdmin() {
  return http.get<unknown, ResumeTemplate[]>('/admin/resume-templates')
}

export function createResumeTemplate(data: ResumeTemplate) {
  return http.post<unknown, ResumeTemplate>('/admin/resume-templates', data)
}

export function updateResumeTemplate(id: number, data: ResumeTemplate) {
  return http.put<unknown, ResumeTemplate>(`/admin/resume-templates/${id}`, data)
}

export function updateResumeTemplateEnabled(id: number, enabled: boolean) {
  return http.patch<unknown, void>(`/admin/resume-templates/${id}/enabled`, null, {
    params: { enabled },
  })
}

export function updateResumeTemplateSort(id: number, sortOrder: number) {
  return http.patch<unknown, void>(`/admin/resume-templates/${id}/sort`, null, {
    params: { sortOrder },
  })
}
