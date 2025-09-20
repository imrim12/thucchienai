import { integer, pgTable, text, timestamp } from 'drizzle-orm/pg-core'

export const otpSchema = pgTable('one_time_passwords', {
  phone: text('phone').primaryKey(), // The phone number serves as the unique identifier
  code: text('code').notNull(), // IMPORTANT: This should be a HASHED value
  expires: timestamp('expires', { mode: 'date' }).notNull(),
  attempts: integer('attempts').notNull().default(0),
  createdAt: timestamp('created_at', { mode: 'date' }).notNull().defaultNow(),
})
