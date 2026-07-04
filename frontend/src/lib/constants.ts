// Cac lua chon co dinh cua wizard - khop app/pages/1_Upload.py (legacy) va
// backend options schema.

export const TRIM_CHOICES: { label: string; value: number | null }[] = [
  { label: "Toàn bộ video", value: null },
  { label: "Chạy thử 60 giây đầu", value: 60 },
  { label: "Chạy thử 120 giây đầu", value: 120 },
];

export const QUALITY_CHOICES: { label: string; value: "720p" | "best" }[] = [
  { label: "Ổn định 720p (nhẹ, nhanh)", value: "720p" },
  { label: "Tốt nhất có sẵn", value: "best" },
];

export const TRANSLATE_PRESETS: {
  label: string;
  maxChars: number;
  maxLines: number;
}[] = [
  { label: "Cân bằng (mặc định)", maxChars: 42, maxLines: 2 },
  { label: "Súc tích (dòng ngắn, dễ đọc nhanh)", maxChars: 32, maxLines: 1 },
  { label: "Thoải mái (dòng dài, ít ngắt)", maxChars: 50, maxLines: 2 },
];

export const POSITION_CHOICES: { label: string; value: "bottom" | "middle" | "top" }[] = [
  { label: "Dưới", value: "bottom" },
  { label: "Giữa", value: "middle" },
  { label: "Trên", value: "top" },
];

export const RENDER_QUALITY_CHOICES: {
  label: string;
  value: "fast" | "balanced" | "high";
}[] = [
  { label: "Cân bằng", value: "balanced" },
  { label: "Nhanh", value: "fast" },
  { label: "Cao", value: "high" },
];

export const FONT_CHOICES = [
  "Arial",
  "Segoe UI",
  "Tahoma",
  "Verdana",
  "Roboto",
  "Times New Roman",
];

export const STATUS_LABELS: Record<string, string> = {
  queued: "Đang chờ",
  running: "Đang chạy",
  done: "Hoàn thành",
  failed: "Thất bại",
};

// Khop app/jobs/stages.py PIPELINE_STAGES (11 buoc) - dung cho progress bar
// nhieu doan.
export const PIPELINE_STEPS = [
  { key: "starting", label: "Khởi động" },
  { key: "download", label: "Tải video" },
  { key: "extract_audio", label: "Tách audio" },
  { key: "denoise", label: "Khử ồn" },
  { key: "transcribe", label: "Nhận diện lời nói" },
  { key: "align", label: "Căn timing" },
  { key: "diarize", label: "Tách người nói" },
  { key: "merge", label: "Ghép kết quả" },
  { key: "translate", label: "Dịch" },
  { key: "dub", label: "Lồng tiếng" },
  { key: "done", label: "Hoàn thành" },
];

export const TOTAL_STAGES = PIPELINE_STEPS.length;
