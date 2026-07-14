import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import NavBar from "../components/NavBar";
import Spinner from "../components/Spinner";
import { api, ApiError } from "../lib/api";
import type { CustomVoiceOut } from "../lib/types";

const SAMPLE_SCRIPT =
  "Xin chào, đây là đoạn văn mẫu để nhân bản giọng nói. Hôm nay trời khá đẹp, " +
  "rất thích hợp để đi dạo hoặc đọc một cuốn sách hay. Công nghệ trí tuệ nhân tạo " +
  "đang ngày càng phát triển và có thể học theo giọng nói của mỗi người chỉ trong " +
  "vài chục giây. Hãy đọc chậm rãi, rõ ràng, với âm lượng và tốc độ nói bình thường " +
  "để có kết quả tốt nhất.";

const MIN_SECONDS = 3;

export default function Voices() {
  const queryClient = useQueryClient();
  const [recording, setRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedSeconds, setRecordedSeconds] = useState(0);
  const [voiceName, setVoiceName] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const { data: voices, isLoading } = useQuery({
    queryKey: ["custom-voices"],
    queryFn: () => api.get<CustomVoiceOut[]>("/api/voices"),
  });

  const uploadVoice = useMutation({
    mutationFn: async () => {
      if (!recordedBlob) throw new Error("Chưa có bản ghi âm/file nào.");
      if (!voiceName.trim()) throw new Error("Hãy đặt tên cho giọng.");
      const form = new FormData();
      form.append("name", voiceName.trim());
      const ext = recordedBlob.type.includes("wav") ? "wav" : "webm";
      form.append("file", recordedBlob, `sample.${ext}`);
      return api.postForm<CustomVoiceOut>("/api/voices", form);
    },
    onSuccess: () => {
      setRecordedBlob(null);
      setRecordedSeconds(0);
      setVoiceName("");
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["custom-voices"] });
    },
    onError: (err) =>
      setErrorMessage(err instanceof ApiError ? err.message : (err as Error).message),
  });

  const deleteVoice = useMutation({
    mutationFn: (id: string) => api.del(`/api/voices/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["custom-voices"] }),
  });

  async function startRecording() {
    setErrorMessage(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setRecordedBlob(blob);
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
      setRecordedBlob(null);
      setRecordedSeconds(0);
      const startedAt = Date.now();
      timerRef.current = window.setInterval(() => {
        setRecordedSeconds((Date.now() - startedAt) / 1000);
      }, 200);
    } catch {
      setErrorMessage("Không truy cập được micro. Hãy cấp quyền cho trình duyệt, hoặc dùng nút tải file bên dưới.");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
    if (timerRef.current) window.clearInterval(timerRef.current);
  }

  function onFileSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setRecordedBlob(file);
    setRecordedSeconds(0);
    setErrorMessage(null);
  }

  const recordedUrl = recordedBlob ? URL.createObjectURL(recordedBlob) : null;

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="mb-1 text-2xl font-bold">Giọng của tôi</h1>
        <p className="mb-6 text-sm text-ink-soft">
          Đọc một đoạn văn mẫu (hoặc tải lên 1 file ghi âm sẵn) để tạo giọng riêng - dùng để lồng
          tiếng thay cho các giọng có sẵn. Cần tối thiểu vài giây âm thanh rõ ràng, ít tiếng ồn;
          đọc khoảng 20-30 giây thường cho kết quả tốt hơn.
        </p>

        <div className="card mb-6 space-y-4">
          <div>
            <p className="label">Đoạn văn mẫu (đọc to, rõ, tốc độ bình thường)</p>
            <p className="rounded-lg bg-cream px-4 py-3 text-sm leading-relaxed text-ink">
              {SAMPLE_SCRIPT}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {!recording ? (
              <button type="button" className="btn-primary" onClick={startRecording}>
                🎙️ Bắt đầu ghi âm
              </button>
            ) : (
              <button type="button" className="btn-primary bg-red-600 hover:bg-red-700" onClick={stopRecording}>
                ⏹ Dừng ({recordedSeconds.toFixed(0)}s)
              </button>
            )}
            <span className="text-sm text-ink-soft">hoặc</span>
            <label className="btn-ghost cursor-pointer">
              Tải file âm thanh lên
              <input type="file" accept="audio/*" className="hidden" onChange={onFileSelected} />
            </label>
          </div>

          {recordedUrl && (
            <div className="space-y-3 rounded-lg border border-line p-4">
              <audio controls src={recordedUrl} className="w-full" />
              {recordedSeconds > 0 && recordedSeconds < MIN_SECONDS && (
                <p className="text-sm text-amber-700">
                  Đoạn ghi hơi ngắn ({recordedSeconds.toFixed(0)}s) - nên ghi tối thiểu{" "}
                  {MIN_SECONDS}s để nhân bản giọng chính xác hơn.
                </p>
              )}
              <div className="flex flex-wrap items-center gap-3">
                <input
                  type="text"
                  className="input max-w-xs"
                  placeholder="Đặt tên cho giọng (vd. Giọng của tôi)"
                  value={voiceName}
                  onChange={(e) => setVoiceName(e.target.value)}
                />
                <button
                  type="button"
                  className="btn-primary"
                  disabled={uploadVoice.isPending}
                  onClick={() => uploadVoice.mutate()}
                >
                  {uploadVoice.isPending && <Spinner className="h-3 w-3" />}
                  {uploadVoice.isPending ? "Đang lưu..." : "Lưu giọng"}
                </button>
              </div>
            </div>
          )}
          {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
        </div>

        <h2 className="mb-3 text-lg font-semibold">Danh sách giọng đã clone</h2>
        {isLoading && (
          <div className="flex items-center gap-2 text-ink-soft">
            <Spinner /> Đang tải...
          </div>
        )}
        {voices && voices.length === 0 && (
          <p className="text-sm text-ink-soft">Chưa có giọng nào - tạo giọng đầu tiên ở trên.</p>
        )}
        <div className="space-y-2">
          {voices?.map((v) => (
            <div
              key={v.id}
              className="card flex items-center justify-between gap-3 py-3"
            >
              <div>
                <p className="font-medium text-ink">{v.name}</p>
                <p className="text-xs text-ink-soft">
                  Tạo lúc {new Date(v.created_at).toLocaleString("vi-VN")}
                </p>
              </div>
              <button
                type="button"
                className="text-sm text-red-600 hover:underline"
                disabled={deleteVoice.isPending && deleteVoice.variables === v.id}
                onClick={() => deleteVoice.mutate(v.id)}
              >
                Xóa
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
