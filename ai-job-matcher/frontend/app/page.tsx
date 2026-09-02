import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 text-center">
      <h1 className="text-4xl font-bold">AI Job Matcher</h1>
      <p className="mt-4 text-gray-500 max-w-md">
        Upload your resume, get an AI-powered skill-gap analysis, match with
        real jobs, and track your applications — all in one place.
      </p>
      <div className="mt-8 flex gap-4">
        <Link href="/register" className="bg-black text-white rounded px-4 py-2">
          Get started
        </Link>
        <Link href="/login" className="border rounded px-4 py-2">
          Log in
        </Link>
      </div>
    </main>
  );
}
