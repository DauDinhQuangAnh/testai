import { TOTAL_STAGES } from "../lib/constants";

/** Thanh tien do nhieu doan (1 o/buoc pipeline) - o hien tai nhap nhay. */
export default function StageProgress({
  progress,
  label,
}: {
  progress: number;
  label: string;
}) {
  const filled = Math.round(progress * TOTAL_STAGES);
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
        <span>{Math.round(progress * 100)}%</span>
      </div>
    </div>
  );
}
