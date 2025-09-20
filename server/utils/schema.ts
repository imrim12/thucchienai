import { createSelectSchema } from 'drizzle-zod'
import { z } from 'zod'
import { userSchema } from '@/db/schemas/user.schema'

// Import existing auth schemas
import { authForgotPasswordSchema } from '@/schemas/auth/forgot-password.schema'
import { authSetPasswordSchema } from '@/schemas/auth/set-password.schema'
import { authSignInSchema } from '@/schemas/auth/signin.schema'
import { authSignUpSchema } from '@/schemas/auth/signup.schema'
import { authVerifyResendSchema } from '@/schemas/auth/verify-resend.schema'
import { authVerifySchema } from '@/schemas/auth/verify.schema'

// Convert Drizzle schema to Zod schema
export const userSelectSchema = createSelectSchema(userSchema)

// Response schemas derived from Drizzle - JSON Schema compatible versions
export const userResponseSchema = z.object({
  id: z.string().describe('User ID'),
  email: z.string().describe('User email address'),
  name: z.string().nullable().describe('User display name'),
  image: z.string().nullable().describe('User profile image URL'),
  emailVerified: z.string().nullable().describe('Email verification timestamp'),
  createdAt: z.string().describe('Account creation timestamp'),
  provider: z.string().describe('Authentication provider'),
})

// Helper function to convert Zod schema to JSON Schema
export function zodToJsonSchema(schema: z.ZodType): any {
  try {
    return z.toJSONSchema(schema)
  }
  catch (error) {
    console.error('Error converting Zod schema to JSON Schema:', error)
    // Fallback to a basic object schema if conversion fails
    return {
      type: 'object',
      description: 'Schema conversion failed',
    }
  }
}

// Pre-converted JSON schemas for reuse
export const userResponseJsonSchema = zodToJsonSchema(userResponseSchema)
export const authSignInJsonSchema = zodToJsonSchema(authSignInSchema)
export const authSignUpJsonSchema = zodToJsonSchema(authSignUpSchema)
export const authForgotPasswordJsonSchema = zodToJsonSchema(authForgotPasswordSchema)
export const authSetPasswordJsonSchema = zodToJsonSchema(authSetPasswordSchema)
export const authVerifyJsonSchema = zodToJsonSchema(authVerifySchema)
export const authVerifyResendJsonSchema = zodToJsonSchema(authVerifyResendSchema)

// Common response schemas
export const successResponseSchema = z.object({
  message: z.string(),
  success: z.boolean().optional(),
})

export const errorResponseSchema = z.object({
  statusCode: z.number(),
  statusMessage: z.string(),
})

// GitHub repository schema
export const githubRepositorySchema = z.object({
  id: z.number().describe('GitHub repository ID'),
  name: z.string().describe('Repository name'),
  fullName: z.string().describe('Full repository name (owner/repo)'),
  isPrivate: z.boolean().describe('Whether repository is private'),
  description: z.string().nullable().describe('Repository description'),
  url: z.string().describe('Repository HTML URL'),
  lastUpdated: z.string().describe('Last update timestamp in ISO format'),
})

export const githubRepositoriesResponseSchema = z.object({
  success: z.boolean().describe('Operation success indicator'),
  repositories: z.array(githubRepositorySchema).describe('List of user repositories'),
  scopes: z.array(z.string()).describe('GitHub OAuth scopes'),
})

export const successResponseJsonSchema = zodToJsonSchema(successResponseSchema)
export const errorResponseJsonSchema = zodToJsonSchema(errorResponseSchema)
export const githubRepositoryJsonSchema = zodToJsonSchema(githubRepositorySchema)
export const githubRepositoriesResponseJsonSchema = zodToJsonSchema(githubRepositoriesResponseSchema)
