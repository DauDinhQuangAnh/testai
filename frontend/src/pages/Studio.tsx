import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import NavBar from "../components/NavBar";
import StageProgress from "../components/StageProgress";
import { api } from "../lib/api";
import { STATUS_LABELS } from "../lib/constants";
import type { JobOut } from "../lib/types";

const FILTERS = [
  { key: "all", label: "Tất cả" },
  { key: "active", label: "Đang xử lý" },
  { key: "done", label: "Hoàn thành" },
  { key: "failed", label: "Thất bại" },
];

const STATUS_BADGE: Record<string, string> = {
  queued: "bg-amber-100 text-amber-700",
  running: "bg-blue-100 text-blue-700",
  done: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export default function Studio() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("all");

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.get<JobOut[]>("/api/jobs"),
    refetchInterval: 3000,
  });

  const deleteJob = useMutation({
    mutationFn: (id: string) => api.del(`/api/jobs/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
  });
  const rerunJob = useMutation({
    mutationFn: (id: string) => api.post(`/api/jobs/${id}/rerun`, {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
  });

  const visible = jobs.filter((j) => {
    if (filter === "active") return j.status === "queued" || j.status === "running";
    if (filter === "done") return j.status === "done";
    if (filter === "failed") return j.status === "failed";
    return true;
  });

  const counts = {
    total: jobs.length,
    active: jobs.filter((j) => j.status === "queued" || j.status === "running").length,
    done: jobs.filter((j) => j.status === "done").length,
    failed: jobs.filter((j) => j.status === "failed").length,
  };

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Studio</h1>
          <Link to="/studio/new" className="btn-primary">
            + Tạo video mới
          </Link>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            ["Tổng số job", counts.total],
            ["Đang xử lý", counts.active],
            ["Hoàn thành", counts.done],
            ["Thất bại", counts.failed],
          ].map(([label, n]) => (
            <div key={label} className="card py-4 text-center">
              <div className="text-2xl font-bold">{n}</div>
              <div className="text-sm text-ink-soft">{label}</div>
            </div>
          ))}
        </div>

        <div className="mb-4 flex gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={
                "rounded-lg px-4 py-1.5 text-sm font-medium transition " +
                (filter === f.key
                  ? "bg-primary text-white"
                  : "border border-line bg-white text-ink-soft hover:text-ink")
              }
            >
              {f.label}
            </button>
          ))}
        </div>

        {isLoading && <p className="text-ink-soft">Đang tải...</p>}
        {!isLoading && visible.length === 0 && (
          <div className="card py-12 text-center text-ink-soft">
            Chưa có job nào.{" "}
            <Link to="/studio/new" className="font-medium text-primary">
              Tạo video đầu tiên
            </Link>
          </div>
        )}

        <div className="space-y-4">
          {visible.map((job) => (
            <div key={job.id} className="card">
              <div className="mb-2 flex items-center justify-between gap-3">
                <Link
                  to={`/studio/jobs/${job.id}`}
                  className="truncate font-semibold hover:text-primary"
                  title={job.filename}
                >
                  {job.filename}
                </Link>
                <span
                  className={
                    "shrink-0 rounded-full px-3 py-0.5 text-xs font-semibold " +
                    (STATUS_BADGE[job.status] ?? "")
                  }
                >
                  {STATUS_LABELS[job.status] ?? job.status}
                </span>
              </div>
              {(job.status === "queued" || job.status === "running") && (
                <StageProgress progress={job.progress} label={job.stage_label} />
              )}
              {job.error_message && (
                <p className="mt-2 max-h-20 overflow-hidden rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  {job.error_message}
                </p>
              )}
              <div className="mt-3 flex items-center justify-between text-sm text-ink-soft">
                <span>Tạo lúc: {new Date(job.created_at).toLocaleString("vi-VN")}</span>
                <span className="flex gap-2">
                  <Link to={`/studio/jobs/${job.id}`} className="btn-ghost px-3 py-1 text-xs">
                    Chi tiết
                  </Link>
                  <button
                    className="btn-ghost px-3 py-1 text-xs"
                    onClick={() => rerunJob.mutate(job.id)}
                  >
                    Tạo lại
                  </button>
                  <button
                    className="btn-ghost px-3 py-1 text-xs text-red-600 hover:border-red-400"
                    onClick={() => {
                      if (confirm(`Xóa vĩnh viễn job "${job.filename}"?`))
                        deleteJob.mutate(job.id);
                    }}
                  >
                    Xóa
                  </button>
                </span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
