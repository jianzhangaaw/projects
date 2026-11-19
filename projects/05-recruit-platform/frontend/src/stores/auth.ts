import { defineStore } from 'pinia'

import { loginApi, registerApi } from '@/api/auth'
import type { LoginRequest, LoginResponse, RegisterRequest, Role } from '@/types/api'

interface AuthState {
  userId?: number
  username: string
  role: Role
  token: string
  unreadCount: number
}

const STORAGE_KEY = 'auth'

function readState(): AuthState {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return { username: '', role: '', token: '', unreadCount: 0 }
  }
  try {
    return { username: '', role: '', token: '', unreadCount: 0, ...JSON.parse(raw) }
  } catch {
    localStorage.removeItem(STORAGE_KEY)
    return { username: '', role: '', token: '', unreadCount: 0 }
  }
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => readState(),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
  },
  actions: {
    persist() {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          userId: this.userId,
          username: this.username,
          role: this.role,
          token: this.token,
        }),
      )
    },
    setSession(session: LoginResponse) {
      this.userId = session.userId
      this.username = session.username
      this.role = session.role
      this.token = session.token
      this.persist()
    },
    async login(payload: LoginRequest) {
      const session = await loginApi(payload)
      this.setSession(session)
      return session
    },
    async register(payload: RegisterRequest) {
      return registerApi(payload)
    },
    logout() {
      this.userId = undefined
      this.username = ''
      this.role = ''
      this.token = ''
      this.unreadCount = 0
      localStorage.removeItem(STORAGE_KEY)
    },
    setUnreadCount(count: number) {
      this.unreadCount = count
    },
  },
})
