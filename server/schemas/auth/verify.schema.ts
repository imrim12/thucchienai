import { z } from 'zod'

export const authVerifySchema = z.object({
  code: z.string(),
})
