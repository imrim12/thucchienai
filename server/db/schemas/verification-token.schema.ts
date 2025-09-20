import { boolean, pgTable, primaryKey, text, timestamp } from 'drizzle-orm/pg-core'
import { verificationTokenTypeEnum } from './enum.schema'

export const verificationTokenSchema = pgTable(
  'verification_tokens',
  {
    // The identifier is typically the user's email address.
    identifier: text('identifier').notNull(),
    token: text('token').notNull(),
    type: verificationTokenTypeEnum('type').notNull(),
    expires: timestamp('expires', { mode: 'date' }).notNull(),
    active: boolean('active').notNull().default(true),
  },
  (table) => {
    return {
      // A composite primary key ensures that the combination of an identifier
      // and a token is unique, which is standard for this pattern.
      pk: primaryKey({ columns: [table.identifier, table.token] }),
    }
  },
)
