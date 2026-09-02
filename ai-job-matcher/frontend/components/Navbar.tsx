"use client";

import Link from "next/link";
import { useSession, signOut } from "next-auth/react";

export default function Navbar() {
  const { data: session } = useSession();

  return (
    <nav className="flex items-center justify-between px-8 py-4 border-b">
      <Link href="/" className="font-bold text-lg">
        AI Job Matcher
      </Link>
      <div className="flex items-center gap-6 text-sm">
        {session ? (
          <>
            <Link href="/dashboard">Dashboard</Link>
            <Link href="/jobs">Jobs</Link>
            <Link href="/applications">Applications</Link>
            <button onClick={() => signOut({ callbackUrl: "/" })} className="text-red-500">
              Sign out
            </button>
          </>
        ) : (
          <>
            <Link href="/login">Log in</Link>
            <Link href="/register">Sign up</Link>
          </>
        )}
      </div>
    </nav>
  );
}
