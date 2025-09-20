import { create, importEncryptSecret } from 'uncsrf'

import { CSRF_COOKIE_NAME } from '@/constants/csrf'

defineRouteMeta({
  openAPI: {
    tags: ['Auth'],
    summary: 'Get CSRF Token',
    description: 'Generates and returns a CSRF token to be optionally included in X-CSRF-Token header. The token is also set in an HTTP-only cookie.',
    responses: {
      200: {
        description: 'CSRF token generated successfully',
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                csrfToken: { type: 'string', description: 'The generated CSRF token' },
                success: { type: 'boolean', description: 'Indicates if the operation was successful' },
              },
              required: ['csrfToken', 'success'],
            },
          },
        },
      },
    },
  },
})

export default defineEventHandler(async (event) => {
  try {
    const runtimeConfig = useRuntimeConfig(event)
    const secret = runtimeConfig.csrfSecret

    const importedSecret = await importEncryptSecret(secret)

    const csrfToken = await create(secret, importedSecret)

    setCookie(event, CSRF_COOKIE_NAME, csrfToken, { httpOnly: true })

    return { csrfToken, success: true }
  }
  catch (error) {
    console.error('Error generating CSRF token:', error)

    throw createError({
      statusCode: 500,
      statusMessage: 'Failed to create CSRF token',
    })
  }
})
