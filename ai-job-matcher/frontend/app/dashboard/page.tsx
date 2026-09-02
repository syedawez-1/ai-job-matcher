"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

type Resume = {
  id: string;
  storage_path: string;
  parsed_data: any;
  uploaded_at: string;
};

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const token = (session as any)?.accessToken;

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  useEffect(() => {
    if (token) {
      apiFetch("/resumes/", {}, token)
        .then(setResumes)
        .catch((e) => setError(e.message));
    }
  }, [token]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !token) return;

    setUploading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const resume = await apiFetch("/resumes/upload", { method: "POST", body: formData }, token);
      setResumes((prev) => [resume, ...prev]);
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  if (status === "loading") return <main className="p-8">Loading...</main>;

  return (
    <main className="max-w-3xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-2">Dashboard</h1>
      <p className="text-gray-500 mb-6">Upload your resume to get started.</p>

      <label className="block border-2 border-dashed rounded-lg p-6 text-center cursor-pointer mb-8">
        <input type="file" accept="application/pdf" className="hidden" onChange={handleUpload} />
        {uploading ? "Uploading and parsing..." : "Click to upload a PDF resume"}
      </label>

      {error && <p className="text-red-500 mb-4">{error}</p>}

      <div className="flex flex-col gap-6">
        {resumes.map((resume) => (
          <div key={resume.id} className="border rounded-lg p-4">
            <p className="text-sm text-gray-400 mb-2">
              Uploaded {new Date(resume.uploaded_at).toLocaleString()}
            </p>
            {resume.parsed_data?.error ? (
              <p className="text-red-500">{resume.parsed_data.error}</p>
            ) : (
              <>
                <h3 className="font-semibold mb-1">Skills</h3>
                <p className="mb-3 text-sm">{(resume.parsed_data?.skills || []).join(", ") || "—"}</p>
                <h3 className="font-semibold mb-1">Experience</h3>
                <ul className="text-sm mb-3 list-disc list-inside">
                  {(resume.parsed_data?.experience || []).map((exp: any, i: number) => (
                    <li key={i}>
                      {exp.title} @ {exp.company} ({exp.duration})
                    </li>
                  ))}
                </ul>
                <a
                  href={`/jobs?resume_id=${resume.id}`}
                  className="text-blue-600 text-sm underline"
                >
                  See matching jobs →
                </a>
              </>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
