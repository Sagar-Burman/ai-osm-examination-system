"use client";

import { ReactNode } from "react";

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({
  children,
}: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="flex h-16 items-center justify-between px-6">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">
              EvalAI
            </h1>
            <p className="text-xs text-slate-500">
              Examination Evaluation Portal
            </p>
          </div>

          <div className="text-sm text-slate-600">
            Examination Portal
          </div>
        </div>
      </header>

      <div className="flex">
        <aside className="hidden min-h-[calc(100vh-4rem)] w-60 border-r border-slate-200 bg-white md:block">
          <nav className="p-4">
            <div className="px-3 py-2 text-sm font-medium text-slate-700">
              Dashboard
            </div>
          </nav>
        </aside>

        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}