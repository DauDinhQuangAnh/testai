import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import NavBar from "../components/NavBar";
import Spinner from "../components/Spinner";
import StageProgress from "../components/StageProgress";
import { api, ApiError, fileUrl } from "../lib/api";
import { STATUS_LABELS } from "../lib/constants";
import type { JobFilesOut, JobOut } from "../lib/types";

type SaveFileHandle = {
  createWritable: () => Promise<{
    write: (data: Blob) => Promise<void>;
    close: () => Promise<void>;
  }>;
};

declare global {
  interface Window {
    showSaveFilePicker?: (options?: {
      suggestedName?: string;
      types?: Array<{ description: string; accept: Record<string, string[]> }>;
    }) => Promise<SaveFileHandle>;
  }
}

export default function JobDetail() {
  const { id = "" } = useParams();
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [emailMessage, setEmailMessage] = useState<string | null>(null);

  const sendEmail = useMutation({
    mutationFn: () => api.post<{ sent_to: string }>(`/api/jobs/${id}/send-email`, {}),
    onSuccess: (result) => setEmailMessage(`Đã gửi link tới ${result.sent_to}.`),
    onError: (err) =>
      setEmailMessage(err instanceof ApiError ? err.message : "Gửi email thất bại."),
  });

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
        <main className="mx-auto flex max-w-4xl items-center gap-2 px-4 py-8 text-ink-soft">
          <Spinner /> Đang tải...
        </main>
      </div>
    );
  }

  const resultVideo =
    files?.videos.length
      ? [...files.videos].sort((a, b) => b.size_bytes - a.size_bytes)[0]
      : null;

  async function saveVideoAs(name: string) {
    if (!window.showSaveFilePicker) {
      setSaveMessage("Trình duyệt này chưa hỗ trợ chọn nơi lưu. Hãy dùng nút Tải video.");
      return;
    }

    setIsSaving(true);
    setSaveMessage(null);
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: name,
        types: [
          {
            description: "Video",
            accept: { "video/mp4": [".mp4"], "video/x-matroska": [".mkv"] },
          },
        ],
      });
      const response = await fetch(fileUrl(id, name));
      if (!response.ok) throw new Error("Không tải được file kết quả.");
      const writable = await handle.createWritable();
      await writable.write(await response.blob());
      await writable.close();
      setSaveMessage("Đã lưu video vào vị trí bạn chọn.");
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setSaveMessage(err instanceof Error ? err.message : "Không lưu được video.");
    } finally {
      setIsSaving(false);
    }
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
                <div className="flex shrink-0 flex-wrap justify-end gap-2">
                  <Link to={`/studio/jobs/${id}/edit`} className="btn-ghost">
                    Sửa phụ đề
                  </Link>
                  <button
                    type="button"
                    className="btn-ghost"
                    disabled={sendEmail.isPending}
                    onClick={() => sendEmail.mutate()}
                  >
                    {sendEmail.isPending && <Spinner className="h-3 w-3" />}
                    {sendEmail.isPending ? "Đang gửi..." : "Gửi về email"}
                  </button>
                  <button
                    type="button"
                    className="btn-ghost"
                    disabled={isSaving}
                    onClick={() => saveVideoAs(resultVideo.name)}
                  >
                    {isSaving && <Spinner className="h-3 w-3" />}
                    {isSaving ? "Đang lưu..." : "Chọn nơi lưu"}
                  </button>
                  <a href={fileUrl(id, resultVideo.name)} download className="btn-primary">
                    Tải video ({(resultVideo.size_bytes / 1024 / 1024).toFixed(1)} MB)
                  </a>
                </div>
              </div>
              {saveMessage && <p className="mt-2 text-sm text-ink-soft">{saveMessage}</p>}
              {emailMessage && <p className="mt-2 text-sm text-ink-soft">{emailMessage}</p>}
            </div>
          </section>
        )}

        {job.status === "done" && files && !resultVideo && (
          <div className="card flex items-center justify-between gap-3 text-ink-soft">
            Chưa tìm thấy clip kết quả.
            <Link to={`/studio/jobs/${id}/edit`} className="btn-ghost shrink-0">
              Sửa phụ đề
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}
