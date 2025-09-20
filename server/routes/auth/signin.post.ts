import { authSignInSchema } from '@/schemas/auth/signin.schema'
import { authSignInJsonSchema, errorResponseJsonSchema, userResponseJsonSchema } from '@/utils/schema'

defineRouteMeta({
  openAPI: {
    tags: ['Auth'],
    summary: 'Sign In',
    description: 'Authenticate user with email and password',
    security: [{ csrfToken: [] }],
    requestBody: {
      required: true,
      content: {
        'application/json': {
          schema: authSignInJsonSchema,
          example: {
            email: 'user@example.com',
            password: 'password123',
          },
        },
      },
    },
    responses: {
      200: {
        description: 'Successfully signed in',
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                message: { type: 'string', description: 'Success message' },
                user: userResponseJsonSchema,
              },
              required: ['message', 'user'],
            },
            example: {
              message: 'Signed in successfully',
              user: {
                id: 'user123',
                email: 'user@example.com',
                name: 'John Doe',
                image: null,
                emailVerified: true,
                createdAt: '2023-01-01T00:00:00Z',
                provider: 'email',
              },
            },
          },
        },
      },
      400: {
        description: 'Invalid credentials or validation error',
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
  const body = await readValidatedBody(event, authSignInSchema.parse)

  const { loginUser } = useAuthCredentials()
  const { createSession } = useAuth()

  try {
    // Authenticate user
    const user = await loginUser(body.email, body.password)

    // Create session
    await createSession(event, user, 'email')

    return {
      message: 'Signed in successfully',
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        image: user.image,
        emailVerified: user.emailVerified,
      },
    }
  }
  catch (error: any) {
    if (error.statusCode) {
      throw error
    }
    throw createError({ statusCode: 500, statusMessage: 'Sign in failed' })
  }
})
