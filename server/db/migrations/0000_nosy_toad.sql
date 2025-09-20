CREATE TYPE "public"."identity_provider" AS ENUM('google', 'github', 'email');--> statement-breakpoint
CREATE TYPE "public"."verification_token_type" AS ENUM('email-verification', 'password-reset');--> statement-breakpoint
CREATE TABLE "identities" (
	"user_id" text NOT NULL,
	"provider_name" "identity_provider" NOT NULL,
	"provider_user_id" text NOT NULL,
	"hashed_password" text,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "identities_provider_name_provider_user_id_pk" PRIMARY KEY("provider_name","provider_user_id")
);
--> statement-breakpoint
CREATE TABLE "one_time_passwords" (
	"phone" text PRIMARY KEY NOT NULL,
	"code" text NOT NULL,
	"expires" timestamp NOT NULL,
	"attempts" integer DEFAULT 0 NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "users" (
	"id" text PRIMARY KEY NOT NULL,
	"name" text,
	"email" text NOT NULL,
	"email_verified" timestamp,
	"image" text,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "users_email_unique" UNIQUE("email")
);
--> statement-breakpoint
CREATE TABLE "verification_tokens" (
	"identifier" text NOT NULL,
	"token" text NOT NULL,
	"type" "verification_token_type" NOT NULL,
	"expires" timestamp NOT NULL,
	CONSTRAINT "verification_tokens_identifier_token_pk" PRIMARY KEY("identifier","token")
);
--> statement-breakpoint
ALTER TABLE "identities" ADD CONSTRAINT "identities_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;