import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import NavBar from "../components/NavBar";
import StageProgress from "../components/StageProgress";
import { api, fileUrl } from "../lib/api";
import { STATUS_LABELS } from "../lib/constants";
import type { JobFilesOut, JobOut } from "../lib/types";

export default function JobDetail() {
  const { id = "" } = useParams();

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

  const resultVideo =
    files?.videos.length
      ? [...files.videos].sort((a, b) => b.size_bytes - a.size_bytes)[0]
      : null;

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
          <StageProgress
            progress={job.progress}
            label={job.stage_label}
            stage={job.stage}
            status={job.status}
            variant="detail"
          />
        )}

        {job.error_message && (
          <div className="mb-6 rounded-xl bg-amber-50 px-4 py-3 text-amber-800">
            {job.error_message}
          </div>
        )}

        {job.status === "done" && resultVideo && (
          <section className="overflow-hidden rounded-xl border border-line bg-white shadow-sm">
            <div className="border-b border-line px-4 py-3">
              <h2 className="text-base font-semibold text-ink">Clip kết quả</h2>
              <p className="mt-0.5 text-xs text-ink-soft">
                Video đã xử lý xong, có thể xem trực tiếp hoặc tải về.
              </p>
            </div>
            <div className="p-4">
              <video
                controls
                className="aspect-video w-full rounded-lg bg-black"
                src={fileUrl(id, resultVideo.name)}
              />
              <div className="mt-3 flex items-center justify-between gap-3">
                <p className="truncate text-sm text-ink-soft" title={resultVideo.name}>
                  {resultVideo.name}
                </p>
                <a href={fileUrl(id, resultVideo.name)} download className="btn-primary shrink-0">
                  Tải video ({(resultVideo.size_bytes / 1024 / 1024).toFixed(1)} MB)
                </a>
              </div>
            </div>
          </section>
        )}

        {job.status === "done" && files && !resultVideo && (
          <div className="card text-ink-soft">Chưa tìm thấy clip kết quả.</div>
        )}
      </main>
    </div>
  );
}
