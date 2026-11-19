export type Role = 'STUDENT' | 'COMPANY' | 'ADMIN' | string

export interface Result<T> {
  code: number
  message: string
  data: T
}

export interface PageResult<T> {
  records: T[]
  total: number
  size: number
  current: number
  pages: number
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  role: Role
  email?: string
  phone?: string
}

export interface LoginResponse {
  userId: number
  username: string
  role: Role
  token: string
}

export interface CurrentUser {
  userId: number
  username: string
  role: Role
}

export interface UserAccount {
  id?: number
  username?: string
  email?: string
  phone?: string
  role?: Role
  status?: string
  createdAt?: string
  updatedAt?: string
  associatedName?: string
}

export interface Company {
  id?: number
  userId?: number
  companyName?: string
  industry?: string
  companySize?: string
  contactName?: string
  contactPhone?: string
  description?: string
  logoFileId?: number
  reviewStatus?: string
  reviewReason?: string
  reviewType?: string
  oldCompanyName?: string
  oldIndustry?: string
  oldCompanySize?: string
  oldContactName?: string
  oldContactPhone?: string
  oldDescription?: string
  createdAt?: string
  updatedAt?: string
}
export interface CompanyDraft {
  id?: number
  companyId?: number
  companyName?: string
  industry?: string
  companySize?: string
  contactName?: string
  contactPhone?: string
  description?: string
  logoFileId?: number
  reviewStatus?: string
  reviewReason?: string
  createdAt?: string
  updatedAt?: string
}

export interface Job {
  id?: number
  companyId?: number
  jobName?: string
  jobType?: string
  city?: string
  salaryRange?: string
  educationRequirement?: string
  majorRequirement?: string
  skillRequirement?: string
  description?: string
  status?: string
  reviewReason?: string
  viewCount?: number
  companyName?: string
  logoFileId?: number
  industry?: string
  companySize?: string
  createdAt?: string
  updatedAt?: string
}

export interface Resume {
  id?: number
  studentId?: number
  resumeName?: string
  resumeType?: string
  targetPosition?: string
  fileId?: number
  fileUrl?: string
  school?: string
  major?: string
  educationLevel?: string
  graduationDate?: string
  skillTags?: string
  createdAt?: string
  updatedAt?: string
}

export interface ResumeTemplate {
  id?: number
  templateName?: string
  templateCode?: string
  coverFileId?: number
  coverUrl?: string
  description?: string
  enabled?: number
  sortOrder?: number
  version?: number
  createdAt?: string
  updatedAt?: string
}

export interface ResumeSnapshot {
  id?: number
  resumeId?: number
  studentId?: number
  templateId?: number
  snapshotJson?: string
  htmlContent?: string
  generatedAt?: string
}

export interface ResumeGenerationSnapshot {
  resumeName?: string
  targetPosition?: string
  profile: StudentProfile
  skills: StudentSkill[]
  experiences: StudentExperience[]
}

export interface GenerateResumeRequest {
  templateId?: number
  snapshot: ResumeGenerationSnapshot
}

export interface ResumeGenerationContextResponse {
  templates: ResumeTemplate[]
  defaultTemplateId?: number
  snapshot: ResumeGenerationSnapshot
}

export interface GeneratedResumeResponse {
  resume: Resume
  pdfFileId: number
  pdfFileUrl: string
  snapshotId: number
  templateId: number
}

export interface StudentProfile {
  id?: number
  userId?: number
  realName?: string
  gender?: string
  age?: number
  hometown?: string
  politicalStatus?: string
  phone?: string
  email?: string
  wechat?: string
  qq?: string
  school?: string
  major?: string
  educationLevel?: string
  gpa?: string
  graduationDate?: string
  expectedPosition?: string
  expectedCity?: string
  expectedSalary?: string
  selfIntro?: string
  avatarFileId?: number
  createdAt?: string
  updatedAt?: string
}

export interface StudentExperience {
  id?: number
  studentId?: number
  experienceType?: string
  title?: string
  timeRange?: string
  roleName?: string
  description?: string
  sortOrder?: number
  fileId?: number
  fileUrl?: string
  createdAt?: string
  updatedAt?: string
}

export interface StudentSkill {
  id?: number
  studentId?: number
  skillName?: string
  skillType?: string
  proficiency?: string
  years?: number
  fileId?: number
  fileUrl?: string
  createdAt?: string
  updatedAt?: string
}

export interface JobApplication {
  id?: number
  jobId?: number
  studentId?: number
  companyId?: number
  resumeId?: number
  status?: string
  remark?: string
  createdAt?: string
  updatedAt?: string
}

export interface CompanyApplicationDetail extends JobApplication {
  jobName?: string
  jobType?: string
  city?: string
  salaryRange?: string
  studentName?: string
  school?: string
  major?: string
  educationLevel?: string
  resumeName?: string
  resumeType?: string
  targetPosition?: string
  resumeFileId?: number
  phone?: string
  email?: string
  gender?: string
}

export interface StudentApplicationDetail extends JobApplication {
  jobName?: string
  jobType?: string
  city?: string
  salaryRange?: string
  companyName?: string
  resumeName?: string
  resumeType?: string
  targetPosition?: string
  resumeFileId?: number
}

export interface StudentDetailResponse {
  profile?: StudentProfile
  skills?: StudentSkill[]
  experiences?: StudentExperience[]
}

export interface Notification {
  id?: number
  receiverId?: number
  title?: string
  content?: string
  type?: string
  isRead?: number
  createdAt?: string
}

export interface FileResource {
  id?: number
  uploaderId?: number
  fileName?: string
  fileType?: string
  fileUrl?: string
  fileSize?: number
  businessType?: string
  createdAt?: string
}

export interface FileUploadResponse {
  id: number
  fileName: string
  fileUrl: string
}
