const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" &&
  window.location.hostname !== "localhost"
    ? "https://ai-job-matcher-i81e.onrender.com"
    : "http://localhost:8000");

export async function apiFetch(path: string, options: RequestInit = {}, token?: string) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  return res.json();
}
