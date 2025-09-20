import { z } from 'zod'

export const authSetPasswordSchema = z.object({
  password: z.string().min(8).max(100),
  code: z.string(),
})
