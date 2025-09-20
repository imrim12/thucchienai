import { template } from 'es-toolkit/compat'
import { withQuery } from 'ufo'
import { authForgotPasswordSchema } from '@/schemas/auth/forgot-password.schema'
import { authForgotPasswordJsonSchema, successResponseJsonSchema } from '@/utils/schema'

defineRouteMeta({
  openAPI: {
    tags: ['Auth'],
    summary: 'Forgot Password',
    description: 'Send password reset email to user',
    security: [{ csrfToken: [] }],
    requestBody: {
      required: true,
      content: {
        'application/json': {
          schema: authForgotPasswordJsonSchema,
          example: {
            email: 'user@example.com',
          },
        },
      },
    },
    responses: {
      200: {
        description: 'Password reset email sent (always returns success to prevent email enumeration)',
        content: {
          'application/json': {
            schema: successResponseJsonSchema,
            example: {
              message: 'Password reset email sent. Please check your inbox.',
            },
          },
        },
      },
    },
  },
})

export default defineEventHandler(async (event) => {
  const runtimeConfig = useRuntimeConfig()
  const body = await readValidatedBody(event, authForgotPasswordSchema.parse)

  const { createVerificationToken } = useAuthCredentials()
  const { sendMail } = useEmail()

  try {
    // Create password reset token
    const resetToken = await createVerificationToken(body.email, 'password-reset')

    // Send password reset email
    const setPasswordEmailTemplate = await useStorage('assets:server').getItem('templates/reset-password.ejs')

    await sendMail(
      'Reset your password',
      template(setPasswordEmailTemplate.toString())({
        appName: 'THECODEORIGIN',
        resetLink: withQuery(`${runtimeConfig.appUrl}/auth/set-password`, {
          code: resetToken,
        }),
      }),
      body.email,
    )

    return { message: 'Password reset email sent. Please check your inbox.' }
  }
  catch {
    // Always return success to prevent email enumeration attacks
    return { message: 'Password reset email sent. Please check your inbox.' }
  }
})
