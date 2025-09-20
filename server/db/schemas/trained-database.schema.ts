import { pgTable, text, timestamp } from 'drizzle-orm/pg-core'
import { relations } from 'drizzle-orm/relations'
import { trainedColumnSchema } from './trained-column.schema'

export const trainedDatabaseSchema = pgTable('trained_databases', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
  type: text('type').notNull(),
  connectionString: text('connection_string').notNull(),
  createdAt: timestamp('created_at', { mode: 'date' }).notNull().defaultNow(),
})

export const trainedDatabasesRelations = relations(trainedDatabaseSchema, ({ many }) => ({
  columns: many(trainedColumnSchema),
}))
