import { z } from 'zod'

export const authSignUpSchema = z.object({
  name: z.string().max(256),
  email: z.email(),
  password: z.string().min(8).max(100),
})
