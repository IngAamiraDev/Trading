import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";

import * as schema from "./schema";

const connectionString =
  process.env.DATABASE_URL ??
  "postgresql://postgres:postgres@127.0.0.1:5432/aaa_web";

declare global {
  // eslint-disable-next-line no-var
  var __aaaSql: ReturnType<typeof postgres> | undefined;
}

function createClient() {
  return postgres(connectionString, {
    max: 5,
    prepare: false,
    idle_timeout: 20,
    connect_timeout: 15,
  });
}

export const sql = global.__aaaSql ?? createClient();

if (process.env.NODE_ENV !== "production") {
  global.__aaaSql = sql;
}

export const db = drizzle(sql, { schema });
