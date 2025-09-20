import { errorResponseJsonSchema } from '@/utils/schema'

defineRouteMeta({
  openAPI: {
    tags: ['Auth'],
    summary: 'Sign Out',
    description: 'Sign out the current user and clear session',
    security: [{ cookieAuth: [] }, { csrfToken: [] }],
    responses: {
      200: {
        description: 'Successfully signed out',
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                success: { type: 'boolean', description: 'Operation success indicator' },
                message: { type: 'string', description: 'Success message' },
              },
              required: ['success', 'message'],
            },
            example: {
              success: true,
              message: 'Successfully logged out',
            },
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
  try {
    const { clearSession } = useAuth()

    // Clear the session from Redis and remove cookie
    await clearSession(event)

    return {
      success: true,
      message: 'Successfully logged out',
    }
  }
  catch (error: any) {
    console.error('Logout error:', error)

    throw createError({
      statusCode: 500,
      statusMessage: 'Internal server error during signout',
    })
  }
})
