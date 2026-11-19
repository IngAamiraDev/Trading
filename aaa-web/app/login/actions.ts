"use server";

import { redirect } from "next/navigation";

import {
  createSession,
  destroySession,
  hasPasswordConfigured,
  verifyPassword,
} from "@/lib/auth";

export async function login(formData: FormData) {
  const password = String(formData.get("password") ?? "");

  if (!process.env.AUTH_SECRET || !(await hasPasswordConfigured())) {
    redirect("/login?error=config");
  }

  let valid = false;
  try {
    valid = await verifyPassword(password);
  } catch {
    valid = false;
  }

  if (!valid) {
    redirect("/login?error=1");
  }

  await createSession();
  redirect("/");
}

export async function logout() {
  await destroySession();
  redirect("/login");
}
