import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import NavBar from "../components/NavBar";
import StageProgress from "../components/StageProgress";
import { api, fileUrl } from "../lib/api";
import { STATUS_LABELS } from "../lib/constants";
import type { JobFilesOut, JobOut } from "../lib/types";

export default function JobDetail() {
  const { id = "" } = useParams();
  const [expandedPreview, setExpandedPreview] = useState<string | null>(null);

  const { data: job } = useQuery({
    queryKey: ["job", id],
    queryFn: () => api.get<JobOut>(`/api/jobs/${id}`),
    refetchInterval: (query) =>
      query.state.data?.status === "queued" || query.state.data?.status === "running"
        ? 3000
        : false,
  });

  const { data: files } = useQuery({
    queryKey: ["job-files", id, job?.status],
    queryFn: () => api.get<JobFilesOut>(`/api/jobs/${id}/files`),
    enabled: job?.status === "done",
  });

  if (!job) {
    return (
      <div className="min-h-screen">
        <NavBar />
        <main className="mx-auto max-w-4xl px-4 py-8 text-ink-soft">Đang tải...</main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="mx-auto max-w-4xl px-4 py-8">
        <Link to="/studio" className="text-sm text-ink-soft hover:text-primary">
          ← Quay lại Studio
        </Link>
        <h1 className="mb-1 mt-2 break-all text-2xl font-bold">{job.filename}</h1>
        <p className="mb-6 text-sm text-ink-soft">
          {STATUS_LABELS[job.status]} · Tạo lúc {new Date(job.created_at).toLocaleString("vi-VN")}
        </p>

        {(job.status === "queued" || job.status === "running") && (
          <div className="card mb-6">
            <StageProgress progress={job.progress} label={job.stage_label} />
          </div>
        )}
        {job.error_message && (
          <div className="mb-6 rounded-xl bg-amber-50 px-4 py-3 text-amber-800">
            {job.error_message}
          </div>
        )}

        {files?.videos.map((video) => (
          <div key={video.name} className="card mb-6">
            <h2 className="mb-3 font-semibold">🎬 Video đã lồng tiếng ({video.language})</h2>
            <video controls className="w-full rounded-lg bg-black" src={fileUrl(id, video.name)} />
            <a href={fileUrl(id, video.name)} download className="btn-primary mt-3">
              Tải video ({(video.size_bytes / 1024 / 1024).toFixed(1)} MB)
            </a>
          </div>
        ))}

        {files?.subtitles.map((group) => (
          <div key={group.language} className="card mb-6">
            <h2 className="mb-3 font-semibold">📝 {group.label}</h2>
            <div className="flex flex-wrap gap-2">
              {group.files.map((f) => (
                <a key={f.name} href={fileUrl(id, f.name)} download className="btn-ghost">
                  {f.format}
                </a>
              ))}
            </div>
            {group.preview_text && (
              <div className="mt-3">
                <button
                  className="text-sm font-medium text-primary"
                  onClick={() =>
                    setExpandedPreview(expandedPreview === group.language ? null : group.language)
                  }
                >
                  {expandedPreview === group.language ? "Ẩn nội dung" : "Xem trước nội dung"}
                </button>
                {expandedPreview === group.language && (
                  <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-cream p-3 text-sm">
                    {group.preview_text}
                  </pre>
                )}
              </div>
            )}
          </div>
        ))}
      </main>
    </div>
  );
}
