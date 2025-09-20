import { and, eq } from 'drizzle-orm'
import { hashPassword, verifyPassword } from '@/utils/auth'
import { createJwt } from '@/utils/jwt'

export default function useAuthCredentials() {
  const db = useDb()
  const { userSchema, identitySchema, verificationTokenSchema } = useDbSchema()

  async function registerUser(email: string, password: string, name: string) {
    // Check if user already exists
    const existingUser = await db.query.userSchema.findFirst({
      where: eq(userSchema.email, email),
    })
    if (existingUser) {
      throw createError({ statusCode: 400, statusMessage: 'User already exists' })
    }

    // Hash password
    const hashedPassword = await hashPassword(password)

    // Create user
    const userId = crypto.randomUUID()
    await db.insert(userSchema).values({
      id: userId,
      email,
      name,
      emailVerified: null,
    })

    // Create email identity
    await db.insert(identitySchema).values({
      userId,
      providerName: 'email',
      providerUserId: email,
      password: hashedPassword,
    })

    return { userId, email }
  }

  async function loginUser(email: string, password: string) {
    // Find user with email identity
    const user = await db.query.userSchema.findFirst({
      where: eq(userSchema.email, email),
      with: {
        identities: {
          where: eq(identitySchema.providerName, 'email'),
        },
      },
    })

    if (!user) {
      throw createError({ statusCode: 401, statusMessage: 'Invalid credentials' })
    }

    const emailIdentity = user.identities[0]
    if (!emailIdentity?.password) {
      throw createError({ statusCode: 401, statusMessage: 'Invalid credentials' })
    }

    // Verify password
    const isValid = await verifyPassword(password, emailIdentity.password)
    if (!isValid) {
      throw createError({ statusCode: 401, statusMessage: 'Invalid credentials' })
    }

    // Check if email is verified
    if (!user.emailVerified) {
      throw createError({ statusCode: 401, statusMessage: 'Email not verified' })
    }

    return user
  }

  async function createVerificationToken(email: string, type: 'email-verification' | 'password-reset', expiresInHours: number = 24) {
    // Invalidate all existing active tokens for this identifier and type
    await db.update(verificationTokenSchema)
      .set({ active: false })
      .where(and(
        eq(verificationTokenSchema.identifier, email),
        eq(verificationTokenSchema.type, type),
        eq(verificationTokenSchema.active, true),
      ))

    const token = await createJwt({ email, type }, `${expiresInHours}h`)
    const expires = new Date(Date.now() + expiresInHours * 60 * 60 * 1000)

    await db.insert(verificationTokenSchema).values({
      identifier: email,
      token,
      type,
      expires,
      active: true,
    })

    return token
  }

  async function verifyToken(token: string) {
    const storedToken = await db.query.verificationTokenSchema.findFirst({
      where: and(
        eq(verificationTokenSchema.token, token),
        eq(verificationTokenSchema.active, true),
      ),
    })

    if (!storedToken) {
      throw createError({ statusCode: 400, statusMessage: 'Invalid token' })
    }

    if (storedToken.expires < new Date()) {
      await db.update(verificationTokenSchema)
        .set({ active: false })
        .where(eq(verificationTokenSchema.token, token))
      throw createError({ statusCode: 400, statusMessage: 'Token expired' })
    }

    return storedToken
  }

  async function verifyEmail(token: string) {
    const tokenData = await verifyToken(token)

    if (tokenData.type !== 'email-verification') {
      throw createError({ statusCode: 400, statusMessage: 'Invalid token type' })
    }

    // Update user email verification
    await db.update(userSchema)
      .set({ emailVerified: new Date() })
      .where(eq(userSchema.email, tokenData.identifier))

    // Deactivate verification token
    await db.update(verificationTokenSchema)
      .set({ active: false })
      .where(eq(verificationTokenSchema.token, token))

    return { email: tokenData.identifier }
  }

  async function resetPassword(token: string, newPassword: string) {
    const tokenData = await verifyToken(token)

    if (tokenData.type !== 'password-reset') {
      throw createError({ statusCode: 400, statusMessage: 'Invalid token type' })
    }

    // Hash new password
    const hashedPassword = await hashPassword(newPassword)

    // Find user and update password in identity
    const user = await db.query.userSchema.findFirst({
      where: eq(userSchema.email, tokenData.identifier),
    })
    if (!user) {
      throw createError({ statusCode: 400, statusMessage: 'User not found' })
    }

    await db.update(identitySchema)
      .set({ password: hashedPassword })
      .where(and(
        eq(identitySchema.userId, user.id),
        eq(identitySchema.providerName, 'email'),
      ))

    // Deactivate verification token
    await db.update(verificationTokenSchema)
      .set({ active: false })
      .where(eq(verificationTokenSchema.token, token))

    return { email: tokenData.identifier }
  }

  async function canResendVerification(email: string, type: 'email-verification' | 'password-reset'): Promise<boolean> {
    const oneMinuteAgo = new Date(Date.now() - 60 * 1000) // 1 minute ago

    const recentToken = await db.query.verificationTokenSchema.findFirst({
      where: and(
        eq(verificationTokenSchema.identifier, email),
        eq(verificationTokenSchema.type, type),
        eq(verificationTokenSchema.active, true),
      ),
      orderBy: (tokens, { desc }) => [desc(tokens.expires)],
    })

    if (!recentToken)
      return true

    // Check if the token was created less than 1 minute ago
    // We estimate creation time by subtracting expiry duration from expires time
    const expiryDuration = type === 'email-verification' ? 1 * 60 * 60 * 1000 : 24 * 60 * 60 * 1000 // 1h for email verification, 24h for password reset
    const estimatedCreationTime = new Date(recentToken.expires.getTime() - expiryDuration)

    return estimatedCreationTime <= oneMinuteAgo
  }

  async function resendVerificationEmail(email: string) {
    // Check if user exists
    const user = await db.query.userSchema.findFirst({
      where: eq(userSchema.email, email),
    })
    if (!user) {
      throw createError({ statusCode: 404, statusMessage: 'User not found' })
    }

    // Check if user is already verified
    if (user.emailVerified) {
      throw createError({ statusCode: 400, statusMessage: 'Email already verified' })
    }

    // Check throttling
    const canResend = await canResendVerification(email, 'email-verification')
    if (!canResend) {
      throw createError({ statusCode: 429, statusMessage: 'Please wait 1 minute before requesting another verification email' })
    }

    // Create new verification token (1 hour expiry)
    const verificationToken = await createVerificationToken(email, 'email-verification', 1)

    return { token: verificationToken, email }
  }

  return {
    registerUser,
    loginUser,
    createVerificationToken,
    verifyEmail,
    resetPassword,
    canResendVerification,
    resendVerificationEmail,
  }
}
