import http from './http'
import type { Company, CompanyDraft, PageResult, StudentDetailResponse } from '@/types/api'

export function listCompanies(params: { current?: number; size?: number } = {}) {
  return http.get<unknown, PageResult<Company>>('/company/companies', { params })
}
export function getMyCompany(userId: number) {
  return http.get<unknown, Company | null>('/company/companies/mine', { params: { userId } })
}
export function getMyDraft(userId: number) {
  return http.get<unknown, CompanyDraft | null>('/company/companies/mine/draft', { params: { userId } })
}
export function saveMyCompany(userId: number, data: Company) {
  return http.post<unknown, Company>('/company/companies/mine', data, { params: { userId } })
}
export function submitReview(userId: number) {
  return http.post<unknown, void>('/company/companies/mine/submit-review', null, { params: { userId } })
}
export function updateMyCompanyLogo(userId: number, logoFileId: number) {
  return http.patch<unknown, Company>(`/company/companies/mine/logo?userId=${userId}&logoFileId=${logoFileId}`)
}
export function createCompany(data: Company) {
  return http.post<unknown, Company>('/company/companies', data)
}
export function updateCompany(id: number, data: Company) {
  return http.put<unknown, Company>(`/company/companies/${id}`, data)
}
export function getStudentDetail(studentId: number) {
  return http.get<unknown, StudentDetailResponse>(`/company/student-detail/${studentId}`)
}
