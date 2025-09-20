import { drizzle } from 'drizzle-orm/node-postgres'

import * as schema from '@/db/schemas'

export function useDbSchema() {
  return schema
}

export function useDb() {
  const runtimeConfig = useRuntimeConfig()

  return drizzle(
    runtimeConfig.databaseUrl,
    {
      schema,
    },
  )
}
