export interface UserSession {
  sessionId: string
  userId: string
  email: string
  name: string
  image?: string
  provider: 'google' | 'github' | 'email'
  accessToken?: string
  refreshToken?: string
  createdAt: number
  expiresAt: number
}
