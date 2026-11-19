import http from './http'
import type {
  GenerateResumeRequest,
  GeneratedResumeResponse,
  PageResult,
  Resume,
  ResumeGenerationContextResponse,
  ResumeSnapshot,
  ResumeTemplate,
  StudentApplicationDetail,
  StudentExperience,
  StudentProfile,
  StudentSkill,
} from '@/types/api'

export function listProfiles(params: { current?: number; size?: number } = {}) {
  return http.get<unknown, PageResult<StudentProfile>>('/student/profiles', { params })
}

export function getMyProfile() {
  return http.get<unknown, StudentProfile>('/student/profiles/me')
}

export function updateMyProfile(data: StudentProfile) {
  return http.put<unknown, StudentProfile>('/student/profiles/me', data)
}

export function listResumesByStudent(studentId: number) {
  return http.get<unknown, Resume[]>('/student/resumes/by-student', { params: { studentId } })
}

export function listResumeTemplates() {
  return http.get<unknown, ResumeTemplate[]>('/student/resumes/templates')
}

export function getResumeGenerationContext() {
  return http.get<unknown, ResumeGenerationContextResponse>('/student/resumes/generation-context')
}

export function createResume(data: Resume) {
  return http.post<unknown, Resume>('/student/resumes', data)
}

export function updateResume(id: number, data: Resume) {
  return http.put<unknown, Resume>(`/student/resumes/${id}`, data)
}

export function deleteResume(id: number) {
  return http.delete<unknown, void>(`/student/resumes/${id}`)
}

export function generateResume(data?: GenerateResumeRequest) {
  return http.post<unknown, GeneratedResumeResponse>('/student/resumes/generate', data || null, {
    timeout: 120000,
  })
}

export function getResumeSnapshot(resumeId: number) {
  return http.get<unknown, ResumeSnapshot>(`/student/resumes/${resumeId}/snapshot`)
}

export function listExperiencesByStudent(studentId: number) {
  return http.get<unknown, StudentExperience[]>('/student/experiences/by-student', {
    params: { studentId },
  })
}

export function createExperience(data: StudentExperience) {
  return http.post<unknown, StudentExperience>('/student/experiences', data)
}

export function updateExperience(id: number, data: StudentExperience) {
  return http.put<unknown, StudentExperience>(`/student/experiences/${id}`, data)
}

export function deleteExperience(id: number) {
  return http.delete<unknown, void>(`/student/experiences/${id}`)
}

export function listSkillsByStudent(studentId: number) {
  return http.get<unknown, StudentSkill[]>('/student/skills/by-student', { params: { studentId } })
}

export function createSkill(data: StudentSkill) {
  return http.post<unknown, StudentSkill>('/student/skills', data)
}

export function updateSkill(id: number, data: StudentSkill) {
  return http.put<unknown, StudentSkill>(`/student/skills/${id}`, data)
}

export function deleteSkill(id: number) {
  return http.delete<unknown, void>(`/student/skills/${id}`)
}

export function listStudentApplicationDetails() {
  return http.get<unknown, StudentApplicationDetail[]>('/applications/by-student/detail')
}
