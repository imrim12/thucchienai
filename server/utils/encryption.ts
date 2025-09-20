import { Buffer } from 'node:buffer'
import { createCipheriv, createDecipheriv, randomBytes } from 'node:crypto'

const algorithm = 'aes-256-gcm'

function getEncryptionKey(): string {
  const runtimeConfig = useRuntimeConfig()

  const key = runtimeConfig.authSecret
  if (!key || key.length !== 64) {
    throw new Error('NITRO_AUTH_SECRET must be a 64-character hex string (32 bytes)')
  }
  return key
}

export function encrypt(text: string): string {
  try {
    const key = Buffer.from(getEncryptionKey(), 'hex')
    const iv = randomBytes(16)
    const cipher = createCipheriv(algorithm, key, iv)

    let encrypted = cipher.update(text, 'utf8', 'hex')
    encrypted += cipher.final('hex')

    const authTag = cipher.getAuthTag()

    // Return iv:authTag:encrypted
    return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`
  }
  catch (error) {
    console.error('Encryption error:', error)
    throw new Error('Failed to encrypt data')
  }
}

export function decrypt(encryptedData: string): string {
  try {
    const key = Buffer.from(getEncryptionKey(), 'hex')
    const parts = encryptedData.split(':')

    if (parts.length !== 3) {
      throw new Error('Invalid encrypted data format')
    }

    const [ivHex, authTagHex, encrypted] = parts
    const iv = Buffer.from(ivHex, 'hex')
    const authTag = Buffer.from(authTagHex, 'hex')

    const decipher = createDecipheriv(algorithm, key, iv)
    decipher.setAuthTag(authTag)

    let decrypted = decipher.update(encrypted, 'hex', 'utf8')
    decrypted += decipher.final('utf8')

    return decrypted
  }
  catch (error) {
    console.error('Decryption error:', error)
    throw new Error('Failed to decrypt data')
  }
}

export function encryptIfExists(data: string | undefined | null): string | null {
  if (!data)
    return null
  return encrypt(data)
}

export function decryptIfExists(encryptedData: string | null): string | null {
  if (!encryptedData)
    return null
  return decrypt(encryptedData)
}
