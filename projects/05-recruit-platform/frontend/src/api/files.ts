import axios from 'axios'

import http from './http'
import type { FileResource, FileUploadResponse, Result } from '@/types/api'

export type FileBusinessType = 'RESUME' | 'AVATAR' | 'LOGO' | 'CERTIFICATE' | 'TEMPLATE_COVER'

const ALLOWED_BUSINESS_TYPES: FileBusinessType[] = ['RESUME', 'AVATAR', 'LOGO', 'CERTIFICATE', 'TEMPLATE_COVER']

function normalizeFileUrl(url?: string) {
  if (!url) return ''
  if (/^(https?:|blob:|data:)/.test(url)) return url
  return `https://${url.replace(/^\/+/, '')}`
}

export function uploadFile(file: File, businessType: FileBusinessType) {
  if (!ALLOWED_BUSINESS_TYPES.includes(businessType)) {
    return Promise.reject(new Error(`businessType 只能是 ${ALLOWED_BUSINESS_TYPES.join(' / ')}`))
  }
  const formData = new FormData()
  formData.append('file', file)
  formData.append('businessType', businessType)
  return http.post<unknown, FileUploadResponse>('/files/upload', formData).then((response) => ({
    ...response,
    fileUrl: normalizeFileUrl(response.fileUrl),
  }))
}

export function getFileResource(id: number) {
  return http.get<unknown, FileResource>(`/files/${id}`).then((response) => ({
    ...response,
    fileUrl: normalizeFileUrl(response.fileUrl),
  }))
}

export async function previewFile(id: number) {
  try {
    const blob = await http.get<unknown, Blob>(`/files/${id}/preview`, {
      responseType: 'blob',
      timeout: 70000,
    })
    await assertPreviewBlob(blob)
    return blob
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data instanceof Blob) {
      throw new Error(await resolvePreviewErrorMessage(error.response.data))
    }
    throw error instanceof Error ? error : new Error('文件预览失败')
  }
}

async function assertPreviewBlob(blob: Blob) {
  if (blob.type.includes('application/json') || blob.type.includes('text/json')) {
    throw new Error(await resolvePreviewErrorMessage(blob))
  }
}

async function resolvePreviewErrorMessage(blob: Blob) {
  try {
    const text = await blob.text()
    if (!text) return '文件预览失败'
    const body = JSON.parse(text) as Result<unknown>
    return body.message || '文件预览失败'
  } catch {
    return '文件预览失败'
  }
}
