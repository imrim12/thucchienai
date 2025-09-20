import { authSetPasswordSchema } from '@/schemas/auth/set-password.schema'
import { authSetPasswordJsonSchema, errorResponseJsonSchema } from '@/utils/schema'

defineRouteMeta({
  openAPI: {
    tags: ['Auth'],
    summary: 'Set New Password',
    description: 'Set a new password using reset token',
    security: [{ csrfToken: [] }],
    requestBody: {
      required: true,
      content: {
        'application/json': {
          schema: authSetPasswordJsonSchema,
          example: {
            password: 'newpassword123',
            code: 'reset-token-here',
          },
        },
      },
    },
    responses: {
      200: {
        description: 'Password reset successfully',
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                message: { type: 'string', description: 'Success message' },
                email: { type: 'string', format: 'email', description: 'Email of the user whose password was reset' },
              },
              required: ['message', 'email'],
            },
            example: {
              message: 'Password reset successfully',
              email: 'user@example.com',
            },
          },
        },
      },
      400: {
        description: 'Invalid or expired reset token',
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
  const body = await readValidatedBody(event, authSetPasswordSchema.parse)

  const { resetPassword } = useAuthCredentials()

  try {
    const { email } = await resetPassword(body.code, body.password)

    return {
      message: 'Password reset successfully',
      email,
    }
  }
  catch (error: any) {
    if (error.statusCode) {
      throw error
    }
    throw createError({ statusCode: 500, statusMessage: 'Password reset failed' })
  }
})
