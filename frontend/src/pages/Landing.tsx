import { Link } from "react-router-dom";

import NavBar from "../components/NavBar";

const FEATURES = [
  {
    icon: "🎙️",
    title: "11+ giọng đọc tự nhiên",
    desc: "Giọng Neural bản địa + đa ngôn ngữ, chỉnh tốc độ và cao độ, nghe thử trước khi chạy.",
  },
  {
    icon: "🌐",
    title: "Dán link là xong",
    desc: "YouTube, Douyin, TikTok... tự tải về và xử lý — không cần tải file thủ công.",
  },
  {
    icon: "🧠",
    title: "Nhận diện đa người nói",
    desc: "Mỗi người nói trong video tự động nhận một giọng lồng tiếng riêng biệt.",
  },
  {
    icon: "🔉",
    title: "Phối âm chuyên nghiệp",
    desc: "Giữ nhạc nền, tự giảm âm gốc khi có lời thoại (ducking) như phim tài liệu.",
  },
  {
    icon: "📝",
    title: "Phụ đề tùy biến",
    desc: "5 định dạng phụ đề + gắn cứng vào video với font, màu, vị trí tùy chọn.",
  },
  {
    icon: "📖",
    title: "Bảng thuật ngữ",
    desc: "Ép giữ đúng tên riêng, từ chuyên ngành khi dịch — không còn dịch sai thuật ngữ.",
  },
];

const STEPS = [
  { n: "1", title: "Chọn nguồn", desc: "Dán link hoặc tải video lên, chọn ngôn ngữ đích." },
  { n: "2", title: "Tùy chỉnh", desc: "Chọn giọng đọc, kiểu phụ đề, cách phối âm." },
  { n: "3", title: "Nhận kết quả", desc: "Video đã lồng tiếng + phụ đề đầy đủ định dạng." },
];

export default function Landing() {
  return (
    <div className="min-h-screen">
      <NavBar />

      <section className="mx-auto max-w-6xl px-4 pb-20 pt-16 text-center">
        <p className="mb-4 inline-block rounded-full bg-primary-soft px-4 py-1 text-sm font-medium text-primary">
          Chạy hoàn toàn trên máy của bạn · Whisper + NLLB + Neural TTS
        </p>
        <h1 className="mx-auto max-w-3xl text-4xl font-extrabold leading-tight sm:text-5xl">
          Lồng tiếng video sang <span className="text-primary">tiếng Việt</span> chỉ trong một
          cú nhấp
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-ink-soft">
          Tự động nhận diện lời nói, dịch thuật giữ ngữ cảnh và tạo giọng đọc tự nhiên — từ
          video YouTube, Douyin hoặc file của bạn.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/register" className="btn-primary px-8 py-3 text-lg">
            Bắt đầu ngay
          </Link>
          <Link to="/login" className="btn-ghost px-8 py-3 text-lg">
            Đăng nhập
          </Link>
        </div>
      </section>

      <section className="border-y border-line bg-white py-16">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="mb-10 text-center text-3xl font-bold">Mọi thứ bạn cần để lồng tiếng</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="rounded-xl border border-line bg-cream p-6">
                <div className="mb-3 text-3xl">{f.icon}</div>
                <h3 className="mb-1 font-semibold">{f.title}</h3>
                <p className="text-sm text-ink-soft">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="mx-auto max-w-4xl px-4">
          <h2 className="mb-10 text-center text-3xl font-bold">Quy trình 3 bước</h2>
          <div className="grid gap-6 sm:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.n} className="card text-center">
                <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-lg font-bold text-white">
                  {s.n}
                </div>
                <h3 className="mb-1 font-semibold">{s.title}</h3>
                <p className="text-sm text-ink-soft">{s.desc}</p>
              </div>
            ))}
          </div>
          <div className="mt-12 text-center">
            <Link to="/register" className="btn-primary px-8 py-3 text-lg">
              Tạo video đầu tiên
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-line bg-white py-8 text-center text-sm text-ink-soft">
        VietDub Studio — công cụ cá nhân, toàn bộ pipeline AI chạy local trên GPU của bạn.
      </footer>
    </div>
  );
}
