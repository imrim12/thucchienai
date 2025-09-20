import { template } from 'es-toolkit/compat'
import { withQuery } from 'ufo'
import { authVerifyResendSchema } from '@/schemas/auth/verify-resend.schema'
import { authVerifyResendJsonSchema, errorResponseJsonSchema, successResponseJsonSchema } from '@/utils/schema'

defineRouteMeta({
  openAPI: {
    tags: ['Auth'],
    summary: 'Resend Email Verification',
    description: 'Resend email verification to user',
    security: [{ csrfToken: [] }],
    requestBody: {
      required: true,
      content: {
        'application/json': {
          schema: authVerifyResendJsonSchema,
          example: {
            email: 'user@example.com',
          },
        },
      },
    },
    responses: {
      200: {
        description: 'Verification email sent',
        content: {
          'application/json': {
            schema: successResponseJsonSchema,
            example: {
              message: 'Verification email sent successfully. Please check your inbox.',
            },
          },
        },
      },
      400: {
        description: 'Invalid email or user not found',
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
  const runtimeConfig = useRuntimeConfig()
  const body = await readValidatedBody(event, authVerifyResendSchema.parse)

  const { resendVerificationEmail } = useAuthCredentials()
  const { sendMail } = useEmail()

  try {
    // Resend verification email with throttling check
    const { token, email } = await resendVerificationEmail(body.email)

    // Send verification email
    const verifyEmailTemplate = await useStorage('assets:server').getItem('templates/verify.ejs')

    await sendMail(
      'Verify your email',
      template(verifyEmailTemplate.toString())({
        appName: 'THECODEORIGIN',
        verificationLink: withQuery(`${runtimeConfig.apiUrl}/auth/verify`, {
          code: token,
        }),
      }),
      email,
    )

    return { message: 'Verification email sent successfully. Please check your inbox.' }
  }
  catch (error: any) {
    if (error.statusCode) {
      throw error
    }
    throw createError({ statusCode: 500, statusMessage: 'Failed to resend verification email' })
  }
})
