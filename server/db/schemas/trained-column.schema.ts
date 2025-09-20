import { pgTable, text, timestamp } from 'drizzle-orm/pg-core'
import { relations } from 'drizzle-orm/relations'
import { trainedDatabaseSchema } from './trained-database.schema'

export const trainedColumnSchema = pgTable('trained_columns', {
  id: text('id').primaryKey(),
  trainedDatabaseId: text('trained_database_id')
    .references(() => trainedDatabaseSchema.id, { onDelete: 'cascade' }),
  name: text('name').notNull(),
  createdAt: timestamp('created_at', { mode: 'date' }).notNull().defaultNow(),
})

export const trainedColumnsRelations = relations(trainedColumnSchema, ({ one }) => ({
  trainedDatabase: one(trainedDatabaseSchema, {
    fields: [trainedColumnSchema.trainedDatabaseId],
    references: [trainedDatabaseSchema.id],
  }),
}))
