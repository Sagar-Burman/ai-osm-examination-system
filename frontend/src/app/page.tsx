"use client";

import { FormEvent, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      const body = new URLSearchParams();

      body.append("username", email.trim());
      body.append("password", password);


      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("role", data.role);

      console.log("Login successful:", data);

      window.location.href = "/examiner/queue";

    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to connect to server"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-100 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-5xl overflow-hidden rounded-xl bg-white shadow-lg">
        <div className="grid min-h-[560px] md:grid-cols-2">

          {/* Left: OSM Illustration */}
          <div className="hidden bg-blue-900 md:flex items-center justify-center p-10">
            <div className="w-full max-w-sm text-center text-white">

              <div className="relative mx-auto mb-8 h-64 w-72">

                {/* Paper */}
                <div className="absolute left-16 top-4 h-56 w-40 rounded-lg bg-white p-5 shadow-xl">
                  <div className="mb-4 flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-700">
                      Question Paper
                    </span>

                    <span className="rounded bg-blue-100 px-2 py-1 text-[9px] text-blue-700">
                      OSM
                    </span>
                  </div>

                  <div className="space-y-3">
                    {[1, 2, 3].map((item) => (
                      <div key={item}>
                        <div className="mb-1 h-2 w-20 rounded bg-slate-300" />
                        <div className="h-1.5 w-full rounded bg-slate-200" />
                        <div className="mt-1 h-1.5 w-28 rounded bg-slate-200" />
                      </div>
                    ))}
                  </div>

                  {/* Mark */}
                  <div className="absolute -right-4 top-28 flex h-9 w-9 items-center justify-center rounded-full bg-green-500 text-lg font-bold text-white shadow">
                    ✓
                  </div>
                </div>

                {/* Marks panel */}
                <div className="absolute left-0 top-20 w-20 rounded-lg bg-white p-3 shadow-xl">
                  <p className="mb-3 text-[10px] font-semibold text-slate-600">
                    Marks
                  </p>

                  <div className="grid grid-cols-2 gap-2">
                    {[1, 2, 3, 4].map((mark) => (
                      <div
                        key={mark}
                        className="flex h-7 w-7 items-center justify-center rounded-full bg-green-100 text-[10px] font-semibold text-green-700"
                      >
                        {mark}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Annotation */}
                <div className="absolute bottom-2 right-1 rounded-lg bg-white px-4 py-2 text-xs font-medium text-red-500 shadow-lg">
                  ✕ Review
                </div>
              </div>

              <h2 className="text-2xl font-semibold">
                Digital Examination Evaluation
              </h2>

              <p className="mt-3 text-sm leading-6 text-blue-100">
                Secure on-screen marking for digital answer sheets with
                examiner-assisted evaluation.
              </p>
            </div>
          </div>

          {/* Right: Login */}
          <div className="flex items-center justify-center p-8 sm:p-12">
            <div className="w-full max-w-md">

              <div className="mb-8">
                <div className="mb-4 flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-900 text-lg font-bold text-white">
                    E
                  </div>

                  <div>
                    <h1 className="text-2xl font-bold text-slate-900">
                      EvalAI
                    </h1>

                    <p className="text-xs text-slate-500">
                      Examination Evaluation Portal
                    </p>
                  </div>
                </div>

                <h2 className="text-xl font-semibold text-slate-900">
                  Sign in
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Enter your credentials to access the examination portal.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">

                {/* Username */}
<div>
  <label
    htmlFor="username"
    className="mb-2 block text-sm font-medium text-slate-700"
  >
    Username
  </label>

  <input
    id="username"
    type="text"
    value={email}
    onChange={(e) => setEmail(e.target.value)}
    placeholder="Enter your username"
    required
    className="w-full border-0 border-b border-slate-300 bg-transparent px-1 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-700"
  />
</div>
                {/* Password */}
                <div>
                  <label
                    htmlFor="password"
                    className="mb-2 block text-sm font-medium text-slate-700"
                  >
                    Password
                  </label>

                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    required
                    className="w-full border-0 border-b border-slate-300 bg-transparent px-1 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-700"
                  />
                </div>

                {/* Error */}
                {error && (
                  <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    {error}
                  </div>
                )}

                {/* Sign In */}
                <button
                  type="submit"
                  disabled={loading}
                  className="mt-4 w-full rounded-md bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-blue-200"
                >
                  {loading ? "Signing in..." : "Sign In"}
                </button>
              </form>

              <p className="mt-8 text-center text-xs text-slate-400">
                EvalAI Examination Portal
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}