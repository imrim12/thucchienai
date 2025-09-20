import { pgTable, primaryKey, text, timestamp } from 'drizzle-orm/pg-core'
import { relations } from 'drizzle-orm/relations'
import { identityProviderEnum } from './enum.schema'
import { userSchema } from './user.schema'

export const identitySchema = pgTable(
  'identities',
  {
    userId: text('user_id')
      .notNull()
      .references(() => userSchema.id, { onDelete: 'cascade' }),
    providerName: identityProviderEnum('provider_name').notNull(),
    providerUserId: text('provider_user_id').notNull(),
    password: text('password'),
    // OAuth session data for integrations
    accessToken: text('access_token'), // Store encrypted access token
    refreshToken: text('refresh_token'), // Store encrypted refresh token (for Google)
    tokenExpiresAt: timestamp('token_expires_at', { mode: 'date' }), // Token expiry time
    scopes: text('scopes'), // Comma-separated list of granted scopes
    createdAt: timestamp('created_at', { mode: 'date' }).notNull().defaultNow(),
    updatedAt: timestamp('updated_at', { mode: 'date' })
      .notNull()
      .defaultNow()
      .$onUpdate(() => new Date()),
  },
  table => [
    primaryKey({ columns: [table.providerName, table.providerUserId] }),
  ],
)

export const identitiesRelations = relations(identitySchema, ({ one }) => ({
  user: one(userSchema, {
    fields: [identitySchema.userId],
    references: [userSchema.id],
  }),
}))
