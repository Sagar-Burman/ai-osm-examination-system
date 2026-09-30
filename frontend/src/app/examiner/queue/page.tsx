"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/layout/DashboardLayout";

type Sheet = {
  sheet_id: number;
  anonymous_code: string;
  exam: string;
  pages: number;
  status: string;
  progress: number;
};

const statusStyles: Record<string, string> = {
  RESULT_READY: "bg-green-50 text-green-700",
  SUBMITTED: "bg-blue-50 text-blue-700",
  FLAGGED: "bg-red-50 text-red-700",
  APPROVED: "bg-green-50 text-green-700",
  PENDING: "bg-amber-50 text-amber-700",
  COMPLETED: "bg-green-50 text-green-700",
};

export default function ExaminerQueuePage() {
  const [sheets, setSheets] = useState<Sheet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    fetch("http://127.0.0.1:8000/examiner/queue", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(
            `Failed to load queue: ${response.status}`
          );
        }

        return response.json();
      })
      .then((data: Sheet[]) => {
        setSheets(data);
      })
      .catch((err) => {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load queue."
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const assignedCount = sheets.length;

  const pendingCount = sheets.filter(
    (sheet) =>
      sheet.status === "SUBMITTED" ||
      sheet.status === "PENDING"
  ).length;

  const completedCount = sheets.filter(
    (sheet) =>
      sheet.status === "RESULT_READY" ||
      sheet.status === "APPROVED"
  ).length;

  const flaggedCount = sheets.filter(
    (sheet) => sheet.status === "FLAGGED"
  ).length;

  const completedPercentage =
    assignedCount > 0
      ? Math.round((completedCount / assignedCount) * 100)
      : 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page heading */}
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">
            Examiner Dashboard
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Review and evaluate your assigned answer sheets.
          </p>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryCard
            label="Assigned"
            value={String(assignedCount)}
          />

          <SummaryCard
            label="Pending"
            value={String(pendingCount)}
          />

          <SummaryCard
            label="Completed"
            value={String(completedCount)}
          />

          <SummaryCard
            label="Flagged"
            value={String(flaggedCount)}
          />
        </div>

        {/* Progress */}
        <section className="rounded-lg border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-slate-900">
                Evaluation Progress
              </h3>

              <p className="mt-1 text-xs text-slate-500">
                {completedCount} of {assignedCount} assigned sheets
                completed
              </p>
            </div>

            <span className="text-sm font-semibold text-slate-700">
              {completedPercentage}%
            </span>
          </div>

          <div className="mt-4 h-2 w-full rounded-full bg-slate-100">
            <div
              className="h-2 rounded-full bg-blue-800"
              style={{
                width: `${completedPercentage}%`,
              }}
            />
          </div>
        </section>

        {/* Queue table */}
        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-slate-900">
              Assigned Sheets
            </h3>

            <p className="mt-1 text-xs text-slate-500">
              Answer sheets assigned to you for evaluation.
            </p>
          </div>

          {loading && (
            <div className="px-5 py-8 text-center text-sm text-slate-500">
              Loading assigned sheets...
            </div>
          )}

          {!loading && error && (
            <div className="px-5 py-8 text-center text-sm text-red-600">
              {error}
            </div>
          )}

          {!loading && !error && sheets.length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-slate-500">
              No assigned sheets found.
            </div>
          )}

          {!loading && !error && sheets.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-5 py-3 font-medium">
                      Anonymous Code
                    </th>

                    <th className="px-5 py-3 font-medium">
                      Exam
                    </th>

                    <th className="px-5 py-3 font-medium">
                      Pages
                    </th>

                    <th className="px-5 py-3 font-medium">
                      Status
                    </th>

                    <th className="px-5 py-3 font-medium">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">
                  {sheets.map((sheet) => (
                    <tr
                      key={sheet.sheet_id}
                      className="hover:bg-slate-50"
                    >
                      <td className="px-5 py-4 font-medium text-slate-900">
                        {sheet.anonymous_code}
                      </td>

                      <td className="px-5 py-4 text-slate-600">
                        {sheet.exam}
                      </td>

                      <td className="px-5 py-4 text-slate-600">
                        {sheet.pages}
                      </td>

                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
                            statusStyles[sheet.status] ??
                            "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {sheet.status}
                        </span>
                      </td>

                      <td className="px-5 py-4">
                        <Link
                          href={`/examiner/sheet/${sheet.sheet_id}`}
                          className="inline-flex rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Open
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </DashboardLayout>
  );
}

function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <p className="text-sm text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-2xl font-semibold text-slate-900">
        {value}
      </p>
    </div>
  );
}