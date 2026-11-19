import http from './http'
import type { CurrentUser, LoginRequest, LoginResponse, RegisterRequest, UserAccount } from '@/types/api'

export function loginApi(data: LoginRequest) {
  return http.post<unknown, LoginResponse>('/auth/login', data)
}

export function registerApi(data: RegisterRequest) {
  return http.post<unknown, UserAccount>('/auth/register', data)
}

export function meApi() {
  return http.get<unknown, CurrentUser>('/auth/me')
}
