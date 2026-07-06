import { useMutation, useQuery } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import NavBar from "../components/NavBar";
import { api } from "../lib/api";
import {
  FONT_CHOICES,
  languageName,
  RENDER_QUALITY_CHOICES,
  TRANSLATE_PRESETS,
  TRIM_CHOICES,
} from "../lib/constants";
import {
  defaultOptions,
  type JobOptions,
  type JobOut,
  type VideoMetadata,
  type VoiceInfo,
} from "../lib/types";

const STEPS = [
  { key: "source", title: "Nguồn", desc: "Video và ngôn ngữ" },
  { key: "voice", title: "Giọng đọc", desc: "Âm thanh và người nói" },
  { key: "translate", title: "Dịch", desc: "Giọng điệu và ngữ cảnh" },
  { key: "subtitle", title: "Phụ đề", desc: "Kiểu dáng và mật độ" },
  { key: "audio", title: "Âm thanh & Xuất", desc: "Phối âm và định dạng" },
  { key: "review", title: "Xem lại", desc: "Cấu hình đã xác nhận" },
];

type SourceMode = "upload" | "download";

function formatDuration(seconds?: number | null): string {
  if (!seconds) return "";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

export default function NewJob() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [options, setOptions] = useState<JobOptions>(defaultOptions());
  const [file, setFile] = useState<File | null>(null);
  const [sourceMode, setSourceMode] = useState<SourceMode>("upload");
  const [videoUrl, setVideoUrl] = useState("");
  const [videoMetadata, setVideoMetadata] = useState<VideoMetadata | null>(null);
  const [selectedQuality, setSelectedQuality] = useState("best");
  const [presetIndex, setPresetIndex] = useState(0);
  const [sampleUrl, setSampleUrl] = useState<string | null>(null);
  const [draggingSubtitle, setDraggingSubtitle] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  const previewRef = useRef<HTMLDivElement>(null);

  const moveSubtitleTo = (clientX: number, clientY: number) => {
    const rect = previewRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = Math.min(100, Math.max(0, ((clientX - rect.left) / rect.width) * 100));
    const y = Math.min(100, Math.max(0, ((clientY - rect.top) / rect.height) * 100));
    setOptions((o) => ({
      ...o,
      subtitle: { ...o.subtitle, style: { ...o.subtitle.style, position_x: x, position_y: y } },
    }));
  };

  const patch = (updates: Partial<JobOptions>) => setOptions((o) => ({ ...o, ...updates }));

  const { data: languages } = useQuery({
    queryKey: ["languages"],
    queryFn: () => api.get<{ targets: string[]; sources: string[] }>("/api/meta/languages"),
  });
  const { data: voices = [] } = useQuery({
    queryKey: ["voices", options.dubbing.target_language],
    queryFn: () => api.get<VoiceInfo[]>(`/api/meta/voices/${options.dubbing.target_language}`),
  });

  const previewVoice = useMutation({
    mutationFn: async () => {
      const blob = (await api.post<Blob>("/api/meta/voice-sample", {
        language: options.dubbing.target_language,
        voice: options.dubbing.voice ?? voices[0]?.id,
        rate_percent: options.dubbing.rate_percent,
        pitch_hz: options.dubbing.pitch_hz,
      })) as Blob;
      return URL.createObjectURL(blob);
    },
    onSuccess: (url) => {
      setSampleUrl(url);
      setTimeout(() => audioRef.current?.play(), 50);
    },
  });

  const analyzeSource = useMutation({
    mutationFn: async () => {
      const submittedUrl = videoUrl.trim();
      if (!submittedUrl) throw new Error("Hãy dán link YouTube/Douyin trước.");
      return api.post<VideoMetadata>("/api/jobs/source/analyze", { url: submittedUrl });
    },
    onSuccess: (metadata) => {
      setVideoMetadata(metadata);
      setVideoUrl(metadata.url);
      setSelectedQuality(metadata.qualities[0]?.id ?? "best");
    },
  });

  const createJob = useMutation({
    mutationFn: async () => {
      const optionsToSubmit: JobOptions = {
        ...options,
        source: {
          ...options.source,
          input_mode: sourceMode,
          download:
            sourceMode === "download"
              ? {
                  url: videoMetadata?.url ?? videoUrl.trim(),
                  quality: selectedQuality,
                  title: videoMetadata?.title,
                }
              : undefined,
        },
      };
      const form = new FormData();
      form.append("options", JSON.stringify(optionsToSubmit));
      if (sourceMode === "upload" && file) form.append("file", file);
      return api.postForm<JobOut>("/api/jobs", form);
    },
    onSuccess: (job) => navigate(`/studio/jobs/${job.id}`),
  });

  const sourceValid =
    sourceMode === "upload" ? Boolean(file) : Boolean(videoMetadata && selectedQuality);
  const sourceName =
    sourceMode === "upload"
      ? (file?.name ?? "(chưa chọn file)")
      : (videoMetadata?.title ?? "(chưa phân tích link)");
  const selectedVoice =
    voices.find((v) => v.id === options.dubbing.voice) ?? voices[0] ?? null;

  const resetCurrentStep = () => {
    const defaults = defaultOptions();
    const key = STEPS[step].key;

    if (key === "source") {
      patch({ source: defaults.source });
      setFile(null);
      setSourceMode("upload");
      setVideoUrl("");
      setVideoMetadata(null);
      setSelectedQuality("best");
      return;
    }
    if (key === "voice") {
      patch({ dubbing: defaults.dubbing });
      setSampleUrl(null);
      return;
    }
    if (key === "translate") {
      patch({ translation: defaults.translation });
      setPresetIndex(0);
      return;
    }
    if (key === "subtitle") {
      patch({ subtitle: defaults.subtitle });
      return;
    }
    if (key === "audio") {
      patch({ audio: defaults.audio, output: defaults.output });
      return;
    }

    setOptions(defaults);
    setFile(null);
    setSourceMode("upload");
    setVideoUrl("");
    setVideoMetadata(null);
    setSelectedQuality("best");
    setPresetIndex(0);
    setSampleUrl(null);
  };

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-primary">
              Tạo video · Bước {step + 1} / {STEPS.length}
            </p>
            <h1 className="text-2xl font-bold">Quick Video</h1>
          </div>
          <Link to="/studio" className="btn-ghost">
            Hủy
          </Link>
        </div>

        <div className="flex flex-col gap-6 lg:flex-row">
          {/* Stepper sidebar */}
          <aside className="lg:w-60">
            <ol className="flex gap-2 overflow-x-auto lg:flex-col">
              {STEPS.map((s, i) => (
                <li key={s.key}>
                  <button
                    onClick={() => setStep(i)}
                    className={
                      "w-full rounded-xl border px-4 py-3 text-left transition " +
                      (i === step
                        ? "border-primary bg-primary-soft"
                        : "border-line bg-white hover:border-primary/40")
                    }
                  >
                    <span
                      className={
                        "mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold " +
                        (i < step
                          ? "bg-green-500 text-white"
                          : i === step
                            ? "bg-primary text-white"
                            : "bg-cream-dark text-ink-soft")
                      }
                    >
                      {i < step ? "✓" : i + 1}
                    </span>
                    <span className="font-medium">{s.title}</span>
                    <p className="ml-8 text-xs text-ink-soft">{s.desc}</p>
                  </button>
                </li>
              ))}
            </ol>
          </aside>

          {/* Step content */}
          <section className="min-w-0 flex-1">
            <div className="card">
              <div className="mb-5 flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-primary">
                    Bước {step + 1}
                  </p>
                  <p className="text-sm text-ink-soft">{STEPS[step].desc}</p>
                </div>
                <button type="button" className="btn-ghost self-start" onClick={resetCurrentStep}>
                  {step === STEPS.length - 1 ? "Đặt lại tất cả" : "Đặt lại bước này"}
                </button>
              </div>

              {step === 0 && (
                <div className="space-y-5">
                  <h2 className="text-lg font-semibold">Chọn nguồn video</h2>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {(["upload", "download"] as SourceMode[]).map((mode) => (
                      <button
                        key={mode}
                        type="button"
                        className={
                          "rounded-lg border px-4 py-3 text-left transition " +
                          (sourceMode === mode
                            ? "border-primary bg-primary-soft"
                            : "border-line bg-white hover:border-primary/40")
                        }
                        onClick={() => setSourceMode(mode)}
                      >
                        <span className="font-semibold">
                          {mode === "upload" ? "Insert video" : "Tải từ link"}
                        </span>
                        <p className="mt-1 text-xs text-ink-soft">
                          {mode === "upload"
                            ? "Chọn file có sẵn trên máy."
                            : "YouTube, Douyin hoặc link yt-dlp hỗ trợ."}
                        </p>
                      </button>
                    ))}
                  </div>

                  {sourceMode === "upload" && (
                    <div>
                      <label className="label">File video/audio (tối đa 500MB)</label>
                      <input
                        type="file"
                        accept=".mp4,.mkv,.mov,.wav,.mp3,.m4a"
                        className="input"
                        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                      />
                      {file && (
                        <p className="mt-2 text-sm text-ink-soft">
                          {file.name} · {(file.size / 1024 / 1024).toFixed(1)} MB
                        </p>
                      )}
                    </div>
                  )}

                  {sourceMode === "download" && (
                    <div className="space-y-4">
                      <div>
                        <label className="label">Link video</label>
                        <div className="flex flex-col gap-2 sm:flex-row">
                          <input
                            type="url"
                            className="input"
                            value={videoUrl}
                            placeholder="https://www.youtube.com/watch?v=..."
                            onChange={(e) => {
                              setVideoUrl(e.target.value);
                              setVideoMetadata(null);
                            }}
                          />
                          <button
                            type="button"
                            className="btn-ghost justify-center sm:w-36"
                            disabled={analyzeSource.isPending}
                            onClick={() => analyzeSource.mutate()}
                          >
                            {analyzeSource.isPending ? "Đang đọc..." : "Phân tích"}
                          </button>
                        </div>
                        <p className="mt-1 text-xs text-ink-soft">
                          Video tải về chỉ lưu tạm trong thư mục job, xử lý xong sẽ tự xóa nguồn.
                        </p>
                      </div>

                      {analyzeSource.isError && (
                        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                          {analyzeSource.error instanceof Error
                            ? analyzeSource.error.message
                            : "Không phân tích được link video"}
                        </p>
                      )}

                      {videoMetadata && (
                        <div className="grid gap-4 rounded-lg border border-line bg-cream p-4 sm:grid-cols-[160px_1fr]">
                          {videoMetadata.thumbnail ? (
                            <img
                              src={videoMetadata.thumbnail}
                              alt=""
                              className="aspect-video w-full rounded-md object-cover"
                            />
                          ) : (
                            <div className="aspect-video rounded-md bg-cream-dark" />
                          )}
                          <div className="min-w-0 space-y-3">
                            <div>
                              <p className="break-words font-semibold">{videoMetadata.title}</p>
                              <p className="text-xs text-ink-soft">
                                {[videoMetadata.uploader, videoMetadata.source, formatDuration(videoMetadata.duration)]
                                  .filter(Boolean)
                                  .join(" · ")}
                              </p>
                            </div>
                            <div>
                              <label className="label">Chất lượng tải</label>
                              <select
                                className="input"
                                value={selectedQuality}
                                onChange={(e) => setSelectedQuality(e.target.value)}
                              >
                                {videoMetadata.qualities.map((q) => (
                                  <option key={q.id} value={q.id}>
                                    {q.label}
                                  </option>
                                ))}
                              </select>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="label">Kiểm thử (chạy thử đoạn ngắn)</label>
                      <select
                        className="input"
                        value={String(options.source.trim_seconds)}
                        onChange={(e) =>
                          patch({
                            source: {
                              ...options.source,
                              trim_seconds:
                                e.target.value === "null" ? null : Number(e.target.value),
                            },
                          })
                        }
                      >
                        {TRIM_CHOICES.map((t) => (
                          <option key={String(t.value)} value={String(t.value)}>
                            {t.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="label">Ngôn ngữ nguồn</label>
                      <select
                        className="input"
                        value={options.source.source_language ?? "auto"}
                        onChange={(e) =>
                          patch({
                            source: {
                              ...options.source,
                              source_language: e.target.value === "auto" ? null : e.target.value,
                            },
                          })
                        }
                      >
                        <option value="auto">Tự phát hiện (khuyên dùng)</option>
                        {languages?.sources.map((l) => (
                          <option key={l} value={l}>
                            {languageName(l)}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {step === 1 && (
                <div className="space-y-5">
                  <h2 className="text-lg font-semibold">Giọng đọc và cách diễn đạt</h2>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      className="h-5 w-5 accent-primary"
                      checked={options.dubbing.enabled}
                      onChange={(e) =>
                        patch({ dubbing: { ...options.dubbing, enabled: e.target.checked } })
                      }
                    />
                    <span>Lồng tiếng tự động sau khi tạo phụ đề</span>
                  </label>

                  {options.dubbing.enabled && (
                    <>
                      <div>
                        <label className="label">Ngôn ngữ lồng tiếng</label>
                        <select
                          className="input"
                          value={options.dubbing.target_language}
                          onChange={(e) =>
                            patch({
                              dubbing: {
                                ...options.dubbing,
                                target_language: e.target.value,
                                voice: null,
                              },
                            })
                          }
                        >
                          {languages?.targets.map((l) => (
                            <option key={l} value={l}>
                              {languageName(l)}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="label">Giọng đọc</label>
                        <div className="grid max-h-64 gap-2 overflow-y-auto sm:grid-cols-2">
                          {voices.map((v) => (
                            <button
                              key={v.id}
                              onClick={() =>
                                patch({ dubbing: { ...options.dubbing, voice: v.id } })
                              }
                              className={
                                "rounded-lg border px-3 py-2 text-left text-sm transition " +
                                ((options.dubbing.voice ?? voices[0]?.id) === v.id
                                  ? "border-primary bg-primary-soft"
                                  : "border-line bg-white hover:border-primary/40")
                              }
                            >
                              <span className="font-medium">
                                {v.recommended && "⭐ "}
                                {v.label}
                              </span>
                              <p className="text-xs text-ink-soft">{v.style}</p>
                            </button>
                          ))}
                        </div>
                        <p className="mt-1 text-xs text-ink-soft">
                          ⭐ = giọng bản địa. Video nhiều người nói sẽ tự gán thêm giọng khác nhau.
                        </p>
                      </div>

                      <div className="grid gap-4 sm:grid-cols-2">
                        <div>
                          <label className="label">
                            Tốc độ nói: {options.dubbing.rate_percent > 0 ? "+" : ""}
                            {options.dubbing.rate_percent}%
                          </label>
                          <input
                            type="range"
                            min={-50}
                            max={50}
                            value={options.dubbing.rate_percent}
                            className="w-full accent-primary"
                            onChange={(e) =>
                              patch({
                                dubbing: {
                                  ...options.dubbing,
                                  rate_percent: Number(e.target.value),
                                },
                              })
                            }
                          />
                        </div>
                        <div>
                          <label className="label">
                            Cao độ: {options.dubbing.pitch_hz > 0 ? "+" : ""}
                            {options.dubbing.pitch_hz}Hz
                          </label>
                          <input
                            type="range"
                            min={-20}
                            max={20}
                            value={options.dubbing.pitch_hz}
                            className="w-full accent-primary"
                            onChange={(e) =>
                              patch({
                                dubbing: { ...options.dubbing, pitch_hz: Number(e.target.value) },
                              })
                            }
                          />
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <button
                          className="btn-ghost"
                          onClick={() => previewVoice.mutate()}
                          disabled={previewVoice.isPending}
                        >
                          {previewVoice.isPending ? "Đang tạo mẫu..." : "▶ Nghe thử giọng này"}
                        </button>
                        {sampleUrl && <audio ref={audioRef} controls src={sampleUrl} />}
                      </div>
                      {previewVoice.isError && (
                        <p className="text-sm text-red-600">
                          Không tạo được mẫu giọng (cần internet).
                        </p>
                      )}
                    </>
                  )}
                </div>
              )}

              {step === 2 && (
                <div className="space-y-5">
                  <h2 className="text-lg font-semibold">Mục đích dịch</h2>
                  <p className="rounded-lg bg-cream px-4 py-2 text-sm text-ink-soft">
                    {options.dubbing.enabled ? (
                      <>
                        Đang dịch/lồng tiếng sang{" "}
                        <strong>{languageName(options.dubbing.target_language)}</strong> — đổi
                        ngôn ngữ ở{" "}
                        <button
                          type="button"
                          className="underline"
                          onClick={() => setStep(1)}
                        >
                          Bước 2 · Giọng đọc
                        </button>
                        .
                      </>
                    ) : (
                      <>
                        Lồng tiếng đang <strong>tắt</strong> (Bước 2) nên bước này sẽ không có
                        tác dụng — chỉ phụ đề gốc được xuất ra.
                      </>
                    )}
                  </p>
                  <div>
                    <label className="label">Kiểu trình bày bản dịch</label>
                    <div className="flex flex-wrap gap-2">
                      {TRANSLATE_PRESETS.map((p, i) => (
                        <button
                          key={p.label}
                          onClick={() => {
                            setPresetIndex(i);
                            patch({
                              translation: {
                                ...options.translation,
                                max_chars_per_line: p.maxChars,
                                max_lines: p.maxLines,
                              },
                            });
                          }}
                          className={presetIndex === i ? "btn-primary" : "btn-ghost"}
                        >
                          {p.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="label">Bảng thuật ngữ (mỗi dòng: nguồn = đích)</label>
                    <textarea
                      className="input h-32 font-mono text-sm"
                      placeholder={"CPU = CPU\nSQL Server = SQL Server\nmachine learning = học máy"}
                      value={options.translation.glossary}
                      onChange={(e) =>
                        patch({
                          translation: { ...options.translation, glossary: e.target.value },
                        })
                      }
                    />
                    <p className="mt-1 text-xs text-ink-soft">
                      Ép giữ đúng thuật ngữ khi dịch. Dịch theo ngữ cảnh sâu (LLM) sẽ bổ sung sau
                      — engine hiện tại là NLLB chạy local.
                    </p>
                  </div>
                  <div>
                    <label className="label">
                      Bảng phát âm cho giọng lồng tiếng (mỗi dòng: từ = cách đọc)
                    </label>
                    <textarea
                      className="input h-24 font-mono text-sm"
                      placeholder={"SQL = ét quy eo\nAPI = ây pi ai"}
                      value={options.translation.pronunciation}
                      onChange={(e) =>
                        patch({
                          translation: { ...options.translation, pronunciation: e.target.value },
                        })
                      }
                    />
                    <p className="mt-1 text-xs text-ink-soft">
                      Chỉ đổi cách <strong>giọng đọc phát âm</strong> khi lồng tiếng — phụ đề vẫn
                      hiển thị nguyên chữ gốc. Ghi đè lên bộ quy tắc mặc định của hệ thống (vd.
                      SQL → "ét quy eo") nếu trùng từ.
                    </p>
                  </div>
                </div>
              )}

              {step === 3 && (
                <div className="space-y-5">
                  <h2 className="text-lg font-semibold">Kiểu dáng phụ đề</h2>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      className="h-5 w-5 accent-primary"
                      checked={options.subtitle.burn_in}
                      onChange={(e) =>
                        patch({ subtitle: { ...options.subtitle, burn_in: e.target.checked } })
                      }
                    />
                    <span>
                      Gắn phụ đề vào video (hardsub){" "}
                      <span className="text-sm text-ink-soft">— render lâu hơn</span>
                    </span>
                  </label>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="label">Phông chữ</label>
                      <select
                        className="input"
                        value={options.subtitle.style.font}
                        onChange={(e) =>
                          patch({
                            subtitle: {
                              ...options.subtitle,
                              style: { ...options.subtitle.style, font: e.target.value },
                            },
                          })
                        }
                      >
                        {FONT_CHOICES.map((f) => (
                          <option key={f}>{f}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="label">Cỡ chữ: {options.subtitle.style.font_size}px</label>
                      <input
                        type="range"
                        min={24}
                        max={96}
                        value={options.subtitle.style.font_size}
                        className="w-full accent-primary"
                        onChange={(e) =>
                          patch({
                            subtitle: {
                              ...options.subtitle,
                              style: {
                                ...options.subtitle.style,
                                font_size: Number(e.target.value),
                              },
                            },
                          })
                        }
                      />
                    </div>
                    <div>
                      <label className="label">Màu chữ</label>
                      <input
                        type="color"
                        className="h-10 w-full cursor-pointer rounded-lg border border-line"
                        value={options.subtitle.style.text_color}
                        onChange={(e) =>
                          patch({
                            subtitle: {
                              ...options.subtitle,
                              style: { ...options.subtitle.style, text_color: e.target.value },
                            },
                          })
                        }
                      />
                    </div>
                    <div>
                      <label className="label">Màu nền</label>
                      <input
                        type="color"
                        className="h-10 w-full cursor-pointer rounded-lg border border-line"
                        value={options.subtitle.style.background_color}
                        onChange={(e) =>
                          patch({
                            subtitle: {
                              ...options.subtitle,
                              style: {
                                ...options.subtitle.style,
                                background_color: e.target.value,
                              },
                            },
                          })
                        }
                      />
                    </div>
                    <label className="flex items-center gap-3 self-end pb-2">
                      <input
                        type="checkbox"
                        className="h-5 w-5 accent-primary"
                        checked={options.subtitle.style.opaque_box}
                        onChange={(e) =>
                          patch({
                            subtitle: {
                              ...options.subtitle,
                              style: { ...options.subtitle.style, opaque_box: e.target.checked },
                            },
                          })
                        }
                      />
                      <span>Hộp nền đặc sau chữ</span>
                    </label>
                  </div>

                  {/* Preview */}
                  <div>
                    <p className="mb-2 text-xs text-ink-soft">
                      Kéo phụ đề bên dưới để đặt vào bất kỳ vị trí nào trên khung hình.
                    </p>
                    <div
                      ref={previewRef}
                      className="relative aspect-video w-full touch-none select-none overflow-hidden rounded-xl bg-gradient-to-br from-gray-700 to-gray-900"
                      onPointerMove={(e) => {
                        if (draggingSubtitle) moveSubtitleTo(e.clientX, e.clientY);
                      }}
                      onPointerUp={() => setDraggingSubtitle(false)}
                      onPointerLeave={() => setDraggingSubtitle(false)}
                    >
                      <span
                        onPointerDown={(e) => {
                          e.currentTarget.setPointerCapture(e.pointerId);
                          setDraggingSubtitle(true);
                          moveSubtitleTo(e.clientX, e.clientY);
                        }}
                        className="absolute cursor-grab whitespace-nowrap active:cursor-grabbing"
                        style={{
                          left: `${options.subtitle.style.position_x}%`,
                          top: `${options.subtitle.style.position_y}%`,
                          transform: "translate(-50%, -50%)",
                          fontFamily: options.subtitle.style.font,
                          fontSize: Math.max(14, options.subtitle.style.font_size / 2.5),
                          color: options.subtitle.style.text_color,
                          textShadow: "0 0 2px #000, 0 0 4px #000",
                          background: options.subtitle.style.opaque_box
                            ? options.subtitle.style.background_color
                            : "transparent",
                          padding: options.subtitle.style.opaque_box ? "4px 12px" : 0,
                          borderRadius: 4,
                        }}
                      >
                        Bản dịch giữ đúng ngữ cảnh và vừa khung hình.
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {step === 4 && (
                <div className="grid gap-6 sm:grid-cols-2">
                  <div className="space-y-5">
                    <h2 className="text-lg font-semibold">Phối âm</h2>
                    <div>
                      <label className="label">
                        Âm lượng âm gốc: {Math.round(options.audio.original_volume * 100)}%
                      </label>
                      <input
                        type="range"
                        min={0}
                        max={100}
                        value={Math.round(options.audio.original_volume * 100)}
                        className="w-full accent-primary"
                        onChange={(e) =>
                          patch({
                            audio: {
                              ...options.audio,
                              original_volume: Number(e.target.value) / 100,
                              ducking:
                                Number(e.target.value) === 0 ? false : options.audio.ducking,
                            },
                          })
                        }
                      />
                      <p className="text-xs text-ink-soft">
                        0% = xóa hẳn tiếng gốc · &gt;0% = giữ nhạc nền (kiểu thuyết minh)
                      </p>
                    </div>
                    <div>
                      <label className="label">
                        Âm lượng giọng lồng tiếng: {Math.round(options.audio.dub_volume * 100)}%
                      </label>
                      <input
                        type="range"
                        min={50}
                        max={150}
                        value={Math.round(options.audio.dub_volume * 100)}
                        className="w-full accent-primary"
                        onChange={(e) =>
                          patch({
                            audio: { ...options.audio, dub_volume: Number(e.target.value) / 100 },
                          })
                        }
                      />
                    </div>
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        className="h-5 w-5 accent-primary"
                        disabled={options.audio.original_volume === 0}
                        checked={options.audio.ducking}
                        onChange={(e) =>
                          patch({ audio: { ...options.audio, ducking: e.target.checked } })
                        }
                      />
                      <span>
                        Giảm âm gốc khi có lời thoại{" "}
                        <span className="text-sm text-ink-soft">(sidechain ducking)</span>
                      </span>
                    </label>
                  </div>
                  <div className="space-y-5">
                    <h2 className="text-lg font-semibold">Đầu ra</h2>
                    <div>
                      <label className="label">Định dạng</label>
                      <select
                        className="input"
                        value={options.output.format}
                        onChange={(e) =>
                          patch({
                            output: {
                              ...options.output,
                              format: e.target.value as "mp4" | "mkv",
                            },
                          })
                        }
                      >
                        <option value="mp4">MP4</option>
                        <option value="mkv">MKV</option>
                      </select>
                    </div>
                    <div>
                      <label className="label">Chất lượng dựng (khi hardsub)</label>
                      <select
                        className="input"
                        value={options.output.quality}
                        onChange={(e) =>
                          patch({
                            output: {
                              ...options.output,
                              quality: e.target.value as "fast" | "balanced" | "high",
                            },
                          })
                        }
                      >
                        {RENDER_QUALITY_CHOICES.map((q) => (
                          <option key={q.value} value={q.value}>
                            {q.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {step === 5 && (
                <div className="space-y-4">
                  <h2 className="text-lg font-semibold">Xem lại cấu hình đã xác nhận</h2>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <ReviewCard title="NGUỒN">
                      <p className="break-all font-medium">
                        {sourceName}
                      </p>
                      <p className="text-xs text-ink-soft">
                        {sourceMode === "download"
                          ? `Tải từ link · ${selectedQuality}`
                          : "Insert video"}{" "}
                        ·{" "}
                        {options.source.source_language
                          ? languageName(options.source.source_language)
                          : "Tự phát hiện"}{" "}
                        →{" "}
                        {options.dubbing.enabled
                          ? languageName(options.dubbing.target_language)
                          : "chỉ phụ đề"}
                        {options.source.trim_seconds
                          ? ` · ${options.source.trim_seconds}s đầu`
                          : " · toàn bộ video"}
                      </p>
                    </ReviewCard>
                    <ReviewCard title="GIỌNG ĐỌC">
                      <p className="font-medium">
                        {options.dubbing.enabled
                          ? (selectedVoice?.label ?? "mặc định")
                          : "(tắt lồng tiếng)"}
                      </p>
                      <p className="text-xs text-ink-soft">
                        Tốc độ {options.dubbing.rate_percent >= 0 ? "+" : ""}
                        {options.dubbing.rate_percent}% · Cao độ{" "}
                        {options.dubbing.pitch_hz >= 0 ? "+" : ""}
                        {options.dubbing.pitch_hz}Hz
                      </p>
                    </ReviewCard>
                    <ReviewCard title="DỊCH">
                      <p className="font-medium">{TRANSLATE_PRESETS[presetIndex].label}</p>
                      <p className="text-xs text-ink-soft">
                        Bảng thuật ngữ:{" "}
                        {
                          options.translation.glossary
                            .split("\n")
                            .filter((l) => l.includes("=")).length
                        }{" "}
                        mục · Bảng phát âm riêng:{" "}
                        {
                          options.translation.pronunciation
                            .split("\n")
                            .filter((l) => l.includes("=")).length
                        }{" "}
                        mục
                      </p>
                    </ReviewCard>
                    <ReviewCard title="PHỤ ĐỀ">
                      <p className="font-medium">
                        {options.subtitle.burn_in ? "Gắn cứng vào video" : "Xuất file rời"}
                      </p>
                      <p className="text-xs text-ink-soft">
                        {options.subtitle.style.font} {options.subtitle.style.font_size}px · vị
                        trí ({Math.round(options.subtitle.style.position_x)}%,{" "}
                        {Math.round(options.subtitle.style.position_y)}%)
                      </p>
                    </ReviewCard>
                    <ReviewCard title="ÂM THANH & ĐẦU RA">
                      <p className="font-medium">
                        Gốc {Math.round(options.audio.original_volume * 100)}% / Giọng{" "}
                        {Math.round(options.audio.dub_volume * 100)}%
                      </p>
                      <p className="text-xs text-ink-soft">
                        {options.audio.ducking ? "Ducking bật · " : ""}
                        {options.output.format.toUpperCase()} · {options.output.quality}
                      </p>
                    </ReviewCard>
                  </div>

                  {!sourceValid && (
                    <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
                      Chưa có nguồn hợp lệ — quay lại bước 1 để chọn file hoặc phân tích link.
                    </p>
                  )}
                  {createJob.isError && (
                    <p className="text-sm text-red-600">
                      {createJob.error instanceof Error
                        ? createJob.error.message
                        : "Tạo job thất bại"}
                    </p>
                  )}
                  <button
                    className="btn-primary w-full justify-center py-3 text-lg"
                    disabled={!sourceValid || createJob.isPending}
                    onClick={() => createJob.mutate()}
                  >
                    {createJob.isPending
                      ? sourceMode === "download"
                        ? "Đang tạo job tải video..."
                        : "Đang tạo và tải lên..."
                      : "🚀 Tạo và khởi chạy"}
                  </button>
                </div>
              )}
            </div>

            {/* Prev/next */}
            <div className="mt-4 flex justify-between">
              <button
                className="btn-ghost"
                disabled={step === 0}
                onClick={() => setStep((s) => Math.max(0, s - 1))}
              >
                ← Quay lại
              </button>
              {step < STEPS.length - 1 && (
                <button className="btn-primary" onClick={() => setStep((s) => s + 1)}>
                  Tiếp tục →
                </button>
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

function ReviewCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-cream p-4">
      <p className="mb-1 text-xs font-bold tracking-wide text-ink-soft">{title}</p>
      {children}
    </div>
  );
}
