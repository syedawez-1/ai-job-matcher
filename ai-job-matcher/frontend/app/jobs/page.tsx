"use client";

import { Suspense, useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

type Job = {
  id: string;
  title: string;
  company: string;
  required_skills: string[];
};

type Match = Job & { match_score: number };

function JobsContent() {
  const { data: session } = useSession();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get("resume_id");
  const token = (session as any)?.accessToken;

  const [jobs, setJobs] = useState<Job[] | Match[]>([]);
  const [gapResult, setGapResult] = useState<Record<string, any>>({});
  const [applying, setApplying] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    const path = resumeId
      ? `/jobs/matches/${resumeId}`
      : "/jobs/";

    apiFetch(path, {}, token).then((data) => {
      setJobs(resumeId ? data.matches : data);
    });
  }, [token, resumeId]);

  async function checkSkillGap(jobId: string) {
    if (!resumeId || !token) return;

    const result = await apiFetch(
      `/analysis/skill-gap/${resumeId}/${jobId}`,
      {},
      token
    );

    setGapResult((prev) => ({
      ...prev,
      [jobId]: result,
    }));
  }

  async function applyToJob(jobId: string) {
    if (!token) return;

    setApplying(jobId);

    try {
      await apiFetch(
        "/applications/",
        {
          method: "POST",
          body: JSON.stringify({
            job_id: jobId,
          }),
        },
        token
      );
    } finally {
      setApplying(null);
    }
  }

  return (
    <main className="max-w-3xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">
        {resumeId ? "Matching Jobs" : "All Jobs"}
      </h1>

      <div className="flex flex-col gap-4">
        {jobs.map((job) => (
          <div key={job.id} className="border rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold">{job.title}</h3>

                <p className="text-sm text-gray-500">
                  {job.company}
                </p>
              </div>

              {"match_score" in job && (
                <span className="text-sm font-medium bg-gray-100 rounded px-2 py-1">
                  {Math.round(
                    (job as Match).match_score * 100
                  )}
                  % match
                </span>
              )}
            </div>

            <p className="text-xs text-gray-400 mt-2">
              {(job.required_skills || []).join(", ")}
            </p>

            <div className="flex gap-3 mt-3">
              {resumeId && (
                <button
                  onClick={() => checkSkillGap(job.id)}
                  className="text-sm underline text-blue-600"
                >
                  Analyze skill gap
                </button>
              )}

              <button
                onClick={() => applyToJob(job.id)}
                disabled={applying === job.id}
                className="text-sm underline text-green-600 disabled:opacity-50"
              >
                {applying === job.id
                  ? "Adding..."
                  : "Track application"}
              </button>
            </div>

            {gapResult[job.id] && (
              <div className="mt-3 text-sm bg-yellow-50 rounded p-3">
                <p>
                  <strong>Missing skills:</strong>{" "}
                  {(gapResult[job.id].missing_skills || [])
                    .join(", ") || "None!"}
                </p>

                <p className="mt-1">
                  <strong>Recommendations:</strong>{" "}
                  {(gapResult[job.id].recommendations || [])
                    .join("; ")}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}

export default function JobsPage() {
  return (
    <Suspense fallback={<div className="p-8">Loading jobs...</div>}>
      <JobsContent />
    </Suspense>
  );
}