import type { H3Event } from 'h3'
import type { Promisable } from 'type-fest'
import type { UserSession } from '@/types/auth'
import { Buffer } from 'node:buffer'
import { randomBytes, scrypt, timingSafeEqual } from 'node:crypto'
import { AUTH_COOKIE_NAME } from '@/constants/auth'

export async function getSessionId(event: H3Event): Promise<string | null> {
  return getCookie(event, AUTH_COOKIE_NAME) || null
}

export function defineAuthenticatedEventHandler<T>(handler: (event: H3Event, session: UserSession) => Promisable<T>) {
  return defineEventHandler(async (event) => {
    const { getSession } = useAuth()
    const session = await getSession(event)

    if (!session) {
      throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
    }

    return handler(event, session)
  })
}

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16)
  const keyLength = 64

  return new Promise((resolve, reject) => {
    scrypt(password, salt, keyLength, (err, derivedKey) => {
      if (err)
        reject(err)
      else resolve(`${salt.toString('hex')}:${derivedKey.toString('hex')}`)
    })
  })
}

export async function verifyPassword(password: string, hashedPassword: string): Promise<boolean> {
  const [saltHex, keyHex] = hashedPassword.split(':')
  const salt = Buffer.from(saltHex, 'hex')
  const key = Buffer.from(keyHex, 'hex')
  const keyLength = key.length

  return new Promise((resolve, reject) => {
    scrypt(password, salt, keyLength, (err, derivedKey) => {
      if (err)
        reject(err)
      else resolve(timingSafeEqual(key, derivedKey))
    })
  })
}
