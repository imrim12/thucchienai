import { config } from 'dotenv'
import { defineConfig } from 'drizzle-kit'

config({ path: '.env' })

export default defineConfig({
  schema: [
    './server/db/schemas/index.ts',
  ],
  out: './server/db/migrations',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.NITRO_DATABASE_URL!,
    ssl: false,
  },
  verbose: true,
  strict: true,
})
