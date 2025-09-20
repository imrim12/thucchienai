import { z } from 'zod'

export const authVerifyResendSchema = z.object({
  email: z.email(),
})
