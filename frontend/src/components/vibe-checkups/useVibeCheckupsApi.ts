import { useCallback, useEffect, useRef } from "react";

const API = "/api/vibe-checkups";

export function useVibeCheckupsApi() {
  const csrfTokenRef = useRef<string | null>(null);
  const csrfLoadPromiseRef = useRef<Promise<void> | null>(null);

  useEffect(() => {
    csrfLoadPromiseRef.current = fetch(`${API}/csrf-token`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load CSRF token");
        return res.json() as Promise<{ csrf_token?: string }>;
      })
      .then((data) => {
        if (data.csrf_token) csrfTokenRef.current = data.csrf_token;
      });
  }, []);

  const vcPost = useCallback(async <T,>(path: string, body?: Record<string, unknown>): Promise<T> => {
    if (csrfLoadPromiseRef.current) await csrfLoadPromiseRef.current;
    const token = csrfTokenRef.current;
    if (!token) throw new Error("CSRF token not available");
    const res = await fetch(`${API}${path}`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": token,
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    if (!res.ok) {
      const err = (data.error as string) || res.statusText || "Request failed";
      throw new Error(err);
    }
    return data as T;
  }, []);

  return { vcPost, apiBase: API };
}
