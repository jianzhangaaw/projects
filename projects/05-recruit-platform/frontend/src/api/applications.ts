import http from './http'
import type { CompanyApplicationDetail, JobApplication, PageResult, StudentApplicationDetail } from '@/types/api'

export function listApplications(params: { current?: number; size?: number } = {}) {
  return http.get<unknown, PageResult<JobApplication>>('/applications', { params })
}

export function listApplicationsByStudent(studentId: number) {
  return http.get<unknown, JobApplication[]>('/applications/by-student', { params: { studentId } })
}

export function listStudentApplicationDetails() {
  return http.get<unknown, StudentApplicationDetail[]>('/applications/by-student/detail')
}

export function listApplicationsByCompany(companyId: number) {
  return http.get<unknown, JobApplication[]>('/applications/by-company', { params: { companyId } })
}

export function listCompanyApplicationDetails(companyId: number) {
  return http.get<unknown, CompanyApplicationDetail[]>('/applications/by-company/detail', {
    params: { companyId },
  })
}

export function updateApplicationStatus(id: number, status: string, remark?: string) {
  return http.patch<unknown, void>(`/applications/${id}/status`, null, {
    params: { status, remark },
  })
}

export function createApplication(data: JobApplication) {
  return http.post<unknown, JobApplication>('/applications', data)
}

export function withdrawApplication(id: number) {
  return http.delete<unknown, void>(`/applications/${id}`)
}
