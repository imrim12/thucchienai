import type { H3Event } from 'h3'
import type { User } from '@/db/schemas'
import type { UserSession } from '@/types/auth'
import { randomUUID } from 'node:crypto'
import { and, eq } from 'drizzle-orm'
import { AUTH_COOKIE_NAME } from '@/constants/auth'
import { decryptIfExists, encryptIfExists } from '@/utils/encryption'

export function useAuth() {
  const SESSION_EXPIRY = 60 * 60 * 24 * 7 * 1000 // 7 days in milliseconds

  async function getSession(event: H3Event): Promise<UserSession | null> {
    try {
      const sessionId = await getSessionId(event)

      if (!sessionId) {
        return null
      }

      const redis = useStorage('redis')
      const sessionData = await redis.getItem<UserSession>(`session:${sessionId}`)

      if (!sessionData) {
        return null
      }

      // Check if session has expired
      if (Date.now() > sessionData.expiresAt) {
        await redis.removeItem(`session:${sessionId}`)
        return null
      }

      return sessionData
    }
    catch (error) {
      console.error('Session error:', error)
      return null
    }
  }

  async function createSession(event: H3Event, user: User, provider: 'google' | 'github' | 'email', tokens?: { accessToken?: string, refreshToken?: string }): Promise<string> {
    try {
      const sessionId = randomUUID()
      const now = Date.now()
      const expiresAt = now + SESSION_EXPIRY

      const sessionData: UserSession = {
        sessionId,
        userId: user.id,
        email: user.email,
        name: user.name || '',
        image: user.image || undefined,
        provider,
        accessToken: tokens?.accessToken,
        refreshToken: tokens?.refreshToken,
        createdAt: now,
        expiresAt,
      }

      const redis = useStorage('redis')
      await redis.setItem(`session:${sessionId}`, sessionData, {
        ttl: SESSION_EXPIRY / 1000, // TTL in seconds
      })

      // Set session cookie
      setCookie(event, AUTH_COOKIE_NAME, sessionId, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
        maxAge: SESSION_EXPIRY / 1000, // maxAge in seconds
      })

      return sessionId
    }
    catch (error) {
      console.error('Session creation error:', error)
      throw error
    }
  }

  async function clearSession(event: H3Event): Promise<void> {
    try {
      const sessionId = await getSessionId(event)
      if (sessionId) {
        const redis = useStorage('redis')
        await redis.removeItem(`session:${sessionId}`)
      }

      // Clear session cookie
      deleteCookie(event, AUTH_COOKIE_NAME, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
      })
    }
    catch (error) {
      console.error('Session clear error:', error)
      throw error
    }
  }

  async function findOrCreateUser(
    email: string,
    name: string,
    image: string | null,
    provider: 'google' | 'github' | 'email',
    providerUserId: string,
    oauthData?: {
      accessToken?: string
      refreshToken?: string
      expiresAt?: Date
      scopes?: string[]
    },
  ): Promise<User> {
    const db = useDb()
    const { userSchema, identitySchema } = useDbSchema()

    try {
      // First try to find existing user by provider identity
      const existingIdentity = await db.query.identitySchema.findFirst({
        where: and(
          eq(identitySchema.providerName, provider),
          eq(identitySchema.providerUserId, providerUserId),
        ),
        with: {
          user: true,
        },
      })

      if (existingIdentity) {
        // Update user info if needed
        const user = existingIdentity.user
        if (user.name !== name || user.image !== image) {
          const [updatedUser] = await db
            .update(userSchema)
            .set({
              name,
              image,
              updatedAt: new Date(),
            })
            .where(eq(userSchema.id, user.id))
            .returning()

          // Update OAuth data in identity table
          if (oauthData) {
            await updateOAuthTokens(user.id, provider, providerUserId, oauthData)
          }

          return updatedUser
        }

        // Update OAuth data even if user info hasn't changed
        if (oauthData) {
          await updateOAuthTokens(user.id, provider, providerUserId, oauthData)
        }

        return user
      }

      // Try to find user by email
      const existingUserByEmail = await db.query.userSchema.findFirst({
        where: eq(userSchema.email, email),
      })

      let user: User

      if (existingUserByEmail) {
        // User exists with this email, create new identity for this provider
        user = existingUserByEmail

        // Update user info if needed
        if (user.name !== name || user.image !== image) {
          const [updatedUser] = await db
            .update(userSchema)
            .set({
              name,
              image,
              updatedAt: new Date(),
            })
            .where(eq(userSchema.id, user.id))
            .returning()

          user = updatedUser
        }
      }
      else {
        // Create new user
        const [newUser] = await db
          .insert(userSchema)
          .values({
            id: randomUUID(),
            email,
            name,
            image,
          })
          .returning()

        user = newUser
      }

      // Create identity for this provider with OAuth data
      await db
        .insert(identitySchema)
        .values({
          userId: user.id,
          providerName: provider,
          providerUserId,
          accessToken: encryptIfExists(oauthData?.accessToken),
          refreshToken: encryptIfExists(oauthData?.refreshToken),
          tokenExpiresAt: oauthData?.expiresAt,
          scopes: oauthData?.scopes?.join(','),
        })
        .onConflictDoNothing()

      return user
    }
    catch (error) {
      console.error('Error finding or creating user:', error)
      throw error
    }
  }

  async function updateOAuthTokens(
    userId: string,
    provider: 'google' | 'github' | 'email',
    providerUserId: string,
    oauthData: {
      accessToken?: string
      refreshToken?: string
      expiresAt?: Date
      scopes?: string[]
    },
  ): Promise<void> {
    const db = useDb()
    const { identitySchema } = useDbSchema()

    try {
      await db
        .update(identitySchema)
        .set({
          accessToken: encryptIfExists(oauthData.accessToken),
          refreshToken: encryptIfExists(oauthData.refreshToken),
          tokenExpiresAt: oauthData.expiresAt,
          scopes: oauthData.scopes?.join(','),
          updatedAt: new Date(),
        })
        .where(and(
          eq(identitySchema.userId, userId),
          eq(identitySchema.providerName, provider),
          eq(identitySchema.providerUserId, providerUserId),
        ))
    }
    catch (error) {
      console.error('Error updating OAuth tokens:', error)
      throw error
    }
  }

  async function getOAuthTokens(
    userId: string,
    provider: 'google' | 'github' | 'email',
  ): Promise<{
    accessToken: string | null
    refreshToken: string | null
    expiresAt: Date | null
    scopes: string[]
  } | null> {
    const db = useDb()
    const { identitySchema } = useDbSchema()

    try {
      const identity = await db.query.identitySchema.findFirst({
        where: and(
          eq(identitySchema.userId, userId),
          eq(identitySchema.providerName, provider),
        ),
        columns: {
          accessToken: true,
          refreshToken: true,
          tokenExpiresAt: true,
          scopes: true,
        },
      })

      if (!identity) {
        return null
      }

      return {
        accessToken: decryptIfExists(identity.accessToken),
        refreshToken: decryptIfExists(identity.refreshToken),
        expiresAt: identity.tokenExpiresAt,
        scopes: identity.scopes ? identity.scopes.split(',') : [],
      }
    }
    catch (error) {
      console.error('Error retrieving OAuth tokens:', error)
      return null
    }
  }

  async function refreshGoogleToken(userId: string, providerUserId: string): Promise<string | null> {
    try {
      // Get current refresh token
      const tokens = await getOAuthTokens(userId, 'google')

      if (!tokens?.refreshToken) {
        console.error('No refresh token available for user:', userId)
        return null
      }

      const runtimeConfig = useRuntimeConfig()
      const { OAuth2Client } = await import('google-auth-library')

      const oauth2Client = new OAuth2Client(
        runtimeConfig.googleClientId,
        runtimeConfig.googleClientSecret,
      )

      oauth2Client.setCredentials({
        refresh_token: tokens.refreshToken,
      })

      const { credentials } = await oauth2Client.refreshAccessToken()

      if (!credentials.access_token) {
        throw new Error('Failed to refresh access token')
      }

      // Update tokens in database
      await updateOAuthTokens(userId, 'google', providerUserId, {
        accessToken: credentials.access_token,
        refreshToken: credentials.refresh_token || tokens.refreshToken, // Keep old refresh token if new one not provided
        expiresAt: credentials.expiry_date ? new Date(credentials.expiry_date) : undefined,
        scopes: credentials.scope ? credentials.scope.split(' ') : tokens.scopes,
      })

      return credentials.access_token
    }
    catch (error) {
      console.error('Error refreshing Google token:', error)
      return null
    }
  }

  return {
    getSession,
    createSession,
    clearSession,
    findOrCreateUser,
    updateOAuthTokens,
    getOAuthTokens,
    refreshGoogleToken,
  }
}
