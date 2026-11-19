CREATE TABLE "candidates" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"run_id" uuid NOT NULL,
	"mode" text NOT NULL,
	"ticker" text NOT NULL,
	"company" text DEFAULT '' NOT NULL,
	"sector" text DEFAULT '' NOT NULL,
	"industry" text DEFAULT '' NOT NULL,
	"status" text NOT NULL,
	"score" double precision DEFAULT 0 NOT NULL,
	"a1" boolean,
	"a2" boolean,
	"a3" boolean,
	"setup" text DEFAULT '' NOT NULL,
	"price" double precision,
	"entry" double precision,
	"stop" double precision,
	"target" double precision,
	"rr" double precision,
	"risk_pct" double precision,
	"shares" integer,
	"earnings" text,
	"last_bar" text,
	"selected" boolean DEFAULT false NOT NULL,
	"source" text DEFAULT '' NOT NULL,
	"reasons" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"metrics" jsonb DEFAULT '{}'::jsonb NOT NULL
);
--> statement-breakpoint
CREATE TABLE "regime_indices" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"run_id" uuid NOT NULL,
	"symbol" text NOT NULL,
	"close" double precision,
	"sma_fast" double precision,
	"sma_slow" double precision,
	"above_fast" boolean,
	"above_slow" boolean,
	"last_bar" text,
	"error" text
);
--> statement-breakpoint
CREATE TABLE "scan_runs" (
	"id" uuid PRIMARY KEY NOT NULL,
	"generated_at" timestamp with time zone NOT NULL,
	"trading_date" date NOT NULL,
	"regime" text NOT NULL,
	"vix" double precision,
	"capital" double precision,
	"source" text DEFAULT 'cli' NOT NULL,
	"leaders" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"errors" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"notes" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"modes" jsonb DEFAULT '{}'::jsonb NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "candidates" ADD CONSTRAINT "candidates_run_id_scan_runs_id_fk" FOREIGN KEY ("run_id") REFERENCES "public"."scan_runs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "regime_indices" ADD CONSTRAINT "regime_indices_run_id_scan_runs_id_fk" FOREIGN KEY ("run_id") REFERENCES "public"."scan_runs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE UNIQUE INDEX "candidates_run_mode_ticker_idx" ON "candidates" USING btree ("run_id","mode","ticker");--> statement-breakpoint
CREATE INDEX "candidates_ticker_idx" ON "candidates" USING btree ("ticker");--> statement-breakpoint
CREATE INDEX "candidates_status_idx" ON "candidates" USING btree ("status");--> statement-breakpoint
CREATE INDEX "candidates_score_idx" ON "candidates" USING btree ("score");--> statement-breakpoint
CREATE UNIQUE INDEX "regime_indices_run_symbol_idx" ON "regime_indices" USING btree ("run_id","symbol");--> statement-breakpoint
CREATE INDEX "scan_runs_generated_at_idx" ON "scan_runs" USING btree ("generated_at");