import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import NavBar from "../components/NavBar";
import Spinner from "../components/Spinner";
import { api, ApiError, fileUrl, originalUrl } from "../lib/api";
import { languageName } from "../lib/constants";
import type { CustomVoiceOut, JobFilesOut, JobOut, SubtitleSegment, VoiceInfo } from "../lib/types";

type Tab = "edit" | "translate" | "dub";

const TABS: { key: Tab; label: string }[] = [
  { key: "edit", label: "Chỉnh sửa phụ đề" },
  { key: "translate", label: "Dịch phụ đề" },
  { key: "dub", label: "Lồng tiếng lại" },
];

function emptySegment(): SubtitleSegment {
  return { start: 0, end: 0, text: "", speaker: null };
}

export default function Editor() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("edit");
  const [language, setLanguage] = useState<string | null>(null);
  const [rows, setRows] = useState<SubtitleSegment[]>([]);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [translateLanguage, setTranslateLanguage] = useState("en");
  const [translateMessage, setTranslateMessage] = useState<string | null>(null);
  const [dubLanguage, setDubLanguage] = useState("vi");
  const [dubVoice, setDubVoice] = useState<string | null>(null);
  const [dubCustomVoiceId, setDubCustomVoiceId] = useState<string | null>(null);
  const [dubKeepOriginal, setDubKeepOriginal] = useState(false);
  const [dubMessage, setDubMessage] = useState<string | null>(null);

  const { data: job } = useQuery({
    queryKey: ["job", id],
    queryFn: () => api.get<JobOut>(`/api/jobs/${id}`),
  });

  const { data: files } = useQuery({
    queryKey: ["job-files", id],
    queryFn: () => api.get<JobFilesOut>(`/api/jobs/${id}/files`),
    enabled: job?.status === "done",
  });

  const { data: languages } = useQuery({
    queryKey: ["languages"],
    queryFn: () => api.get<{ targets: string[]; sources: string[] }>("/api/meta/languages"),
  });

  const { data: dubVoices = [] } = useQuery({
    queryKey: ["voices", dubLanguage],
    queryFn: () => api.get<VoiceInfo[]>(`/api/meta/voices/${dubLanguage}`),
    enabled: tab === "dub",
  });
  const { data: customVoices = [] } = useQuery({
    queryKey: ["custom-voices"],
    queryFn: () => api.get<CustomVoiceOut[]>("/api/voices"),
    enabled: tab === "dub",
  });

  useEffect(() => {
    if (language === null && files?.subtitles.length) setLanguage(files.subtitles[0].language);
  }, [files, language]);

  const {
    data: segments,
    isLoading: segmentsLoading,
    isError: segmentsError,
  } = useQuery({
    queryKey: ["subtitles", id, language],
    queryFn: () => api.get<SubtitleSegment[]>(`/api/jobs/${id}/subtitles/${language}`),
    enabled: Boolean(language),
  });

  useEffect(() => {
    if (segments) setRows(segments);
  }, [segments]);

  const saveSegments = useMutation({
    mutationFn: () => api.put(`/api/jobs/${id}/subtitles/${language}`, { segments: rows }),
    onSuccess: () => {
      setSaveMessage("Đã lưu và xuất lại file phụ đề.");
      queryClient.invalidateQueries({ queryKey: ["job-files", id] });
    },
    onError: (err) =>
      setSaveMessage(err instanceof ApiError ? err.message : "Lưu thất bại, thử lại."),
  });

  const translate = useMutation({
    mutationFn: () =>
      api.post(`/api/jobs/${id}/translate`, { target_language: translateLanguage }),
    onSuccess: () =>
      setTranslateMessage(
        `Đã gửi yêu cầu dịch sang '${languageName(translateLanguage)}'. Chạy ngầm vài phút, quay lại tab Chỉnh sửa phụ đề sau đó để xem.`
      ),
    onError: (err) =>
      setTranslateMessage(err instanceof ApiError ? err.message : "Gửi yêu cầu dịch thất bại."),
  });

  const dub = useMutation({
    mutationFn: () =>
      api.post(`/api/jobs/${id}/dub`, {
        target_language: dubLanguage,
        voice: dubVoice,
        keep_original_audio: dubKeepOriginal,
        custom_voice_id: dubCustomVoiceId,
      }),
    onSuccess: () =>
      setDubMessage(
        "Đã gửi yêu cầu dịch + lồng tiếng (chạy ngầm, có thể mất vài phút). Video kết quả sẽ xuất hiện trong Studio."
      ),
    onError: (err) =>
      setDubMessage(err instanceof ApiError ? err.message : "Gửi yêu cầu lồng tiếng thất bại."),
  });

  function updateRow(index: number, patch: Partial<SubtitleSegment>) {
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  }

  function removeRow(index: number) {
    setRows((prev) => prev.filter((_, i) => i !== index));
  }

  if (!job) {
    return (
      <div className="min-h-screen">
        <NavBar />
        <main className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-8 text-ink-soft">
          <Spinner /> Đang tải...
        </main>
      </div>
    );
  }

  if (job.status !== "done") {
    return (
      <div className="min-h-screen">
        <NavBar />
        <main className="mx-auto max-w-5xl px-4 py-8">
          <div className="card text-ink-soft">
            Job này chưa xử lý xong, chưa thể sửa phụ đề.{" "}
            <Link to={`/studio/jobs/${id}`} className="text-primary hover:underline">
              Xem tiến độ
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const matchingVideo = files?.videos.find((v) => v.language === language);
  const videoSrc = matchingVideo ? fileUrl(id, matchingVideo.name) : originalUrl(id);

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Link to={`/studio/jobs/${id}`} className="text-sm text-ink-soft hover:text-primary">
          ← Quay lại chi tiết job
        </Link>
        <h1 className="mb-1 mt-2 break-all text-2xl font-bold">Sửa phụ đề: {job.filename}</h1>

        <div className="mb-6 mt-4 flex gap-2 border-b border-line">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium transition ${
                tab === t.key
                  ? "border-primary text-primary"
                  : "border-transparent text-ink-soft hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "edit" && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
            <div className="lg:col-span-2">
              <video controls className="aspect-video w-full rounded-lg bg-black" src={videoSrc} />
              {files && files.subtitles.length > 0 && (
                <div className="mt-4">
                  <label className="label">Ngôn ngữ phụ đề</label>
                  <select
                    className="input"
                    value={language ?? ""}
                    onChange={(e) => setLanguage(e.target.value)}
                  >
                    {files.subtitles.map((group) => (
                      <option key={group.language} value={group.language}>
                        {group.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div className="lg:col-span-3">
              {segmentsLoading && (
                <div className="flex items-center gap-2 text-ink-soft">
                  <Spinner /> Đang tải phụ đề...
                </div>
              )}
              {segmentsError && (
                <div className="card text-ink-soft">Không tìm thấy phụ đề cho ngôn ngữ này.</div>
              )}
              {!segmentsLoading && !segmentsError && files && files.subtitles.length === 0 && (
                <div className="card text-ink-soft">Job này chưa có phụ đề nào để sửa.</div>
              )}
              {!segmentsLoading && rows.length > 0 && (
                <>
                  <div className="max-h-[60vh] space-y-3 overflow-y-auto pr-1">
                    {rows.map((row, i) => (
                      <div key={i} className="card space-y-2">
                        <div className="flex gap-2">
                          <div className="flex-1">
                            <label className="label">Bắt đầu (s)</label>
                            <input
                              type="number"
                              step="0.01"
                              className="input"
                              value={row.start}
                              onChange={(e) => updateRow(i, { start: Number(e.target.value) })}
                            />
                          </div>
                          <div className="flex-1">
                            <label className="label">Kết thúc (s)</label>
                            <input
                              type="number"
                              step="0.01"
                              className="input"
                              value={row.end}
                              onChange={(e) => updateRow(i, { end: Number(e.target.value) })}
                            />
                          </div>
                          <div className="flex-1">
                            <label className="label">Người nói</label>
                            <input
                              type="text"
                              className="input"
                              value={row.speaker ?? ""}
                              onChange={(e) => updateRow(i, { speaker: e.target.value || null })}
                            />
                          </div>
                        </div>
                        <div>
                          <label className="label">Nội dung</label>
                          <textarea
                            className="input"
                            rows={2}
                            value={row.text}
                            onChange={(e) => updateRow(i, { text: e.target.value })}
                          />
                        </div>
                        <button
                          type="button"
                          className="text-sm text-red-600 hover:underline"
                          onClick={() => removeRow(i)}
                        >
                          Xóa dòng
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex items-center gap-3">
                    <button
                      type="button"
                      className="btn-ghost"
                      onClick={() => setRows((prev) => [...prev, emptySegment()])}
                    >
                      + Thêm dòng
                    </button>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={saveSegments.isPending}
                      onClick={() => saveSegments.mutate()}
                    >
                      {saveSegments.isPending && <Spinner className="h-3 w-3" />}
                      {saveSegments.isPending ? "Đang lưu..." : "Lưu và xuất lại file"}
                    </button>
                  </div>
                  {saveMessage && <p className="mt-2 text-sm text-ink-soft">{saveMessage}</p>}
                </>
              )}
            </div>
          </div>
        )}

        {tab === "translate" && (
          <div className="card max-w-lg space-y-4">
            <p className="text-sm text-ink-soft">
              Chỉ xuất phụ đề đã dịch (không tạo audio). File kết quả có hậu tố ngôn ngữ, ví dụ
              video.en.srt.
            </p>
            <div>
              <label className="label">Ngôn ngữ dịch</label>
              <select
                className="input"
                value={translateLanguage}
                onChange={(e) => setTranslateLanguage(e.target.value)}
              >
                {(languages?.targets ?? []).map((code) => (
                  <option key={code} value={code}>
                    {languageName(code)}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              className="btn-primary"
              disabled={translate.isPending}
              onClick={() => translate.mutate()}
            >
              {translate.isPending && <Spinner className="h-3 w-3" />}
              {translate.isPending ? "Đang gửi..." : "Dịch và xuất file mới"}
            </button>
            {translateMessage && <p className="text-sm text-ink-soft">{translateMessage}</p>}
          </div>
        )}

        {tab === "dub" && (
          <div className="card max-w-lg space-y-4">
            <p className="text-sm text-ink-soft">
              Tự động dịch (nếu chưa có) rồi lồng tiếng lại với ngôn ngữ/giọng/chế độ khác. Nếu
              video có nhiều người nói, giọng chọn bên dưới áp dụng cho người nói đầu tiên - các
              người nói khác tự động nhận giọng khác nhau.
            </p>
            <div>
              <label className="label">Ngôn ngữ lồng tiếng</label>
              <select
                className="input"
                value={dubLanguage}
                onChange={(e) => {
                  setDubLanguage(e.target.value);
                  setDubVoice(null);
                }}
              >
                {(languages?.targets ?? []).map((code) => (
                  <option key={code} value={code}>
                    {languageName(code)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Giọng đã clone (tuỳ chọn)</label>
              <select
                className="input"
                value={dubCustomVoiceId ?? ""}
                onChange={(e) => setDubCustomVoiceId(e.target.value || null)}
              >
                <option value="">Không dùng - chọn giọng có sẵn bên dưới</option>
                {customVoices.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
              {customVoices.length === 0 && (
                <p className="mt-1 text-xs text-ink-soft">
                  Chưa có giọng nào được clone - tạo ở trang{" "}
                  <Link to="/voices" className="underline">
                    Giọng của tôi
                  </Link>
                  .
                </p>
              )}
            </div>
            {!dubCustomVoiceId && (
              <div>
                <label className="label">Giọng đọc</label>
                <select
                  className="input"
                  value={dubVoice ?? ""}
                  onChange={(e) => setDubVoice(e.target.value || null)}
                >
                  <option value="">(Mặc định)</option>
                  {dubVoices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.label}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <label className="flex items-center gap-2 text-sm text-ink">
              <input
                type="checkbox"
                checked={dubKeepOriginal}
                onChange={(e) => setDubKeepOriginal(e.target.checked)}
              />
              Giữ tiếng gốc giảm 70% + tiếng dịch lên trên (kiểu thuyết minh)
            </label>
            <button
              type="button"
              className="btn-primary"
              disabled={dub.isPending}
              onClick={() => dub.mutate()}
            >
              {dub.isPending && <Spinner className="h-3 w-3" />}
              {dub.isPending ? "Đang gửi..." : "Dịch + Lồng tiếng"}
            </button>
            {dubMessage && <p className="text-sm text-ink-soft">{dubMessage}</p>}
          </div>
        )}
      </main>
    </div>
  );
}
