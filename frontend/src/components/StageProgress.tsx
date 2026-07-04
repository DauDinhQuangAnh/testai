import { PIPELINE_STEPS, STATUS_LABELS, TOTAL_STAGES } from "../lib/constants";

type JobStatus = "queued" | "running" | "done" | "failed";

type StageProgressProps = {
  progress: number;
  label: string;
  stage?: string | null;
  status?: JobStatus;
  variant?: "compact" | "detail";
};

function clampProgress(progress: number) {
  return Math.max(0, Math.min(1, progress || 0));
}

function currentIndex(stage: string | null | undefined, progress: number) {
  const byStage = PIPELINE_STEPS.findIndex((step) => step.key === stage);
  if (byStage >= 0) return byStage;
  return Math.max(0, Math.min(TOTAL_STAGES - 1, Math.ceil(progress * TOTAL_STAGES) - 1));
}

export default function StageProgress({
  progress,
  label,
  stage,
  status = "running",
  variant = "compact",
}: StageProgressProps) {
  const safeProgress = clampProgress(progress);
  const percent = Math.round(safeProgress * 100);
  const filled = Math.round(safeProgress * TOTAL_STAGES);
  const activeIndex = currentIndex(stage, safeProgress);

  if (variant === "compact") {
    return (
      <div>
        <div className="flex gap-1">
          {Array.from({ length: TOTAL_STAGES }, (_, i) => (
            <div
              key={i}
              className={
                "h-2 flex-1 rounded-full transition-colors " +
                (i < filled - 1
                  ? "bg-primary"
                  : i === filled - 1
                    ? "animate-pulse bg-primary"
                    : "bg-cream-dark")
              }
            />
          ))}
        </div>
        <div className="mt-1.5 flex justify-between text-xs text-ink-soft">
          <span>Bước hiện tại: {label}</span>
          <span>{percent}%</span>
        </div>
      </div>
    );
  }

  const headline =
    status === "queued" ? "Đang chờ xử lý" : status === "running" ? "Đang xử lý" : STATUS_LABELS[status];
  const detail =
    status === "queued"
      ? "Job đã vào hàng đợi. Worker sẽ tự động nhận khi đến lượt."
      : "Pipeline đang chạy. Trang này tự cập nhật khi có tiến độ mới.";

  return (
    <section className="mb-6 overflow-hidden rounded-xl border border-line bg-white shadow-sm">
      <div className="border-b border-line bg-gradient-to-r from-primary-soft via-white to-white px-5 py-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <span className="inline-flex h-2.5 w-2.5 rounded-full bg-primary shadow-[0_0_0_6px_rgba(232,89,12,0.12)]" />
              <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-primary shadow-sm">
                {STATUS_LABELS[status] ?? status}
              </span>
            </div>
            <h2 className="text-lg font-bold text-ink">{headline}</h2>
            <p className="mt-1 text-sm text-ink-soft">{detail}</p>
          </div>

          <div
            className="grid h-20 w-20 shrink-0 place-items-center rounded-full"
            style={{
              background: `conic-gradient(#E8590C ${percent * 3.6}deg, #F1E9DF 0deg)`,
            }}
          >
            <div className="grid h-16 w-16 place-items-center rounded-full bg-white text-center shadow-sm">
              <span className="text-xl font-bold text-ink">{percent}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="px-5 py-4">
        <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
              Bước hiện tại
            </p>
            <p className="mt-1 text-base font-semibold text-ink">{label}</p>
          </div>
          <p className="text-sm text-ink-soft">
            Bước {Math.min(activeIndex + 1, TOTAL_STAGES)} / {TOTAL_STAGES}
          </p>
        </div>

        <div className="mb-4 h-2.5 overflow-hidden rounded-full bg-cream-dark">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500"
            style={{ width: `${percent}%` }}
          />
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {PIPELINE_STEPS.map((step, index) => {
            const isDone = index < activeIndex;
            const isActive = index === activeIndex;
            return (
              <div
                key={step.key}
                className={
                  "flex min-h-11 items-center gap-2 rounded-lg border px-3 py-2 text-sm transition " +
                  (isActive
                    ? "border-primary bg-primary-soft text-primary shadow-sm"
                    : isDone
                      ? "border-orange-100 bg-orange-50 text-ink"
                      : "border-line bg-white text-ink-soft")
                }
              >
                <span
                  className={
                    "grid h-5 w-5 shrink-0 place-items-center rounded-full text-[11px] font-bold " +
                    (isActive
                      ? "bg-primary text-white"
                      : isDone
                        ? "bg-primary/80 text-white"
                        : "bg-cream-dark text-ink-soft")
                  }
                >
                  {isDone ? "✓" : index + 1}
                </span>
                <span className="min-w-0 truncate">{step.label}</span>
                {isActive && <span className="ml-auto h-2 w-2 rounded-full bg-primary animate-pulse" />}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
