import { authVerifySchema } from '@/schemas/auth/verify.schema'
import { errorResponseJsonSchema } from '@/utils/schema'

defineRouteMeta({
  openAPI: {
    tags: ['Auth'],
    summary: 'Verify Email',
    description: 'Verify user email using verification token',
    parameters: [
      {
        name: 'code',
        in: 'query',
        required: true,
        schema: { type: 'string' },
        description: 'Email verification token',
        example: 'verification-token-here',
      },
    ],
    responses: {
      200: {
        description: 'Email verified successfully',
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                message: { type: 'string', description: 'Success message' },
                email: { type: 'string', format: 'email', description: 'Verified email address' },
              },
              required: ['message', 'email'],
            },
            example: {
              message: 'Email verified successfully',
              email: 'user@example.com',
            },
          },
        },
      },
      400: {
        description: 'Invalid or expired verification token',
        content: {
          'application/json': {
            schema: errorResponseJsonSchema,
          },
        },
      },
      500: {
        description: 'Internal server error',
        content: {
          'application/json': {
            schema: errorResponseJsonSchema,
          },
        },
      },
    },
  },
})

export default defineEventHandler(async (event) => {
  const query = await getValidatedQuery(event, authVerifySchema.parse)

  const { verifyEmail } = useAuthCredentials()

  try {
    const { email } = await verifyEmail(query.code)

    return {
      message: 'Email verified successfully',
      email,
    }
  }
  catch (error: any) {
    if (error.statusCode) {
      throw error
    }
    throw createError({ statusCode: 500, statusMessage: 'Email verification failed' })
  }
})
