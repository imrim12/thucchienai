import { pgTable, text, timestamp } from 'drizzle-orm/pg-core'

export const querySchema = pgTable('queries', {
  id: text('id').primaryKey(),
  question: text('question').notNull(),
  sql: text('sql').notNull(),
  embedding: text('embedding').notNull(),
  createdAt: timestamp('created_at', { mode: 'date' }).notNull().defaultNow(),
})
