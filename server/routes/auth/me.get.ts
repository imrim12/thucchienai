import { errorResponseJsonSchema, userResponseJsonSchema } from '@/utils/schema'

defineRouteMeta({
  openAPI: {
    tags: ['Auth'],
    summary: 'Get Current User',
    description: 'Get information about the currently authenticated user',
    security: [{ cookieAuth: [] }],
    responses: {
      200: {
        description: 'Current user information',
        content: {
          'application/json': {
            schema: userResponseJsonSchema,
            example: {
              id: 'user123',
              email: 'user@example.com',
              name: 'John Doe',
              image: 'https://github.com/johndoe.png',
              provider: 'github',
              createdAt: '2023-01-01T00:00:00Z',
            },
          },
        },
      },
      401: {
        description: 'Unauthorized - no valid session',
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

export default defineAuthenticatedEventHandler(async (_, session) => {
  try {
    return {
      id: session.userId,
      email: session.email,
      name: session.name,
      image: session.image,
      provider: session.provider,
      createdAt: session.createdAt,
    }
  }
  catch (error: any) {
    console.error('Get user session error:', error)

    if (error.statusCode) {
      throw error
    }

    throw createError({
      statusCode: 500,
      statusMessage: 'Internal server error',
    })
  }
})
