import { timingSafeEqual } from "node:crypto";

import bcrypt from "bcryptjs";
import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";

export const SESSION_COOKIE = "aaa_session";
const SESSION_MAX_AGE = 60 * 60 * 24 * 30;

function secretKey() {
  const secret = process.env.AUTH_SECRET ?? "";
  if (!secret) {
    throw new Error("AUTH_SECRET no está configurado.");
  }
  return new TextEncoder().encode(secret);
}

export async function createSession() {
  const token = await new SignJWT({ role: "owner" })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${SESSION_MAX_AGE}s`)
    .sign(secretKey());

  const store = await cookies();
  store.set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  });
}

export async function destroySession() {
  const store = await cookies();
  store.delete(SESSION_COOKIE);
}

export async function getSession() {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token || !process.env.AUTH_SECRET) {
    return null;
  }
  try {
    const { payload } = await jwtVerify(token, secretKey());
    return payload;
  } catch {
    return null;
  }
}

function passwordHash() {
  const encoded = process.env.APP_PASSWORD_HASH_B64?.trim();
  if (encoded) {
    try {
      return Buffer.from(encoded, "base64").toString("utf8").trim();
    } catch {
      return "";
    }
  }
  return process.env.APP_PASSWORD_HASH?.trim() ?? "";
}

export async function hasPasswordConfigured() {
  return Boolean(passwordHash() || process.env.APP_PASSWORD);
}

export async function verifyPassword(password: string) {
  const hash = passwordHash();
  if (hash) {
    return bcrypt.compare(password, hash);
  }

  const plain = process.env.APP_PASSWORD;
  if (!plain) {
    return false;
  }
  const provided = Buffer.from(password);
  const expected = Buffer.from(plain);
  if (provided.length !== expected.length) {
    return false;
  }
  return timingSafeEqual(provided, expected);
}
