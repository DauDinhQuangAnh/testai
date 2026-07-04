import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import NavBar from "../components/NavBar";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Mật khẩu nhập lại không khớp");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await register(email, password);
      navigate("/studio");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng ký thất bại");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen">
      <NavBar />
      <div className="mx-auto flex max-w-md flex-col px-4 pt-20">
        <div className="card">
          <h1 className="mb-6 text-center text-2xl font-bold">Tạo tài khoản</h1>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
                required
              />
            </div>
            <div>
              <label className="label">Mật khẩu (tối thiểu 6 ký tự)</label>
              <input
                className="input"
                type="password"
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="label">Nhập lại mật khẩu</label>
              <input
                className="input"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button className="btn-primary w-full justify-center" disabled={busy}>
              {busy ? "Đang tạo..." : "Đăng ký"}
            </button>
          </form>
          <p className="mt-4 text-center text-sm text-ink-soft">
            Đã có tài khoản?{" "}
            <Link to="/login" className="font-medium text-primary">
              Đăng nhập
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
