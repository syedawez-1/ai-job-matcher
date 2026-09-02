"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { apiFetch } from "@/lib/api";

type Application = {
  id: string;
  job_id: string;
  status: string;
  applied_at: string;
  notes: string | null;
};

const STATUSES = ["applied", "interviewing", "offer", "rejected"];

export default function ApplicationsPage() {
  const { data: session } = useSession();
  const token = (session as any)?.accessToken;
  const [applications, setApplications] = useState<Application[]>([]);

  useEffect(() => {
    if (token) {
      apiFetch("/applications/", {}, token).then(setApplications);
    }
  }, [token]);

  async function updateStatus(id: string, status: string) {
    const updated = await apiFetch(
      `/applications/${id}`,
      { method: "PATCH", body: JSON.stringify({ status }) },
      token
    );
    setApplications((prev) => prev.map((a) => (a.id === id ? updated : a)));
  }

  async function removeApplication(id: string) {
    await apiFetch(`/applications/${id}`, { method: "DELETE" }, token);
    setApplications((prev) => prev.filter((a) => a.id !== id));
  }

  return (
    <main className="max-w-3xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Application Tracker</h1>
      <div className="flex flex-col gap-3">
        {applications.map((app) => (
          <div key={app.id} className="border rounded-lg p-4 flex justify-between items-center">
            <div>
              <p className="text-sm text-gray-400">
                Applied {new Date(app.applied_at).toLocaleDateString()}
              </p>
              <p className="text-xs text-gray-400">Job ID: {app.job_id}</p>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={app.status}
                onChange={(e) => updateStatus(app.id, e.target.value)}
                className="border rounded p-1 text-sm"
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <button
                onClick={() => removeApplication(app.id)}
                className="text-red-500 text-sm underline"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
        {applications.length === 0 && (
          <p className="text-gray-400">No applications tracked yet — add some from the Jobs page.</p>
        )}
      </div>
    </main>
  );
}
