import { z } from 'zod'

export const authForgotPasswordSchema = z.object({
  email: z.string(),
})
