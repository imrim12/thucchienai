import { pgTable, text, timestamp } from 'drizzle-orm/pg-core'
import { relations } from 'drizzle-orm/relations'
import { identitySchema } from './identity.schema'

export const userSchema = pgTable('users', {
  id: text('id').primaryKey(),
  name: text('name'),
  email: text('email').notNull().unique(),
  emailVerified: timestamp('email_verified', { mode: 'date' }),
  image: text('image'), // Profile picture URL
  createdAt: timestamp('created_at', { mode: 'date' }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { mode: 'date' })
    .notNull()
    .defaultNow()
    .$onUpdate(() => new Date()),
})

export type User = typeof userSchema.$inferSelect

export type UserWithIdentities = User & {
  identities: Array<typeof identitySchema.$inferSelect>
}

export const usersRelations = relations(userSchema, ({ many }) => ({
  // A user can have many identities (e.g., Google, GitHub, Email).
  identities: many(identitySchema),
}))
