import { pgEnum } from 'drizzle-orm/pg-core'

export const identityProviderEnum = pgEnum('identity_provider', [
  'google',
  'github',
  'email',
])

export const verificationTokenTypeEnum = pgEnum('verification_token_type', [
  'email-verification',
  'password-reset',
])
