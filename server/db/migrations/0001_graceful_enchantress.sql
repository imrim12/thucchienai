ALTER TABLE "identities" RENAME COLUMN "hashed_password" TO "password";--> statement-breakpoint
ALTER TABLE "identities" ADD COLUMN "access_token" text;--> statement-breakpoint
ALTER TABLE "identities" ADD COLUMN "refresh_token" text;--> statement-breakpoint
ALTER TABLE "identities" ADD COLUMN "token_expires_at" timestamp;--> statement-breakpoint
ALTER TABLE "identities" ADD COLUMN "scopes" text;